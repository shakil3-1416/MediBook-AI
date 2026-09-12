#!/usr/bin/env bash

echo "======================================================"
echo "MEDIBOOK SECURITY SANITY AUDIT"
echo "======================================================"

echo
echo "===== SECRET FILES ====="

for FILE in \
  .env \
  .env.production \
  frontend/.env.local
do

    if [ -f "$FILE" ]; then

        PERMS="$(
            stat -c '%a' "$FILE" \
            2>/dev/null
        )"

        echo "$FILE permissions: $PERMS"

    else

        echo "$FILE: not present"
    fi

done


echo
echo "===== FRONTEND ENV SECRET NAMES ====="

python3 - <<'PY'
from pathlib import Path

for path in [
    Path("frontend/.env.local"),
    Path("frontend/.env.production"),
]:

    if not path.exists():
        continue

    dangerous = []

    for raw in path.read_text().splitlines():

        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        name = line.split(
            "=",
            1,
        )[0].strip()


        if any(
            word in name.upper()
            for word in [
                "SECRET",
                "PASSWORD",
                "PRIVATE",
            ]
        ):

            dangerous.append(
                name
            )


    print(
        path,
        "secret-like names:",
        dangerous or "NONE",
    )
PY


echo
echo "===== DEBUG FLAGS ====="

grep -RniE \
  'DEBUG\s*=\s*(true|1)|debug=True' \
  app \
  2>/dev/null \
  | head -n20 \
  || true


echo
echo "===== TODO / FIXME ====="

grep -RniE \
  'TODO|FIXME|HACK' \
  app frontend/src \
  2>/dev/null \
  | head -n50 \
  || true


echo
echo "SECURITY AUDIT FINISHED"
