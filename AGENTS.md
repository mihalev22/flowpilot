# AGENTS.md — FlowPilot

> Версия: скорректированная (v1.1). Изменения относительно исходного варианта отмечены пометкой **[FIX]**.

## 1. Project

**FlowPilot** — AI-платформа для автоматизации обработки входящих обращений малого бизнеса.

Основной сценарий:

```text
Клиент
  ↓
Telegram / Web
  ↓
Webhook
  ↓
FastAPI
  ↓
AI Service (только интерпретация, без записи в БД)
  ↓
Structured JSON (AIResult)
  ↓
Pydantic validation
  ↓
Service Layer (бизнес-логика, решает что писать в БД)
  ↓
PostgreSQL
  ↓
REST API
  ↓
React Dashboard
  ↓
Менеджер
```

Главная демонстрационная цепочка проекта:

> Клиент отправляет сообщение → система принимает webhook → AI определяет намерение и извлекает данные → данные валидируются → создаётся заявка → менеджер видит её в Dashboard.

---

## 2. Developer Context

Разработчик — студент 2 курса «Информационные системы и технологии», начинающий уровень.

Правила:

* не усложнять без необходимости;
* не использовать технологии ради резюме;
* объяснять архитектурные решения перед кодом;
* избегать избыточной абстракции;
* код должен быть объясним на собеседовании.

---

## 3. Core Stack

**Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, JWT, pytest.

**Frontend:** React, TypeScript, Vite, Tailwind CSS.

**Infrastructure:** Docker, Docker Compose, Nginx, Git.

**AI:**

```text
AIProvider (interface)
├── MockProvider     — детерминированные сценарии по ключевым словам, без API key
├── OpenAIProvider
└── QwenProvider
```

**[FIX]** MockProvider — не "один и тот же JSON всегда", а набор из ~6–8 сценариев (по intent: booking/question/complaint/price_request/cancel_booking/reschedule/other), выбираемых простым keyword-matching по входящему тексту. Это нужно, чтобы demo seed выглядел разнообразно, а не как один хардкод-ответ.

---

## 4. Repository Structure

```text
flowpilot/
│
├── backend/
│   ├── app/
│   │   ├── api/            # только HTTP: routes, dependencies
│   │   ├── core/            # config, security, exceptions
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # бизнес-логика
│   │   ├── repositories/     # доступ к БД
│   │   ├── db/                # session, base
│   │   └── main.py
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/         # API client
│   │   ├── types/
│   │   └── main.tsx
│   │
│   ├── package.json
│   └── Dockerfile
│
├── nginx/
│   └── nginx.conf
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md
```

---

## 5. Architecture Rules

**API Layer** — HTTP, request/response, auth, validation, status codes. Без бизнес-логики.

**Service Layer** — бизнес-логика: `RequestService`, `ClientService`, `AIAnalysisService`, `TelegramService`, `AnalyticsService`.

**[FIX] Явное правило:** `AIAnalysisService` вызывает `AIProvider` и возвращает `AIResult` (Pydantic-схема). Он **не имеет доступа к репозиториям и не пишет в БД**. Запись в БД (создание `Request`, `AIAnalysis`) выполняет `RequestService` после получения и валидации результата от `AIAnalysisService`. Это разделение — то, что нужно уметь объяснить на собеседовании: AI — источник предложения, а не источник истины.

**Repository Layer** — вся работа с БД, ORM/SQL не должен попадать в API endpoints.

**Models** — SQLAlchemy, описывают структуру БД.

**Schemas** — Pydantic: входные/выходные данные, включая AI structured output.

---

## 6. Database

Сущности:

```text
Business
User
Client
Service
Request   →  таблица в БД называется client_requests  [FIX]
Message
AIAnalysis
RequestStatusHistory
```

**[FIX] Причина переименования таблицы:** имя `requests` совпадает с популярной Python HTTP-библиотекой `requests` и является зарезервированным/предрасположенным к путанице словом в некоторых SQL-диалектах и ORM-инструментах. В коде (Python-класс, API-путь `/api/requests`, UI) оставляем "Request" — совпадение имени сущности с именем таблицы не обязательно.

Связи:

```text
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

Foreign keys обязательны. Индексы — там, где реально нужны (например, `client_requests.status`, `client_requests.business_id`, уникальный индекс на Telegram update, см. п.18).

Все изменения схемы — только через Alembic migrations.

---

## 7. Request Statuses

```text
NEW
IN_PROGRESS
CONFIRMED
COMPLETED
CANCELLED
```

Статусы централизованы (Python Enum + соответствующий Postgres enum или check constraint), не строки по всему проекту.

---

## 8. AI

AI отвечает только за интерпретацию сообщения, не изменяет БД напрямую.

Поток:

```text
Message
 ↓
AIProvider.analyze(text) → raw response
 ↓
Parsing / JSON schema validation → AIResult (Pydantic)
 ↓
AIAnalysisService возвращает AIResult вызывающему коду
 ↓
