#!/usr/bin/env bash

ROOT="$(
cd "$(dirname "$0")/../.." &&
pwd
)"

cd "$ROOT"

echo "======================================================"
echo "MEDIBOOK PRODUCTION READINESS"
echo "======================================================"


echo
echo "===== BACKEND COMPILE ====="

source .venv/bin/activate

python3 -m compileall \
  -q app

echo "BACKEND_COMPILE_STATUS=$?"


echo
echo "===== FRONTEND TYPECHECK ====="

cd frontend

npx tsc --noEmit \
  >/tmp/medibook-readiness-tsc.log \
  2>&1

echo "TYPECHECK_STATUS=$?"


echo
echo "===== FRONTEND BUILD ====="

npm run build \
  >/tmp/medibook-readiness-build.log \
  2>&1

BUILD=$?

echo "BUILD_STATUS=$BUILD"


if [ "$BUILD" != "0" ]; then

    tail -n 80 \
      /tmp/medibook-readiness-build.log
fi


cd "$ROOT"


echo
echo "===== PRODUCTION ENV ====="

python3 \
  deploy/scripts/check_production_env.py


echo
echo "===== CURRENT CORE ACCEPTANCE ====="

ACCEPTANCE="$(
find "$ROOT" \
  -type f \
  -name 'medibook_acceptance.sh' \
  2>/dev/null \
  | head -n1
)"


if [ -n "$ACCEPTANCE" ]; then

    bash "$ACCEPTANCE" \
      || true

else

    echo "Acceptance script not found."
fi


echo
echo "===== SECURITY AUDIT ====="

bash \
  deploy/scripts/security_audit.sh


echo
echo "======================================================"
echo "READINESS AUDIT FINISHED"
echo "======================================================"
