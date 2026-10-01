#!/usr/bin/env bash
# MediBook PostgreSQL backup: plain SQL, gzip, owner-only permissions.
# Keeps the newest 14 files. Overrides: MEDIBOOK_BACKUP_DIR plus pg_common.sh variables.
# The last line printed is the backup path.
set -uo pipefail
umask 077

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
. "$ROOT/deploy/scripts/pg_common.sh"

BACKUP_DIR="${MEDIBOOK_BACKUP_DIR:-$ROOT/deploy/backups}"
mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/medibook_$(date +%Y%m%d_%H%M%S).sql.gz"

echo "Creating MediBook PostgreSQL backup of $PG_DB ..."

docker exec "$PG_CONTAINER" pg_dump -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl | gzip > "$FILE"
STATUS="${PIPESTATUS[0]}"

if [ "$STATUS" = "0" ] && [ -s "$FILE" ] && gzip -t "$FILE"; then
    echo "BACKUP: PASS"
else
    echo "BACKUP: FAIL"
    rm -f "$FILE"
    exit 1
fi

find "$BACKUP_DIR" -type f -name 'medibook_*.sql.gz' -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr | tail -n +15 | cut -d' ' -f2- | xargs -r rm -f

echo "$FILE"
