#!/usr/bin/env bash
# Rehearse the production stack locally in an isolated compose project.
# Builds the images, starts postgres, redis, migrate, backend, worker and
# frontend from compose.production.yaml on a fresh database, runs smoke and
# monitor checks, then removes the rehearsal containers and volumes.
#
# Usage: deploy/scripts/rehearse_production.sh [--keep]
# Env:   REHEARSAL_ENV_FILE       KEY=VALUE lines applied over .env.production
#                                 for migrate, backend and worker (test SMTP/S3)
#        REHEARSAL_BACKEND_PORT   default 18000
#        REHEARSAL_FRONTEND_PORT  default 13000
set -uo pipefail
umask 077

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1

PROJECT="medibook-rehearsal"
BP="${REHEARSAL_BACKEND_PORT:-18000}"
FP="${REHEARSAL_FRONTEND_PORT:-13000}"
KEEP="${1:-}"
WORK="$(mktemp -d)"
OVERRIDE="$WORK/override.yaml"
DC=(docker compose -p "$PROJECT" --env-file .env.production -f compose.production.yaml -f "$OVERRIDE")
FAILURES=0

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILURES=$((FAILURES + 1)); }
status() { curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1"; }

cleanup() {
    if [ "$KEEP" = "--keep" ]; then
        echo "rehearsal left running; remove it with: docker compose -p $PROJECT -f compose.production.yaml down -v"
    else
        "${DC[@]}" down -v --remove-orphans > /dev/null 2>&1
        echo "rehearsal containers and volumes removed"
    fi
    rm -rf "$WORK"
}
trap cleanup EXIT

if [ -f .env.production ]; then :; else echo "ERROR: .env.production is missing"; exit 1; fi

env_block() {
    if [ -n "${REHEARSAL_ENV_FILE:-}" ] && [ -f "$REHEARSAL_ENV_FILE" ]; then
        echo "    environment:"
        grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$REHEARSAL_ENV_FILE" | while IFS='=' read -r key value; do
            printf '      %s: "%s"\n' "$key" "$value"
        done
    fi
}

{
    echo "services:"
    echo "  backend:"
    echo "    ports:"
    echo "      - \"127.0.0.1:$BP:8000\""
    env_block
    echo "  frontend:"
    echo "    ports:"
    echo "      - \"127.0.0.1:$FP:3000\""
    if [ -n "${REHEARSAL_ENV_FILE:-}" ]; then
        echo "  migrate:"
        env_block
        echo "  worker:"
        env_block
    fi
} > "$OVERRIDE"

echo "1/6 build images"
if "${DC[@]}" build > "$WORK/build.log" 2>&1; then pass "images built"; else tail -n 30 "$WORK/build.log"; fail "image build"; exit 1; fi

echo "2/6 start migrate, backend, worker and frontend on a fresh database"
if "${DC[@]}" up -d migrate backend worker frontend > "$WORK/up.log" 2>&1; then pass "stack started"; else tail -n 30 "$WORK/up.log"; fail "compose up"; fi

echo "3/6 wait for backend and frontend"
ready=0
for _ in $(seq 1 90); do
    if [ "$(status "http://127.0.0.1:$BP/health")" = 200 ] && [ "$(status "http://127.0.0.1:$FP/")" = 200 ]; then ready=1; break; fi
    sleep 2
done
if [ "$ready" = 1 ]; then pass "backend and frontend answer"; else fail "backend or frontend not ready after 180s"; "${DC[@]}" logs --tail=40 migrate backend frontend 2>&1 | tail -n 60; fi

echo "4/6 services and smoke checks"
"${DC[@]}" ps -a --format '{{.Service}}|{{.State}}|{{.Health}}|{{.ExitCode}}' > "$WORK/ps.txt" 2>/dev/null
while IFS='|' read -r service state health exit_code; do
    case "$service" in
        "") ;;
        migrate)
            if [ "$state" = exited ] && [ "$exit_code" = 0 ]; then pass "migrate completed"; else fail "migrate is $state (exit $exit_code)"; fi ;;
        *)
            if [ "$state" = running ]; then pass "$service running${health:+ ($health)}"; else fail "$service is $state"; fi ;;
    esac
done < "$WORK/ps.txt"
revision="$("${DC[@]}" exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select version_num from alembic_version"' 2>/dev/null)"
if [ -n "$revision" ]; then pass "fresh database at alembic $revision"; else fail "no alembic revision in the rehearsal database"; fi
if [ "$(status "http://127.0.0.1:$BP/openapi.json")" = 200 ]; then pass "OpenAPI served"; else fail "OpenAPI not served"; fi
code="$(status "http://127.0.0.1:$BP/api/v1/auth/me")"
case "$code" in 401|403) pass "auth guard answers $code" ;; *) fail "auth guard answered $code" ;; esac
code="$(status "http://127.0.0.1:$FP/api/directory/doctors")"
if [ "$code" = 200 ]; then pass "frontend BFF reaches the backend"; else fail "frontend BFF answered $code"; fi
if curl -s -D - -o /dev/null "http://127.0.0.1:$BP/health" | tr -d '\r' | grep -qi '^x-content-type-options: nosniff'; then pass "security headers present"; else fail "security headers missing"; fi
if "${DC[@]}" logs worker 2>/dev/null | grep -q 'integration.worker.started'; then pass "worker started"; else fail "worker did not log its start"; fi
llm="$("${DC[@]}" exec -T backend python -c 'import os, urllib.request; base = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/"); print(urllib.request.urlopen(base + "/api/tags", timeout=5).status)' 2>&1 | tail -n 1)"
if [ "$llm" = 200 ]; then pass "LLM endpoint reachable from the backend container"; else echo "WARN  LLM endpoint not reachable from the backend container ($llm); Ollama must listen on an address containers can reach"; fi

echo "5/6 health monitor"
if MONITOR_URL="http://127.0.0.1:$BP" MONITOR_PROJECT="$PROJECT" MONITOR_SKIP_BACKUP=1 bash "$ROOT/deploy/scripts/monitor_health.sh"; then pass "monitor reports OK"; else fail "monitor reported problems"; fi

echo "6/6 result"
if [ "$FAILURES" = 0 ]; then echo "REHEARSAL: PASS"; exit 0; fi
echo "REHEARSAL: FAIL ($FAILURES checks)"
exit 1
