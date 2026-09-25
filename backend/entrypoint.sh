#!/bin/sh
set -e

alembic upgrade head

if [ "$AI_MODE" = "mock" ]; then
    echo "AI_MODE=mock: загрузка демо-данных (если БД пуста)"
    python -m app.scripts.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
