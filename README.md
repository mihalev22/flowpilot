# FlowPilot

AI-powered customer request automation platform for small businesses.

> ⚠️ Status: **Demo / portfolio project**, work in progress. Not production-ready — security, testing and deployment have not yet been fully verified (see Roadmap).

FlowPilot ingests customer messages (Telegram, web form), uses an LLM to extract structured intent and booking data, and turns them into trackable requests in a lightweight CRM dashboard.

**Core flow:**

```
Client message → Telegram webhook → FastAPI → AI Service → structured JSON
→ Pydantic validation → PostgreSQL → REST API → React dashboard → Manager review
```

## Features

- [ ] JWT authentication with role-based access (`admin`, `manager`)
- [ ] Request (CRM ticket) management with status pipeline
- [ ] Client directory with request history
- [ ] AI intent extraction with confidence-based triage
- [ ] Swappable AI provider (mock / OpenAI / Qwen) via a common interface
- [ ] Telegram webhook integration, idempotent by design
- [ ] Analytics dashboard (requests by day, source, service)
- [ ] Fully dockerized local setup (`docker compose up`)

*(Checklist will be updated as each stage lands — see AGENTS.md for the build order.)*

## Architecture

```
                Telegram
                   │
                   ▼
                Webhook
                   │
                   ▼
              FastAPI API
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   AI Service             PostgreSQL
        │                     │
        ▼                     │
 Structured JSON              │
        │                     │
        └──────────┬──────────┘
                   ▼
                React
                   │
                   ▼
               Dashboard
```

The AI layer is isolated behind an `AIProvider` interface so the underlying model/provider can be swapped without touching business logic:

```
AIProvider
├── MockProvider    (default, no API key required)
├── OpenAIProvider
└── QwenProvider
```

AI output is never trusted directly — every result passes through Pydantic validation and can be corrected manually by a manager before a request is confirmed.

Full details, database schema and API contract: see [AGENTS.md](./AGENTS.md).

## Tech Stack

**Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, JWT, pytest
**Frontend:** React, TypeScript, Vite, Tailwind CSS
**Infrastructure:** Docker, Docker Compose, Nginx

## Screenshots

*(to be added once the frontend is built)*

## Installation

### Prerequisites

- Docker Desktop
- Git

### Local setup

```powershell
git clone https://github.com/<your-username>/flowpilot.git
cd flowpilot
copy .env.example .env
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- Backend docs (Swagger): http://localhost:8000/docs

### Demo data

After the containers are up, seed demo data (1 business, 2 users, 10 clients, 20 requests):

```powershell
docker compose exec backend python -m app.scripts.seed
```

*(Command name will be finalized once the seed script is implemented.)*

## Environment variables

See [`.env.example`](./.env.example) for the full list. Key ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for signing access tokens — never commit a real value |
| `AI_MODE` | `mock` (default, no API key) or `live` |
| `AI_PROVIDER` | `mock` / `openai` / `qwen` |
| `AI_API_KEY` | Only required if `AI_MODE=live` |
| `TELEGRAM_BOT_TOKEN` | Only required for real Telegram integration |
| `TELEGRAM_WEBHOOK_SECRET` | Used to verify incoming webhook requests |

## Docker

```powershell
docker compose up --build
docker compose down
```

Services: `frontend`, `backend`, `postgres`, `nginx`.

## API

Interactive OpenAPI/Swagger docs are served at `/docs` once the backend is running. Key endpoints (see AGENTS.md §15 for the full contract):

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

GET    /api/requests
POST   /api/requests
GET    /api/requests/{id}
PATCH  /api/requests/{id}

GET    /api/clients
GET    /api/clients/{id}

GET    /api/dashboard/stats

POST   /api/webhooks/telegram
```

## Database

Core entities: `Business`, `User`, `Client`, `Service`, `Request` (table: `client_requests`), `Message`, `AIAnalysis`, `RequestStatusHistory`.

```
Business
│
├── Users
├── Clients
├── Services
└── Requests (client_requests)
      │
      ├── Messages
      ├── AIAnalysis
      └── StatusHistory
```

Schema changes are managed exclusively through Alembic migrations.

## AI pipeline

```
Message → AIProvider.analyze(text) → raw response
        → JSON schema validation → AIResult
        → confidence check → auto-process / needs review / manual only
        → RequestService writes to DB (AI never writes directly)
```

Supported intents: `booking`, `question`, `complaint`, `price_request`, `cancel_booking`, `reschedule`, `other`.

Confidence thresholds:

| Confidence | Behavior |
|---|---|
| ≥ 0.85 | Auto-processed |
| 0.60–0.85 | Flagged for manager review |
| < 0.60 | Manual processing required |

Confidence is an internal model-quality signal, not a calibrated probability.

## Telegram integration

Webhook flow: `POST /api/webhooks/telegram` → payload validation → find/create client → create message → AI analysis → create request. Idempotency is enforced with a unique constraint on `(business_id, telegram_update_id)`, so duplicate Telegram updates never create duplicate requests.

For local development, a mock webhook endpoint/script is provided so the full pipeline can be exercised without configuring a real Telegram bot.

## Testing

```powershell
docker compose exec backend pytest
```

Coverage focus: auth, request lifecycle, AI mock provider (valid/invalid/error paths), Telegram webhook (including duplicate-update handling).

*(Not yet verified — will be updated once the test suite is written and actually run.)*

## Deployment

*(To be documented once VPS deployment is completed and verified. Not done yet — do not treat this project as production-ready before this section is filled in.)*

## Roadmap

- [ ] Backend foundation & database migrations
- [ ] Authentication & roles
- [ ] Requests & clients CRUD
- [ ] AI service (mock + real provider)
- [ ] Telegram webhook
- [ ] Frontend dashboard
- [ ] Analytics
- [ ] Docker Compose setup
- [ ] Test suite
- [ ] Security review
- [ ] VPS deployment
- [ ] Screenshots + final polish

## What I learned

*(To be filled in honestly at the end of the project — real engineering takeaways only, no invented metrics.)*
