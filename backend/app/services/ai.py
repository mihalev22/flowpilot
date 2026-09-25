import json
import logging
import re
import time
from abc import ABC, abstractmethod

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.models.enums import Intent
from app.schemas.ai_result import AIResult

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20.0

SYSTEM_PROMPT = (
    "Ты классифицируешь обращения клиентов малого бизнеса. "
    "Верни ТОЛЬКО валидный JSON без markdown-обёртки по схеме: "
    '{"intent": "booking|question|complaint|price_request|cancel_booking|reschedule|other", '
    '"confidence": число от 0 до 1, "service_name": строка или null, '
    '"preferred_date": строка или null, "preferred_time": строка или null, '
    '"requires_manual_review": булево значение}. '
    "Извлеки услугу, дату и время, если они указаны в тексте. "
    "Значения полей service_name, preferred_date, preferred_time пиши на русском, как в тексте."
)


class AIProviderError(Exception):
    pass


class AIProvider(ABC):
    @abstractmethod
    def analyze(self, text: str) -> str:
        raise NotImplementedError


class MockProvider(AIProvider):
    INTENT_KEYWORDS = (
        (Intent.CANCEL_BOOKING, ("отмен", "cancel")),
        (Intent.RESCHEDULE, ("перенес", "перенос", "reschedul", "другое время")),
        (
            Intent.PRICE_REQUEST,
            ("сколько стоит", "стоимость", "цен", "прайс", "стоит", "сколько", "тариф", "price", "cost"),
        ),
        (
            Intent.COMPLAINT,
            ("жалоб", "претенз", "недоволь", "ужас", "отврат", "возмут", "разочаров", "complaint", "terrible", "awful"),
        ),
        (Intent.BOOKING, ("запис", "запиш", "заброн", "бронь", "book", "хочу на", "прий", "можно на")),
        (
            Intent.QUESTION,
            ("вопрос", "подскаж", "можно ли", "график", "работаете", "когда", "часы работы", "информаци", "?", "question", "hours"),
        ),
    )

    SERVICE_KEYWORDS = (
        ("стрижк", "Стрижка"),
        ("haircut", "Стрижка"),
        ("окраш", "Окрашивание"),
        ("покрас", "Окрашивание"),
        ("мелиров", "Окрашивание"),
        ("маникюр", "Маникюр"),
        ("manicure", "Маникюр"),
        ("педикюр", "Педикюр"),
        ("массаж", "Массаж"),
        ("massage", "Массаж"),
        ("консультац", "Консультация"),
        ("consult", "Консультация"),
        ("чистк", "Чистка лица"),
        ("укладк", "Укладка"),
        ("бров", "Коррекция бровей"),
        ("brow", "Коррекция бровей"),
    )

    DATE_RE = re.compile(
        r"сегодня|завтра|послезавтра|понедельник|вторник|сред[уыею]|четверг|пятниц[уыею]"
        r"|суббот[уыею]|воскресенье|выходные|\d{1,2}\.\d{1,2}(?:\.\d{2,4})?|следующ\w*\s+недел\w*",
        re.IGNORECASE,
    )
    TIME_RE = re.compile(r"\d{1,2}[:.]\d{2}|\b(?:в|к)\s+\d{1,2}\s+час\w*", re.IGNORECASE)

    BASE_CONFIDENCE = {
        Intent.CANCEL_BOOKING: 0.9,
        Intent.RESCHEDULE: 0.9,
        Intent.PRICE_REQUEST: 0.85,
        Intent.COMPLAINT: 0.8,
        Intent.BOOKING: 0.75,
        Intent.QUESTION: 0.7,
        Intent.OTHER: 0.3,
    }

    def analyze(self, text: str) -> str:
        lowered = text.lower()
        intent = Intent.OTHER
        for candidate, keywords in self.INTENT_KEYWORDS:
            if any(keyword in lowered for keyword in keywords):
                intent = candidate
                break
        service_name = next(
            (name for keyword, name in self.SERVICE_KEYWORDS if keyword in lowered), None
        )
        date_match = self.DATE_RE.search(text)
        time_match = self.TIME_RE.search(text)
        confidence = self.BASE_CONFIDENCE[intent]
        if intent == Intent.BOOKING and (date_match or time_match):
            confidence = 0.95
        result = AIResult(
            intent=intent,
            confidence=confidence,
            service_name=service_name,
            preferred_date=date_match.group(0) if date_match else None,
            preferred_time=time_match.group(0) if time_match else None,
        )
        return result.model_dump_json()


class OpenAIProvider(AIProvider):
    BASE_URL = "https://api.openai.com/v1"
    MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def analyze(self, text: str) -> str:
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.0,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                response = httpx.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
                last_error = exc
                logger.warning("AI provider attempt %s failed: %s", attempt, exc)
                if attempt == 1:
                    time.sleep(0.5)
        raise AIProviderError(f"AI provider failed after retry: {last_error}") from last_error


class QwenProvider(OpenAIProvider):
    BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    MODEL = "qwen-plus"


class AIAnalysisService:
    def __init__(self, provider: AIProvider):
        self._provider = provider

    def analyze(self, text: str) -> AIResult:
        raw = self._provider.analyze(text)
        cleaned = self._strip_code_fences(raw)
        try:
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                raise ValueError("not a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Invalid AI JSON response: %r", exc)
            return self._fallback()
        try:
            intent = Intent(data.get("intent", "other"))
        except ValueError:
            intent = Intent.OTHER
        try:
            return AIResult(
                intent=intent,
                confidence=data.get("confidence", 0.0),
                service_name=data.get("service_name"),
                preferred_date=data.get("preferred_date"),
                preferred_time=data.get("preferred_time"),
                requires_manual_review=bool(data.get("requires_manual_review", False)),
            )
        except ValidationError:
            return self._fallback()

    def analyze_safe(self, text: str) -> AIResult:
        try:
            return self.analyze(text)
        except AIProviderError:
            return self._fallback()

    def _fallback(self) -> AIResult:
        return AIResult(intent=Intent.OTHER, confidence=0.0, requires_manual_review=True)

    @staticmethod
    def _strip_code_fences(raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return text


def build_provider(settings: Settings) -> AIProvider:
    name = settings.provider_name
    if name == "openai":
        return OpenAIProvider(api_key=settings.AI_API_KEY)
    if name == "qwen":
        return QwenProvider(api_key=settings.AI_API_KEY)
    return MockProvider()
