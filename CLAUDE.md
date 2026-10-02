# MediBook: notes for coding agents

MediBook is a multi-hospital appointment assistant for Bangladesh. Hospitals embed a chat widget on their own website; patients find doctors and book, reschedule or cancel. Backend code performs every booking change after explicit confirmation; the AI only proposes.

## Layout

- `app/`: FastAPI backend. Routers in `app/api/v1`, business logic in `app/services`, the chatbot in `app/chatbot`, roles in `app/core/roles.py`.
- `migrations/`: Alembic with a single head. Fresh databases are bootstrapped by `app/db_bootstrap.py`.
- `frontend/`: Next.js 16 App Router with Tailwind v4. Route handlers under `frontend/src/app/api` are a backend-for-frontend; the browser never calls the backend directly.
- `tests/`: pytest unit tests and PostgreSQL integration proofs. `frontend/e2e/`: Playwright browser tests.
- `deploy/`: nginx, production compose, backup, restore, rehearsal and monitoring scripts. Runbook: `docs/operations/M7_RELEASE_RUNBOOK.md`.

## Running locally

- `docker compose up -d` starts PostgreSQL and Redis. The `medibook-mailpit` container catches email on 127.0.0.1:1025, inbox at http://127.0.0.1:8025.
- `bash ~/medibook-tools/medibook_local.sh start|stop|status` runs the backend on :8000 and the frontend on :3000 and writes test logins to `~/medibook-local-logins.txt`.
- Test accounts: `PYTHONPATH=. .venv/bin/python scripts/seed_e2e_accounts.py /tmp/e2e.env`.

## Checks before every commit

- Backend: `.venv/bin/python -m pytest -q`
- Frontend: `cd frontend && npm run build && ./node_modules/.bin/tsc --noEmit && npm run lint`
- Browser tests: start a backend and `next start` on free ports, point the frontend at that backend with `BACKEND_URL` and `MEDIBOOK_INTERNAL_API_URL`, then run Playwright with `E2E_BASE_URL` and the seeded accounts. `~/medibook-tools/fix_batch1b.sh` has the exact commands.
- Release gate: `bash ~/medibook-tools/m6_gate.sh`; with `--commit` it commits and pushes when everything is green.
- Full certification before a release: `bash ~/medibook-tools/m7_certify.sh`.

## Rules

- Tenancy is enforced by the backend. Patient appointment calls send `X-MediBook-Hospital-Slug`; staff routes resolve the hospital with `frontend/src/lib/server/hospital-context.ts`.
- Booking, cancelling and rescheduling need explicit patient confirmation. The AI never writes to the database directly.
- Never commit secrets, `.env` files or backup copies (`*.bak*`, `*.before-*`, `*.pre_*`); git is the backup.
- Element styles in `frontend/src/app/globals.css` stay inside `@layer base` so Tailwind classes win. Text contrast at least 4.5:1; every form control has a label.
- Show errors with `readErrorMessage` from `frontend/src/lib/error-message.ts`, never raw JSON.
- Health data is sensitive under Bangladesh's Personal Data Protection Ordinance 2025: log no patient details and keep data to the minimum.

## Next task: embedding and patient sign-in (batch 2)

Patients must be able to chat and book inside a hospital's website without leaving it or creating an account first.

1. Anyone can start chatting without signing in; doctor search and availability are already public.
2. Identity is checked only at the booking step, inside the widget: name, phone or email, a 6-digit code, then confirm. Email codes work today; SMS comes later behind the same interface.
3. The verified session is a short-lived token held by the widget, sent as a header rather than a cookie, and scoped to one hospital.
4. Each hospital has a list of websites allowed to embed it. Embed pages send a matching `Content-Security-Policy: frame-ancestors` header, and nginx (`deploy/nginx/medibook.conf`, `deploy/nginx/medibook-https.conf.template`) stops sending `X-Frame-Options: DENY` for embed paths only.
5. The installer script (`frontend/src/app/api/widget/[hospitalSlug]/installer/route.ts`) reads the hospital's colours, logo, greeting and language from its settings.
6. Fix or remove the widget reschedule route (`frontend/src/app/api/widget/[hospitalSlug]/reschedule/route.ts`), which lists appointments without the hospital header.
7. Add a test page on a different origin that plays the hospital website, and Playwright tests that book, reschedule and cancel through the embedded widget.

Done means: every check above passes, the new embed tests pass, and the release gate commits.
