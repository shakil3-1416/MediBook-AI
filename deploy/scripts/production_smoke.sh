#!/usr/bin/env bash

BASE="${1:-http://127.0.0.1}"

PASS=0
FAIL=0


check() {

    LABEL="$1"
    URL="$2"
    EXPECTED="$3"

    STATUS="$(
        curl -s \
          -o /dev/null \
          -w '%{http_code}' \
          "$URL" \
          2>/dev/null
    )"


    if [ "$STATUS" = "$EXPECTED" ]; then

        printf "%-32s PASS (%s)\n" \
          "$LABEL" \
          "$STATUS"

        PASS=$((PASS + 1))

    else

        printf "%-32s FAIL (%s)\n" \
          "$LABEL" \
          "$STATUS"

        FAIL=$((FAIL + 1))
    fi
}


echo
echo "MEDIBOOK PRODUCTION SMOKE"
echo "============================================"


check \
  "Landing page" \
  "$BASE/" \
  "200"


check \
  "Doctor directory" \
  "$BASE/doctors" \
  "200"


check \
  "Login page" \
  "$BASE/login" \
  "200"


echo
echo "PASS=$PASS"
echo "FAIL=$FAIL"
