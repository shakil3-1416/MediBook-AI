# MediBook M6 Production Runbook

## Production secret

MEDIBOOK_INTEGRATION_MASTER_KEY must come from the deployment secret manager and remain stable after integration credentials are encrypted.

Never commit the real key.

## Health

Public liveness:
GET /health

Platform-admin system health:
GET /api/v1/platform-control-v2/system-health

## Integration worker

Normal:
python scripts/run_integration_sync_worker.py

One iteration:
python scripts/run_integration_sync_worker.py --once

PostgreSQL integration_sync_runs remains the durable source of truth. Redis worker heartbeats are transient.

## Ownership

Managed: MediBook is authoritative and external sync is blocked.

Connected: External system is authoritative. Pull is allowed and push is blocked.

Hybrid: Ownership is explicit per resource. External-owned resources pull; MediBook-owned resources push; unspecified resources fail closed.

## Security

Provider webhook implementations must verify authentic provider signatures before processing data.

Executable provider calls use bounded timeouts and circuit breaking.

Rate limiting protects authentication, chat, widget, and public hospital surfaces.

Never log passwords, bearer tokens, cookies, API keys, webhook secrets, or decrypted integration credentials.
