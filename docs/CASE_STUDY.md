# FlowPilot — Case Study

## Problem

Small service businesses (salons, studios, repair shops) receive
customer messages the same way: a mix of bookings, price questions,
complaints and reschedule requests in one chat. Someone has to read
everything, figure out what each message is, write it down somewhere,
and remember to follow up. Bookings get lost exactly there — between
the chat and the notebook.

## Solution

FlowPilot is a small intake pipeline with a CRM on top:

- a webhook accepts customer messages (Telegram or the built-in web
  form);
- a swappable AI layer classifies each message (intent, service,
  date/time) and returns a confidence score;
- high-confidence requests go straight into the pipeline; ambiguous
  ones are flagged for manual review;
- managers work the requests in a dashboard: statuses, filters,
  client history, analytics.

The AI layer is deliberately isolated: providers (Mock, OpenAI, Qwen)
implement one interface and **never write to the database** — the
service layer validates what the AI proposed and decides what gets
stored. The AI is a source of suggestions, not a source of truth.

## User Flow

1. A customer sends a message ("I'd like to book a manicure tomorrow at
   15:00") to the Telegram bot or it is submitted through the web form.
2. `POST /api/webhooks/telegram` receives the update; nginx maps
   Telegram's `secret_token` header onto the header the backend
   verifies with `hmac.compare_digest`.
3. Idempotency check: a repeated `update_id` never creates a second
   request (unique constraint + pre-check).
4. The client is found or created by `telegram_user_id`.
5. `AIAnalysisService` calls the provider; the response is parsed and
   validated into an `AIResult` (intent, confidence, service, date,
   time) — invalid JSON, provider failures and unknown intents all
   fall back safely instead of failing the request.
6. `RequestService` applies business rules (confidence triage:
   ≥0.85 auto / 0.60–0.85 review / <0.60 manual) and writes
   `Request` + `Message` + `AIAnalysis`.
7. A manager sees the request in the dashboard, fixes the AI's guess
   if needed (service, status), and moves it through the pipeline —
   every status change lands in the request's history.

## Architecture

```
Telegram / Web form
        ↓
      Nginx          static files, reverse proxy, rate limiting
        ↓
     FastAPI         routing, validation, JWT auth, rate limiting
        ↓
 Service layer       RequestService · TelegramService · ClientService
                     AIAnalysisService · AnalyticsService
        ↓                                ↓
 AIProvider (Mock/OpenAI/Qwen)     Repositories (SQLAlchemy)
        ↓ AIResult                       ↓
        └────────────► PostgreSQL ◄──────┘
                          ↓
                      REST API
                          ↓
                  React dashboard
```

- **API layer** — HTTP concerns only, no business logic.
- **Service layer** — all business rules; the only writer to the
  database.
- **Repository layer** — all SQL lives here (parameterized ORM).
- **AI layer** — behind an interface, mockable, with fallbacks.
- **Frontend** — React + TypeScript; API types are generated from the
  live OpenAPI schema, so the client contract can't silently drift.

## Security

JWT auth (HS256, pinned algorithm), bcrypt hashing, backend-enforced
RBAC, secret-verified idempotent webhook, two-layer rate limiting
(nginx + FastAPI), input bounds everywhere, non-root container,
PostgreSQL without published ports, no secrets in git/images/bundle,
sanitized error responses, per-business data isolation. Reviewed stage
by stage in [SECURITY.md](./SECURITY.md).

## Docker

One command reproduces the whole environment:

```bash
docker compose up --build -d
```

PostgreSQL (health-checked) → backend (Alembic migrations + optional
demo seed on start) → frontend init container (multi-stage build, only
`dist/` is shipped — no node_modules in the runtime image) → nginx
(serves static files from a shared volume, proxies `/api`). Production
HTTPS is added without touching the repo: certificates plus a
per-domain `ssl.conf` are mounted through a `docker-compose.override.yml`
that lives on the server, so `git pull` never conflicts.

## Interesting Engineering Problem

The suite was green locally, the container crashed on import.

The backend was developed on Python 3.14; the Docker image uses 3.12
(as planned). On 3.12 the app died with `TypeError: 'function' object
is not subscriptable` while merely *importing* a repository module.
The culprit: a method named `list` shadowed the builtin `list` inside
the class body, so the *next* method's `-> list[Request]` annotation
resolved to the method itself. Python 3.14 (PEP 649, lazy annotations)
never evaluates that expression at import time — 3.12 does.

The fix was one line per file: `from __future__ import annotations`.
The real lesson stayed: a green local suite says nothing about the
runtime you actually ship. After that, the test suite also ran inside
the 3.12 container, and a second instance of the same class of bug
(duck-typing differences between SQLite and PostgreSQL) was caught the
same way — by testing against the real target, not the convenient one.

## Testing

**67/67 passed**, run locally (Python 3.14) and inside the Docker
image (Python 3.12). The suite covers auth, request lifecycle and
permissions, business isolation, the mock AI (classification, invalid
JSON fallback, retry-once, unknown intent mapping), the Telegram
webhook (valid/missing/wrong secret, duplicate updates), and the
security additions (JWT tampering and expiry, password exposure, rate
limits returning 429, input bounds, 500 responses that leak nothing).
No CI exists — tests are run manually, which is stated honestly.

## Deployment

A full guide was written and the HTTPS path was **rehearsed locally**:
a self-signed certificate, the documented `prod/ssl.conf` and
`docker-compose.override.yml` were applied to the running stack, and
health/login/stats/redirect/rate-limit and the Telegram
secret-header mapping were all verified through port 443.

**An actual production VPS deployment has not been performed.** The
guide (Ubuntu, UFW, certbot, renewal cron, `pg_dump` backups, update
and rollback procedure) is in [DEPLOYMENT.md](./DEPLOYMENT.md) and
will be executed by a human later.

## Limitations

In-memory rate limiting (single process); JWT in localStorage; HTTPS
requires the deployment step; Telegram not verified end-to-end with a
real bot; MockProvider is keyword matching, not real NLP; demo
credentials are public by design; no CI.

## Result

Not "production-ready" — that claim would be unverified. What exists
and is verified: a reproducible Docker stand (PostgreSQL, backend,
frontend, nginx), a 67-test suite passing on two Python versions, a
staged security review with fixes, two-layer rate limiting, a rehearsed
HTTPS path, and honest documentation of every limitation. A full
end-to-end chain (webhook → AI → request → manager dashboard) works in
demo mode with one command.

## Portfolio Snippets

**GitHub repository description:**

> FlowPilot — AI-assisted intake for small businesses: Telegram/web
> messages → intent extraction → trackable requests in a FastAPI +
> React + PostgreSQL CRM. Docker Compose, 67 tests, security review.

**Resume bullets:**

- Built an AI-assisted request intake platform (FastAPI, React,
  PostgreSQL, Docker) with a swappable AI provider layer (mock/OpenAI/
  Qwen), structured-output validation and confidence-based triage.
- Designed a layered backend (API / services / repositories) with
  JWT + RBAC, an idempotent secret-verified Telegram webhook, and
  two-layer rate limiting (nginx + FastAPI); documented a staged
  security review.
- Delivered a 67-test suite passing on both dev (3.14) and production
  (3.12) runtimes; caught and fixed cross-runtime and SQLite-vs-
  PostgreSQL contract bugs by testing against real targets.
- Containerized the whole stack (multi-stage builds, non-root backend,
  nginx as the single entry point) and wrote a VPS deployment guide
  with a locally rehearsed Let's Encrypt HTTPS path.