RequestService: валидация бизнес-правил + запись в БД
```

Обработка ошибок AI (обязательно, все ветки):

* невалидный JSON от провайдера → fallback на `intent=other`, `confidence=0`, requires_manual_review=true;
* timeout → retry один раз, затем то же fallback-поведение;
* API error / нет API key → если `AI_MODE=mock`, не применимо; если `AI_MODE=openai/qwen` и ключа нет — явная ошибка конфигурации при старте, а не в рантайме;
* неизвестный intent от модели → маппится в `other`.

---

## 9. AI Intents

```text
booking
question
complaint
price_request
cancel_booking
reschedule
other
```

Новые intents не добавляются без пересмотра фронтенда и БД (это enum, а не свободная строка).

---

## 10. AI Confidence

```text
>= 0.85   → можно автоматически обработать (заявка создаётся сразу со статусом NEW)
0.60–0.85 → показывается менеджеру для проверки перед подтверждением
< 0.60    → обязательно ручная обработка (заявка помечена requires_manual_review=true)
```

Confidence — внутренний сигнал качества модели, не калиброванная вероятность. Не показывать пользователю как "% точности" без оговорки.

---

## 11. Mock AI

```env
AI_MODE=mock
```

**[FIX]** MockProvider возвращает результат, зависящий от входного текста (keyword matching на русском/английском для intent + попытка извлечь услугу/дату простыми правилами), а не константу. Нужен для локальной разработки, тестов, демонстрации, CI, отсутствия платного API key.

---

## 12. Authentication

* password hashing (bcrypt/argon2 через passlib);
* JWT access token;
* protected routes;
* role-based access: `admin`, `manager`.

**[FIX] Явное разграничение по UI, не только по API:**

* `admin` — управление пользователями, статистика, Business settings (включая место, где вводятся/меняются AI API key, Telegram token — сами значения никогда не возвращаются в ответах API, только факт "задано/не задано");
* `manager` — заявки, статусы, клиенты; **не имеет доступа к `/settings`** (там ключи интеграций) — это должно проверяться и на backend (403), и скрываться в UI, а не только скрываться в UI.

Пароли не хранятся в открытом виде. JWT secret не хранится в Git.

---

## 13. Security

Обязательно: `.env`, `.env.example`, `.gitignore`, password hashing, JWT, CORS, input validation, SQLAlchemy ORM (без raw SQL со string-конкатенацией), rate limiting на публичных webhook/auth endpoints, проверка Telegram webhook (секрет в пути или заголовке), безопасная обработка ошибок.

Никогда: коммитить секреты, вставлять credentials в код, возвращать stack trace пользователю, использовать `eval`, отключать security "для удобства".

---

## 14. Environment Variables

```env
DATABASE_URL=
JWT_SECRET=
JWT_EXPIRE_MINUTES=60
AI_MODE=mock
AI_API_KEY=
AI_PROVIDER=mock
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
CORS_ORIGINS=http://localhost:5173
```

`.env` не коммитится. В репозитории только `.env.example` с безопасными placeholder-значениями.

---

## 15. API

```text
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

Правильные HTTP status codes: 200/201/400/401/403/404/409/422/500.

---

## 16. Frontend

Страницы: `/login`, `/register`, `/`, `/requests`, `/requests/:id`, `/clients`, `/clients/:id`, `/analytics`, `/settings` (только admin, см. п.12).

loading states, empty states, error states, skeletons, toast notifications, responsive layout, form validation.

Стиль: минималистичный B2B SaaS. Без чрезмерных градиентов, glassmorphism, "AI neon" эстетики. usability > visual effects.

---

## 17. Dashboard

Новые / В работе / Подтверждено / Завершено, заявки по дням, источники, популярные услуги, последние обращения. Все данные — из backend API, без fake statistics на фронтенде.

---

## 18. Telegram

```text
Telegram
 ↓
POST /api/webhooks/telegram
 ↓
Проверка секрета/подписи
 ↓
Find/create client (по telegram_user_id)
 ↓
Create message
 ↓
AI analysis
 ↓
Create client_request
 ↓
Save AIAnalysis
```

**[FIX] Конкретный механизм идемпотентности:** уникальный constraint `UNIQUE(business_id, telegram_update_id)` на таблице `messages` (или отдельной таблице `telegram_updates`). При повторном update — `INSERT ... ON CONFLICT DO NOTHING` / проверка перед вставкой, без создания дубликата заявки. Это конкретное решение, а не абстрактное "webhook должен быть идемпотентным".

---

## 19. Error Handling

Централизованные exception handlers в FastAPI. Пример ответа:

```json
{ "detail": "Request not found" }
```

Никогда: traceback, SQLAlchemy exception текст, внутренние пути файлов — наружу.

---

## 20. Logging

`logging`, не `print()`. Не логировать пароли, API keys, JWT, полные заголовки с токенами.

---

## 21. Testing

pytest. Минимум:

* **Auth:** регистрация, логин, неверные креды, protected endpoint.
* **Requests:** create, get, update status, permissions (manager vs admin).
* **AI:** mock provider — валидный JSON, невалидный JSON, provider error/timeout.
* **Telegram:** валидный webhook, невалидный payload, повторный update (дубликат не создаётся).

---

## 22. Docker

`docker compose up` запускает: `frontend`, `backend`, `postgres`, `nginx`. Установка PostgreSQL вручную не требуется.

---

## 23–34. Development Workflow, Overengineering, Code Quality, Git, Windows, Agent Rules, Honesty, Metrics, Priority, First Task

Без изменений по содержанию — сохраняются как в исходном документе: небольшие этапы, никакого Kubernetes/Redis/Kafka/микросервисов без обоснованной необходимости, типизированный читаемый код, понятные git-коммиты, все команды — в PowerShell/CMD-варианте, "не проверено" вместо ложных утверждений об успехе, никаких выдуманных бизнес-метрик.

**Порядок реализации (не менять без причины):**

```text
1. Architecture
2. Backend foundation
3. Database
4. Authentication
5. Requests
6. Clients
7. AI service
8. Telegram
9. Frontend
10. Analytics
11. Tests
12. Docker
13. Security review
14. Deployment
15. README
```

**Первая задача агента:** не писать код. Проанализировать репозиторий, сравнить с этой архитектурой, предложить план, указать риски, дождаться подтверждения.

> Сначала понять систему, потом менять систему.
