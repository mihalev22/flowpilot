# Security Review

Stage 13 of the build plan. Verified by code audit, 67 automated tests
(51 existing + 16 security), and manual checks against the Docker stack
(nginx → FastAPI → PostgreSQL). Status legend: PASS — existing
implementation verified; FOUND → FIXED → TESTED — issue found and fixed.

## Authentication

Status: PASS (tests added)

- Password hashing: bcrypt via `hashpw`/`gensalt`, passwords truncated to
  the 72-byte bcrypt limit (`app/core/security.py`). No plaintext storage.
- JWT: HS256 with the algorithm pinned in `jwt.decode` (no `alg`
  confusion), expiry enforced, secret from `JWT_SECRET` env.
- Expired, tampered (payload `sub` replaced, signature kept), and
  structurally broken tokens all return 401 (`tests/test_security.py`).
- `password_hash` never appears in any response: `UserOut` schema only.
- Passwords, tokens and secrets are never logged.

## Authorization

Status: PASS

- Roles: `admin`, `manager`. Backend enforces via `require_admin`
  dependency (`app/api/deps.py`): `/api/dashboard/stats` and
  `/api/settings` return 403 for managers even when called directly,
  bypassing the UI. Frontend hiding is convenience, not the security layer.
- No DELETE endpoints exist in the API contract (§15 of AGENTS.md), so
  nothing to protect there yet.

## Input Validation

Status: FOUND → FIXED → TESTED (3 minor gaps)

- Pydantic bounds everywhere: email format, password 8–128, name lengths,
  request text 1–4000, enums for status/intent/source, pagination
  `limit` 1–200 / `offset` ≥ 0, webhook payload shape.
- Fixed in this review: `search` query capped at 100 chars
  (`app/api/clients.py`); Telegram client name trimmed to 200 chars
  (`app/services/clients.py`); `AIResult` string fields bounded so an
  oversized LLM answer falls back to manual review instead of a 500
  (`app/schemas/ai_result.py`).

## SQL Injection

Status: PASS

- SQLAlchemy ORM only: every user value is a bound parameter. No raw SQL,
  no f-string SQL, no string concatenation (audited by grep over
  `app/`). Alembic migrations contain static DDL only.

## CORS

Status: PASS

- Allowed origins come from `CORS_ORIGINS` (default
  `http://localhost:5173`), credentials enabled, no wildcard. In the
  Docker deployment the frontend is same-origin behind nginx, so the CORS
  layer is effectively inert in production.

## Telegram Webhook

Status: PASS (test added)

- Secret sent via `X-Telegram-Secret` header, compared with
  `hmac.compare_digest` (`app/api/webhooks.py`).
- Missing secret, wrong secret, and unset `TELEGRAM_WEBHOOK_SECRET` all
  rejected with 403. The secret value never appears in any response.
- Duplicate updates are idempotent (unique constraint on
  `business_id + telegram_update_id`).

## Rate Limiting

Status: FOUND → FIXED → TESTED (FastAPI layer was missing)

Defense in depth, two layers:

1. **nginx `limit_req`** — 10 r/m, burst 5 on `/api/webhooks/telegram`
   (`nginx/nginx.conf`). Verified: flood returns 503 before reaching the
   app. Protects the process even if FastAPI is degraded.
2. **FastAPI in-memory** — 20 requests / 60 s per client IP per path on
   `/api/auth/login`, `/api/auth/register`, `/api/webhooks/telegram`
   (`app/core/rate_limit.py`). Returns 429 with `Retry-After`. Verified
   through nginx: 25 rapid logins → 19×401 + 6×429.

The app-level layer is needed because it works regardless of
infrastructure (local dev without nginx, future deployments) and counts
per route precisely; the nginx layer stops floods before they consume
application resources.

## Error Handling

Status: PASS (test added)

- Business errors: centralized `AppError` handler → `{"detail": "..."}`
  with proper status codes (400/401/403/404/409/422/429).
- Unexpected exceptions: 500 `{"detail": "Внутренняя ошибка сервера"}`,
  full traceback only in server logs. Tested that a raised
  `RuntimeError` leaks no message, traceback, or paths to the client.

## Secrets

Status: PASS

- `.env` files are gitignored; `.env.example` contains placeholders
  only. No real secret in git history (audited with
  `git log --all -p` pattern search: only `change-me` and test fixtures).
- Secrets are not baked into images (`.dockerignore` excludes `.env`;
  compose injects them at runtime via `env_file`).
- Frontend bundle checked: no `JWT_SECRET`, no API keys, no database
  credentials (grep over `dist/assets/*.js`).
- Demo credentials (`admin@luna.ru / admin12345`) are intentionally
  public demo values — see Known Limitations.

## Docker Security

Status: PASS

- Backend runs as non-root (`USER app`), migrations run in entrypoint.
- Frontend runtime image is alpine + `dist/` only: no node_modules, no
  source, no nginx inside.
- PostgreSQL has no published ports (internal compose network only).
- Backend exposes 8000 internally but is not published: external traffic
  can only reach nginx on port 80.

## Frontend Security

Status: PASS

- No `dangerouslySetInnerHTML` / `innerHTML`; all user text is rendered
  through React's default escaping.
- JWT access token stored in `localStorage` (trade-off, see limitations).

## Known Limitations

- In-memory rate limiting protects a single process. Horizontal scaling
  requires a shared store (e.g. Redis) — intentionally out of scope (§24
  AGENTS.md: no infrastructure without justified need).
- JWT in `localStorage` means a successful XSS would expose the token.
  httpOnly cookies + CSRF protection would be more robust; current
  trade-off is acceptable for this project stage.
- HTTPS is a deployment concern (nginx listens on 80 in this repo;
  Let's Encrypt is part of the deployment stage).
- `X-Forwarded-For` is trusted for rate limiting. This is safe while the
  backend port stays unpublished and nginx is the only entry point.
- Demo credentials from the seed script are public by design — change
  them before any real use.
- AI provider is Mock in demo mode (`AI_MODE=mock`); OpenAI/Qwen are
  called over HTTPS with the key sent only to the provider.
