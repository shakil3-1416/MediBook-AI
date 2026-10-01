# Shared PostgreSQL target resolution for MediBook ops scripts (sourced).
#   MEDIBOOK_PG_CONTAINER  container to use; default: medibook-postgres when running,
#                          otherwise the postgres service of compose.production.yaml
#   MEDIBOOK_PG_USER / MEDIBOOK_PG_DB  default to the container's POSTGRES_USER / POSTGRES_DB
ROOT="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

if [ -n "${MEDIBOOK_PG_CONTAINER:-}" ]; then
    PG_CONTAINER="$MEDIBOOK_PG_CONTAINER"
elif docker ps --format '{{.Names}}' | grep -qx 'medibook-postgres'; then
    PG_CONTAINER="medibook-postgres"
else
    PG_CONTAINER="$(docker compose --project-directory "$ROOT" -f "$ROOT/compose.production.yaml" ps -q postgres 2>/dev/null | head -1)"
fi

if [ -z "$PG_CONTAINER" ]; then
    echo "ERROR: no running PostgreSQL container found (set MEDIBOOK_PG_CONTAINER)." >&2
    exit 1
fi

PG_USER="${MEDIBOOK_PG_USER:-$(docker exec "$PG_CONTAINER" printenv POSTGRES_USER 2>/dev/null)}"
PG_USER="${PG_USER:-postgres}"
PG_DB="${MEDIBOOK_PG_DB:-$(docker exec "$PG_CONTAINER" printenv POSTGRES_DB 2>/dev/null)}"
PG_DB="${PG_DB:-$PG_USER}"
