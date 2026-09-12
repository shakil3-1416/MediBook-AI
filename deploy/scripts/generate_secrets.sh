#!/usr/bin/env bash

echo
echo "JWT_SECRET:"
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY

echo
echo "POSTGRES_PASSWORD:"
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
