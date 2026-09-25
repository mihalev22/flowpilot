# FlowPilot

AI-assisted intake for small businesses: customer messages from Telegram
or the built-in web form are classified by an AI layer (intent, service,
date/time, confidence), turned into trackable requests, and handed to
managers through a lightweight CRM dashboard.

**Problem:** a small salon or studio gets bookings, price questions,
complaints and reschedule requests mixed in one chat. Answering,
trusting memory, and copy-pasting them into a notebook is where
bookings get lost.

**Solution:** a message lands on a webhook, gets validated, is
interpreted by a swappable AI provider (mock by default, OpenAI/Qwen
ready), and becomes a request with a confidence score. High-confidence
requests flow straight into the pipeline; low-confidence ones are
flagged for manual review.

> Status: **portfolio / demo project.** Fully dockerized and covered by
> tests and a security review, but **not deployed to production** — see
> [Known Limitations](#known-limitations).

```
Client message → webhook → validation → AI analysis → structured JSON
→ request in PostgreSQL → React dashboard → manager review
```

## Features

- JWT authentication with roles (`admin` / `manager`), enforced by the
  backend (UI hiding is convenience, not the security layer).
- Request pipeline: `NEW → IN_PROGRESS → CONFIRMED → COMPLETED` /
  `CANCELLED` with full status history.
- AI intent extraction with confidence-based triage: ≥0.85 auto,
  0.60–0.85 manager review, <0.60 manual handling.
- Swappable AI provider behind one interface: **Mock** (default, no API
  key, Russian/English keyword matching), OpenAI, Qwen — with JSON
  parsing, one retry, and safe fallback on provider errors.
- Telegram webhook: secret-verified, idempotent (duplicate updates
  never create duplicate requests).
- Client directory with search and per-client request history.
- Dashboard and analytics: status counts, 14-day trend, sources,
  top services, recent requests.
- Two-layer rate limiting: nginx `limit_req` + FastAPI in-memory
  limiter (429 with `Retry-After`).
- One-command Docker stack: PostgreSQL, backend, frontend, nginx.
- Alembic migrations applied automatically on container start;
  idempotent demo seed (only when `AI_MODE=mock`).
- React frontend (Russian UI): 9 pages, loading/error/empty states,
  skeletons, toasts; API types generated from the live OpenAPI schema.

## Architecture

```
Telegram / Web form
        ↓
POST /api/webhooks/telegram        POST /api/requests
        ↓ secret check                    ↓ JWT
      Nginx  — static files, reverse proxy, rate limiting (TLS in production)
        ↓
      FastAPI  — routing, validation, auth, rate limiting
        ↓
   Service layer  — RequestService, TelegramService, ClientService,
                    AIAnalysisService, AnalyticsService
        ↓                          ↓
  AIProvider (Mock/OpenAI/Qwen)   Repositories
        ↓ AIResult (Pydantic)            ↓
        └──────────────►  PostgreSQL  ◄──┘
                            ↓
                        REST API
                            ↓
                     React dashboard
```

AI processing pipeline (the AI layer never writes to the database —
it only proposes, services decide):

```
Message → AIProvider.analyze(text) → raw response
        → JSON parsing + Pydantic validation → AIResult
        → confidence check → auto / needs review / manual only
        → RequestService writes Request + Message + AIAnalysis
```

## Tech Stack

| Area | Technologies |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, TanStack Query, React Hook Form, Zod, openapi-typescript |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PyJWT, bcrypt, httpx |
| Database | PostgreSQL 16 (SQLite in-memory for the test suite) |
| Infrastructure | Docker, Docker Compose, nginx, multi-stage builds |
| Security | JWT HS256, bcrypt, RBAC, two-layer rate limiting, env-only secrets |
| Testing | pytest (67 tests), FastAPI TestClient |

## Security

- bcrypt password hashing; passwords truncated to the 72-byte bcrypt limit
- JWT HS256 with pinned algorithm and expiry
- Role checks on the backend for admin-only endpoints
- `password_hash` never leaves the API
- webhook secret compared with `hmac.compare_digest`
- FastAPI rate limiting (429) on login/register/webhook + nginx `limit_req`
- input length limits on every user-controlled field
- parameterized ORM queries only (no raw SQL)
- backend runs as non-root; PostgreSQL has no published ports; backend
  reachable only through nginx
- no secrets in git history, images, or the frontend bundle (audited)
- error responses sanitized (no tracebacks, paths, or internals)
- per-business data isolation; webhook idempotency

Details and known limitations: [docs/SECURITY.md](docs/SECURITY.md).

## Docker / Deployment

### Local / Demo

```bash
cp .env.example .env      # set POSTGRES_PASSWORD and JWT_SECRET
docker compose up --build -d
curl http://localhost/api/health
```

The stack: PostgreSQL (health-checked) → backend (migrations + optional
demo seed + uvicorn) → frontend init container (copies `dist/` to the
shared volume) → nginx. Demo login (only with `AI_MODE=mock` on an
empty database — public by design):
`admin@luna.ru / admin12345` (admin), `maria@luna.ru / manager12345`
(manager).

Run the test suite inside the backend container (Python 3.12):

```bash
docker run --rm -v "$(pwd)/backend/tests:/app/tests" \
  --entrypoint pytest flowpilot-backend -q
```

### Production

A complete VPS guide exists — Ubuntu, UFW, Let's Encrypt HTTPS
(certbot), certificate renewal cron, `pg_dump` backups, update
procedure: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

The HTTPS path (certificates + `docker-compose.override.yml` +
per-domain `ssl.conf`, including the Telegram secret-header mapping)
was rehearsed locally with a self-signed certificate and verified
end-to-end against the running stack. **An actual production VPS
deployment has not been performed in this project.**

## Testing

**67/67 passed** — run locally (Python 3.14) and inside the Docker
image (Python 3.12). Coverage: auth (register/login/bad
credentials/protected endpoints), requests (create, filters, status
transitions, permissions, business isolation), AI (mock classification,
invalid JSON fallback, retry, unknown intents), Telegram webhook
(valid/missing/wrong secret, duplicate updates), security (JWT
tampering/expiry, password exposure, rate limits, input bounds, error
leak prevention). No CI pipeline — tests are run manually.

## Screenshots

| Login | Dashboard |
|---|---|
| ![Login](docs/screenshots/01-login.png) | ![Dashboard](docs/screenshots/02-dashboard.png) |

| Requests | Request detail (AI analysis, status handling) |
|---|---|
| ![Requests](docs/screenshots/03-requests.png) | ![Request detail](docs/screenshots/04-request-detail.png) |

| Analytics | Settings (admin) |
|---|---|
| ![Analytics](docs/screenshots/07-analytics.png) | ![Settings](docs/screenshots/08-settings.png) |

All screenshots: [docs/screenshots/](docs/screenshots/).

## Project Structure

```
flowpilot/
├── backend/
│   ├── app/
│   │   ├── api/            # routes, dependencies
│   │   ├── core/           # config, security, exceptions, rate limiting
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # business logic
│   │   ├── repositories/   # database access
│   │   ├── db/             # engine, session, base
│   │   ├── scripts/        # demo seed
│   │   └── main.py
│   ├── alembic/            # migrations
│   ├── tests/              # 67 tests
│   ├── Dockerfile
│   └── entrypoint.sh       # migrations + seed + uvicorn
├── frontend/               # React + TypeScript + Vite + Tailwind
│   └── src/{pages, components, contexts, services, types}
├── nginx/                  # reverse proxy configuration
├── docs/                   # SECURITY.md, DEPLOYMENT.md, screenshots
└── docker-compose.yml
```

## What I Learned

**"Works locally" ≠ "works in the target runtime."** The whole backend
passed 51 tests on my machine (Python 3.14) and crashed on import in
the Docker image (Python 3.12). The cause: a repository method named
`list` shadowed the builtin `list` inside the class body, so the next
method's `list[Request]` annotation resolved to the *method*, not the
builtin. Python 3.14 hides this (PEP 649 made annotations lazy), 3.12
evaluates them eagerly. The fix was one line per file —
`from __future__ import annotations`. Lesson: test in the same runtime
you ship, and a green local suite proves nothing about the container.

**Dead libraries bite later.** `passlib` (last release 2020) broke with
modern `bcrypt` on Python 3.14 — it crashed on a test hash. Dropping
the wrapper and using `bcrypt` directly removed a dead dependency and
made the failure mode obvious.

**SQLite forgives, PostgreSQL doesn't.** Two schema bugs survived every
SQLite run and exploded on PostgreSQL: `alembic --autogenerate`
duplicated CHECK constraints (same name twice in one table), and a
history table with two enum columns shared one constraint name.
SQLite silently accepted both. Lesson: run migrations against the real
database before calling a schema done.

## Engineering Decisions

- **Docker Compose** — the whole environment (DB, backend, frontend,
  nginx) in one file; a reviewer reproduces the stack with one command.
- **PostgreSQL in production, SQLite for tests** — tests stay fast and
  parallel; the real engine is still exercised by running the suite
  inside the container and by the compose stack.
- **nginx as the single entry point** — static files served without
  touching Python, rate limiting before the app, TLS terminated at the
  infrastructure layer.
- **Non-root backend container** — cheap hardening, standard practice.
- **Two rate-limiting layers** — nginx stops floods even if the app is
  degraded; FastAPI limits precisely per route and works without nginx
  (local dev). Defense in depth.
- **In-memory rate limiter** — honest trade-off: correct for a single
  process, which is this project's scale. Scaling out means Redis or a
  shared store; adding it now would be speculative infrastructure.
- **JWT in localStorage** — simpler than httpOnly cookies + CSRF
  protection, with a documented XSS trade-off. Acceptable at this
  stage, revisit for real production.
- **HTTPS in the deployment layer** — the application never sees TLS;
  certificates and renewal belong to the infrastructure (see
  DEPLOYMENT.md), which keeps the app container simple and identical
  in dev and prod.

## Known Limitations

- In-memory rate limiting covers a single process (Redis needed for
  horizontal scaling).
- JWT in `localStorage` — an XSS would expose the token.
- HTTPS requires the production deployment (rehearsed locally, not
  performed on a VPS).
- Production VPS deployment was **not** executed — only documented.
- Telegram integration is not verified end-to-end with a real bot
  (the webhook endpoint and secret-header mapping are verified).
- `AI_MODE=mock` is the demo default: MockProvider does keyword
  matching, not real NLP.
- Demo credentials are public by design; the seed runs only when
  `AI_MODE=mock` on an empty database.
- No CI pipeline — tests are run manually.

## Documentation

- [docs/SECURITY.md](docs/SECURITY.md) — security review: what was
  checked, fixed, and what remains limited.
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — VPS deployment guide
  (Ubuntu, Docker, Let's Encrypt, backups, updates).
- [docs/CASE_STUDY.md](docs/CASE_STUDY.md) — portfolio case study.
- [AGENTS.md](AGENTS.md) — the original build plan and architecture
  rules the project follows.
