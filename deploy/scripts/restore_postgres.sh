#!/usr/bin/env bash
# MediBook PostgreSQL restore.
#
#   restore_postgres.sh BACKUP.sql.gz
#       Verify (default): restore into a new database medibook_restore_<time>,
#       stop at the first error, print table count and alembic revision.
#       The live database is not touched.
#
#   MEDIBOOK_CONFIRM_RESTORE=<live db> restore_postgres.sh BACKUP.sql.gz --replace-live
#       Replace the live database: safety backup, restore into a staging
#       database, stop app services, swap database names, start services.
#       The previous database is kept as <live db>_pre_restore.
#
# Overrides: MEDIBOOK_APP_SERVICES (default "backend worker frontend"; empty = none),
#            MEDIBOOK_ENV_FILE, plus the pg_common.sh variables.
set -uo pipefail
umask 077

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
. "$ROOT/deploy/scripts/pg_common.sh"

FILE="${1:-}"
MODE="${2:-verify}"
SERVICES="${MEDIBOOK_APP_SERVICES-backend worker frontend}"
COMPOSE=(docker compose --project-directory "$ROOT" -f "$ROOT/compose.production.yaml" --env-file "${MEDIBOOK_ENV_FILE:-$ROOT/.env.production}")

usage() { sed -n '2,17p' "$0"; exit 2; }
psql_in() { docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -v ON_ERROR_STOP=1 "$@"; }
restore_into() { gunzip -c "$FILE" | psql_in -d "$1" --single-transaction -q > /dev/null; }
summary() {
    echo "tables: $(psql_in -d "$1" -Atc "select count(*) from information_schema.tables where table_schema = 'public'")"
    echo "alembic: $(psql_in -d "$1" -Atc 'select version_num from alembic_version' 2>/dev/null || echo none)"
}

[ -n "$FILE" ] || usage
[ -f "$FILE" ] || { echo "Backup file not found: $FILE"; exit 1; }
gzip -t "$FILE" || { echo "Backup file is corrupt: $FILE"; exit 1; }

case "$MODE" in
  verify)
    TARGET="medibook_restore_$(date +%Y%m%d_%H%M%S)"
    docker exec "$PG_CONTAINER" createdb -U "$PG_USER" "$TARGET" || exit 1
    if restore_into "$TARGET"; then
        echo "RESTORE VERIFY: PASS -> database $TARGET"
        summary "$TARGET"
        echo "Drop it when done: docker exec $PG_CONTAINER dropdb -U $PG_USER $TARGET"
    else
        docker exec "$PG_CONTAINER" dropdb -U "$PG_USER" --if-exists "$TARGET"
        echo "RESTORE VERIFY: FAIL (backup does not restore cleanly)"
        exit 1
    fi
    ;;
  --replace-live)
    if [ "${MEDIBOOK_CONFIRM_RESTORE:-}" = "$PG_DB" ]; then :; else
        echo "Refusing to replace live database $PG_DB without MEDIBOOK_CONFIRM_RESTORE=$PG_DB"
        exit 1
    fi
    STAGING="${PG_DB}_restore_staging"
    echo "1/6 safety backup of $PG_DB"
    SAFETY="$(MEDIBOOK_PG_CONTAINER="$PG_CONTAINER" MEDIBOOK_PG_USER="$PG_USER" MEDIBOOK_PG_DB="$PG_DB" bash "$ROOT/deploy/scripts/backup_postgres.sh" | tail -1)"
    [ -s "$SAFETY" ] || { echo "Safety backup failed; nothing changed."; exit 1; }
    echo "    $SAFETY"
    echo "2/6 restore into staging database $STAGING"
    docker exec "$PG_CONTAINER" dropdb -U "$PG_USER" --if-exists "$STAGING"
    docker exec "$PG_CONTAINER" createdb -U "$PG_USER" "$STAGING" || exit 1
    if restore_into "$STAGING"; then :; else
        docker exec "$PG_CONTAINER" dropdb -U "$PG_USER" --if-exists "$STAGING"
        echo "RESTORE: FAIL in staging; live database untouched."
        exit 1
    fi
    echo "3/6 stop app services: ${SERVICES:-none}"
    if [ -n "$SERVICES" ]; then "${COMPOSE[@]}" stop $SERVICES; fi
    echo "4/6 swap $PG_DB -> ${PG_DB}_pre_restore and $STAGING -> $PG_DB"
    psql_in -d postgres -q <<SQL
select pg_terminate_backend(pid) from pg_stat_activity
 where datname in ('$PG_DB', '$STAGING') and pid <> pg_backend_pid();
drop database if exists "${PG_DB}_pre_restore";
alter database "$PG_DB" rename to "${PG_DB}_pre_restore";
alter database "$STAGING" rename to "$PG_DB";
SQL
    SWAP=$?
    echo "5/6 start app services: ${SERVICES:-none}"
    if [ -n "$SERVICES" ]; then "${COMPOSE[@]}" start $SERVICES; fi
    if [ "$SWAP" = 0 ]; then
        echo "RESTORE: PASS"
        summary "$PG_DB"
        echo "6/6 previous database kept as ${PG_DB}_pre_restore; drop it after verification"
    else
        echo "RESTORE: FAIL during swap; inspect $PG_DB, ${PG_DB}_pre_restore and $STAGING"
        exit 1
    fi
    ;;
  *) usage ;;
esac
