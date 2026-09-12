#!/usr/bin/env bash

ROOT="$(
cd "$(dirname "$0")/../.." &&
pwd
)"

BACKUP_DIR="$ROOT/deploy/backups"

mkdir -p "$BACKUP_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"

FILE="$BACKUP_DIR/medibook_$STAMP.sql.gz"


echo "Creating MediBook PostgreSQL backup..."


docker exec \
  medibook-postgres \
  pg_dump \
  -U medibook \
  -d medibook \
  --no-owner \
  --no-acl \
  | gzip \
  > "$FILE"


STATUS="${PIPESTATUS[0]}"


if [ "$STATUS" = "0" ] && [ -s "$FILE" ]; then

    echo "BACKUP: PASS"
    echo "$FILE"

else

    echo "BACKUP: FAIL"

    rm -f "$FILE"
fi


# Keep latest 14 backups.
find "$BACKUP_DIR" \
  -type f \
  -name 'medibook_*.sql.gz' \
  -printf '%T@ %p\n' \
  2>/dev/null \
  | sort -nr \
  | tail -n +15 \
  | cut -d' ' -f2- \
  | xargs -r rm -f
