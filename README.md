# MediBook AI

MediBook AI is a private multi-hospital SaaS appointment assistant designed to embed into hospital websites. Patients interact through a ChatGPT-like interface while doctor discovery, availability, booking, cancellation, rescheduling, tenancy, and transaction safety remain controlled by deterministic backend services.

## Current capabilities

- Multi-hospital tenant isolation
- Hospital-scoped doctor discovery and availability
- Conversational booking with explicit confirmation
- Appointment cancellation and rescheduling
- Persistent widget conversations and editable history
- Patient identity, email verification, profile, password reset, and email change
- Hospital operations dashboard
- Embeddable hospital widget
- Production security guards
- S3-compatible profile-image storage
- Purple and white patient experience

## Technology stack

- Next.js, React, TypeScript
- FastAPI, Python
- PostgreSQL
- Redis
- Ollama

## Safety model

MediBook AI is an appointment administration product, not a diagnostic system. Symptom input is limited to safe specialty guidance. Booking, cancellation, and rescheduling require explicit patient confirmation before database mutation.

## Verified foundations

- Identity V2
- Appointment Tenancy V2
- Transaction Safety V2
- Conversation Tenancy V2
- Frontend Quality V1
- Production security wiring
- Hospital embed installer
- S3-compatible profile storage adapter

## Local development

Backend:

```bash
export PYTHONPATH="$PWD"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

## Quality checks

```bash
.venv/bin/python -m pytest -q
cd frontend
npx tsc --noEmit
npx eslint .
```

## Secrets

Never commit real .env files, credentials, JWT or OTP secrets, SMTP passwords, database credentials, or object-storage keys. Use environment example files and deployment secret management.

## Project status

Active development. Production provider activation and the final deployment launch gate are still in progress.

## License

Private proprietary project. All rights reserved.
