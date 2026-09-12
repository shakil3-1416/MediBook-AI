#!/usr/bin/env bash

FILE="$1"

if [ -z "$FILE" ]; then

    echo "Usage:"
    echo "./deploy/scripts/restore_postgres.sh backup.sql.gz"

else

    if [ ! -f "$FILE" ]; then

        echo "Backup file not found:"
        echo "$FILE"

    else

        echo "Restoring PostgreSQL backup:"
        echo "$FILE"

        gunzip -c "$FILE" \
          | docker exec -i \
              medibook-postgres \
              psql \
              -U medibook \
              -d medibook

        echo "Restore command finished."

    fi
fi
