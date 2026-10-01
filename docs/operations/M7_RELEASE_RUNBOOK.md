# MediBook V1 Release and Operations Runbook

Applies to `compose.production.yaml`. Run commands from the repository root on
the production host. `DC` below means:

    docker compose --env-file .env.production -f compose.production.yaml

## 1. Prepare the environment

1. Copy `.env.production.example` to `.env.production` and replace every
   `CHANGE_ME`.
2. Generate secrets with `deploy/scripts/generate_secrets.sh` (database, JWT)
   and `python3 scripts/generate_integration_master_key.py` for
   `MEDIBOOK_INTEGRATION_MASTER_KEY`. Keep the master key in a secret manager:
   without it, stored integration credentials cannot be decrypted and
   integrations fail closed.
3. Validate with `python3 deploy/scripts/check_production_env.py`; it must
   report no missing keys. Production requires SMTP delivery and S3-compatible
   profile storage (S3, R2 or MinIO). Local storage is rejected because files
   are lost when containers are recreated.
4. The assistant needs an Ollama endpoint at `OLLAMA_BASE_URL` with
   `OLLAMA_MODEL` pulled (default: the host, via `host.docker.internal`).

## 2. First deployment

    DC build
    DC up -d
    DC ps

- `migrate` runs first. On an empty database it loads
  `migrations/baseline/schema.sql` (schema at `m6b2queue20260930`) and then
  runs `alembic upgrade head`. `backend` and `worker` start only after it
  exits successfully.
- Check `curl -fsS https://<domain>/health` and
  `deploy/scripts/production_smoke.sh https://<domain>`.

## 2a. Rehearse before deploying

`deploy/scripts/rehearse_production.sh` builds the images and runs migrate,
backend, worker and frontend from `compose.production.yaml` in a separate
compose project on a fresh database. It smoke-tests them (health, OpenAPI,
authentication guard, frontend, BFF to backend), checks that the backend
container can reach the LLM endpoint, runs the health monitor and then
removes the rehearsal containers and volumes. Point `REHEARSAL_ENV_FILE` at
a file of test values to override SMTP or S3 settings for the rehearsal.

## 3. Upgrades

1. Back up first: `deploy/scripts/backup_postgres.sh`.
2. Check out the release tag, then `DC build`.
3. `DC up -d`. `migrate` applies pending migrations before the app restarts.
4. Repeat the checks from section 2 and read
   `DC logs --tail=100 backend worker`.

## 4. Rollback

- Application: check out the previous tag, `DC build`, `DC up -d`.
- Schema: `DC run --rm backend alembic downgrade <revision>`. The M6
  migrations were verified to downgrade and upgrade cleanly.
- Data: restore from a backup (section 6).

## 5. Backups

- Daily cron example:
  `0 2 * * * cd /srv/medibook && deploy/scripts/backup_postgres.sh >> /var/log/medibook-backup.log 2>&1`
- Files land in `deploy/backups/medibook_<time>.sql.gz`, owner-only; the
  newest 14 are kept. Copy them off the host, encrypted.
- Monthly restore drill (safe): `deploy/scripts/restore_postgres.sh <file>`
  restores into a new `medibook_restore_<time>` database and prints its table
  count and alembic revision. Drop that database afterwards.

## 6. Restore after data loss

    MEDIBOOK_CONFIRM_RESTORE=<live db name> deploy/scripts/restore_postgres.sh <file> --replace-live

This takes a safety backup, restores into a staging database, stops backend,
worker and frontend, swaps the databases, restarts the services, and keeps the
previous database as `<db>_pre_restore` until you drop it.

## 7. Health, logs and monitoring

- Liveness: `GET /health`. Full system health for platform admins:
  `GET /api/v1/platform-control-v2/system-health`.
- Logs are JSON with `request_id` and `trace_id`. Responses carry
  `x-request-id` and `x-trace-id` headers for correlating user reports.
- Worker: `DC logs -f worker`. One manual pass:
  `DC run --rm worker python scripts/run_integration_sync_worker.py --once`.
- Minimum alerting: an external uptime check on `/health` every minute,
  container restarts or unhealthy status in `DC ps`, failed backup cron runs,
  and free disk space on the database volume.
- `deploy/scripts/monitor_health.sh` implements those checks for cron, for
  example every five minutes, mailing its output when it exits non-zero.

## 8. Security operations

- Integration secret audit (expects `plaintext_secret_rows=0`):
  `DC run --rm backend python scripts/audit_integration_secrets.py`.
- Rate limits are set with `MEDIBOOK_RATE_LIMIT_*`. Blocked clients receive
  429 with `Retry-After`.
- Rotating `JWT_SECRET` signs everyone out.
- Email delivery failures surface as 502 (SMTP server unreachable) or 503
  (delivery not configured).

## 9. What V1 was certified against

- Gate: zero duplicate OpenAPI operations; unit and PostgreSQL integration
  tests, including the 8-way concurrent booking proof; alembic at head;
  boot and HTTP smoke; secret audit; worker pass; frontend typecheck, lint
  and build.
- Recovery: backup, scratch restore with row parity, M6 rollback, fresh
  bootstrap equivalent to the migrated schema, replace-live restore on scratch
  databases.
- Deployment: the production image boots, runs migrate on an empty database,
  completes a worker pass and passes the secret audit.
- Security: anonymous authorization sweep (protected operations return 401,
  no 5xx) and login rate limiting.
- Browser E2E: `cd frontend && npm run e2e` against a running stack.

## 10. Local development notes

- Signup needs `MEDIBOOK_OTP_SECRET` in the backend environment; without it
  the signup endpoints fail with a server error.
- In production Ollama must listen on an address the backend container can
  reach (for example `OLLAMA_HOST=0.0.0.0` behind a firewall, or an Ollama
  service on the compose network).

## Production origins and the LLM endpoint

`FRONTEND_ORIGIN` and `MEDIBOOK_ALLOWED_ORIGINS` must be the public `https://` origin people open in the browser; separate several origins with commas. The backend refuses to start without `MEDIBOOK_ALLOWED_ORIGINS` and rejects `*`, and `deploy/scripts/check_production_env.py` rejects `http://` origins.

The backend container calls Ollama at `OLLAMA_BASE_URL` (default `http://host.docker.internal:11434`). Ollama listens only on 127.0.0.1 by default, which containers cannot reach. Run `sudo systemctl edit ollama`, add the lines below, then run `sudo systemctl restart ollama`:

~~~ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
~~~

Then allow port 11434 only from the Docker networks, for example `sudo ufw allow from 172.16.0.0/12 to any port 11434 proto tcp` with ufw denying other incoming traffic. Ollama has no authentication, so the port must never be reachable from the internet. `deploy/scripts/rehearse_production.sh` prints a WARN while the endpoint is unreachable.
