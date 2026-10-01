#!/usr/bin/env bash
# MediBook health monitor for cron or an external scheduler.
# Prints problems and exits 1 when:
#   - GET $MONITOR_URL/health does not return 200
#   - a compose service is not running or is unhealthy (migrate may have exited 0)
#   - the newest backup in deploy/backups is older than MONITOR_BACKUP_MAX_HOURS (26)
#   - the filesystem holding the repository is fuller than MONITOR_DISK_MAX_PCT (85)
# Example cron entry:
#   */5 * * * * cd /srv/medibook && deploy/scripts/monitor_health.sh > /tmp/medibook-monitor.txt || mail -s "MediBook alert" ops@example.com < /tmp/medibook-monitor.txt
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
URL="${MONITOR_URL:-http://127.0.0.1}"
PROJECT="${MONITOR_PROJECT:-}"
MAX_HOURS="${MONITOR_BACKUP_MAX_HOURS:-26}"
MAX_PCT="${MONITOR_DISK_MAX_PCT:-85}"
DC=(docker compose)
if [ -n "$PROJECT" ]; then DC+=(-p "$PROJECT"); fi
DC+=(-f compose.production.yaml)
problems=0
problem() { echo "PROBLEM: $1"; problems=$((problems + 1)); }

code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$URL/health")"
if [ "$code" = 200 ]; then echo "ok: health endpoint"; else problem "health endpoint returned ${code:-no response}"; fi

services=0
while IFS='|' read -r service state health exit_code; do
    [ -n "$service" ] || continue
    services=$((services + 1))
    if [ "$service" = migrate ]; then
        if [ "$state" = running ]; then continue; fi
        if [ "$state" = exited ] && [ "$exit_code" = 0 ]; then continue; fi
        problem "migrate is $state (exit $exit_code)"
        continue
    fi
    if [ "$state" = running ]; then :; else problem "$service is $state"; fi
    if [ "$health" = unhealthy ]; then problem "$service is unhealthy"; fi
done < <("${DC[@]}" ps -a --format '{{.Service}}|{{.State}}|{{.Health}}|{{.ExitCode}}' 2>/dev/null)
if [ "$services" = 0 ]; then problem "no compose services found"; else echo "ok: $services services checked"; fi

if [ "${MONITOR_SKIP_BACKUP:-0}" = 1 ]; then :; else
    newest="$(find "$ROOT/deploy/backups" -type f -name 'medibook_*.sql.gz' -printf '%T@\n' 2>/dev/null | sort -nr | head -n 1)"
    if [ -z "$newest" ]; then
        problem "no backups found in deploy/backups"
    else
        age_hours=$(( ( $(date +%s) - ${newest%.*} ) / 3600 ))
        if [ "$age_hours" -gt "$MAX_HOURS" ]; then problem "newest backup is ${age_hours}h old"; else echo "ok: newest backup ${age_hours}h old"; fi
    fi
fi

used="$(df -P "$ROOT" | awk 'NR == 2 {gsub("%", "", $5); print $5}')"
if [ "${used:-0}" -gt "$MAX_PCT" ]; then problem "disk ${used}% full"; else echo "ok: disk ${used}% used"; fi

if [ "$problems" = 0 ]; then echo "MONITOR: OK"; exit 0; fi
echo "MONITOR: $problems problem(s)"
exit 1
