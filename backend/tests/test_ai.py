import httpx
import pytest

from app.models.enums import Intent
from app.schemas.ai_result import AIResult
from app.services.ai import (
    AIAnalysisService,
    AIProviderError,
    MockProvider,
    OpenAIProvider,
    QwenProvider,
)


def analyze_text(text: str) -> AIResult:
    return AIAnalysisService(MockProvider()).analyze(text)


def test_mock_booking_with_details():
    result = analyze_text("Хочу записаться на стрижку завтра в 15:00")
    assert result.intent == Intent.BOOKING
    assert result.confidence == 0.95
    assert result.service_name == "Стрижка"
    assert result.preferred_date == "завтра"
    assert result.preferred_time == "15:00"


def test_mock_cancel_booking():
    assert analyze_text("Отмените мою запись").intent == Intent.CANCEL_BOOKING


def test_mock_reschedule():
    assert analyze_text("Перенесите запись на другой день").intent == Intent.RESCHEDULE


def test_mock_price_request():
    result = analyze_text("Сколько стоит массаж?")
    assert result.intent == Intent.PRICE_REQUEST
    assert result.service_name == "Массаж"


def test_mock_complaint():
    assert analyze_text("Ужасный сервис, хочу написать жалобу").intent == Intent.COMPLAINT


def test_mock_question():
    assert analyze_text("Вы работаете в воскресенье?").intent == Intent.QUESTION


def test_mock_other_for_plain_greeting():
    result = analyze_text("Добрый день!")
    assert result.intent == Intent.OTHER
    assert result.confidence < 0.60


def test_mock_english_keywords():
    assert analyze_text("I want to book a haircut tomorrow").intent == Intent.BOOKING
    assert analyze_text("cancel my booking please").intent == Intent.CANCEL_BOOKING


class StubProvider:
    def __init__(self, raw: str):
        self.raw = raw

    def analyze(self, text: str) -> str:
        return self.raw


class FailingProvider:
    def analyze(self, text: str) -> str:
        raise AIProviderError("provider unavailable")


def test_invalid_json_fallback():
    result = AIAnalysisService(StubProvider("совсем не json")).analyze("текст")
    assert result.intent == Intent.OTHER
    assert result.confidence == 0.0
    assert result.requires_manual_review is True


def test_json_with_markdown_fences():
    raw = '```json\n{"intent": "booking", "confidence": 0.9}\n```'
    result = AIAnalysisService(StubProvider(raw)).analyze("текст")
    assert result.intent == Intent.BOOKING
    assert result.confidence == 0.9


def test_json_array_fallback():
    result = AIAnalysisService(StubProvider("[1, 2, 3]")).analyze("текст")
    assert result.intent == Intent.OTHER
    assert result.requires_manual_review is True


def test_unknown_intent_mapped_to_other():
    raw = '{"intent": "brand_new_intent", "confidence": 0.9}'
    result = AIAnalysisService(StubProvider(raw)).analyze("текст")
    assert result.intent == Intent.OTHER
    assert result.confidence == 0.9


def test_confidence_out_of_range_fallback():
    raw = '{"intent": "booking", "confidence": 5}'
    result = AIAnalysisService(StubProvider(raw)).analyze("текст")
    assert result.intent == Intent.OTHER
    assert result.confidence == 0.0
    assert result.requires_manual_review is True


def test_provider_error_fallback():
    result = AIAnalysisService(FailingProvider()).analyze_safe("текст")
    assert result.intent == Intent.OTHER
    assert result.confidence == 0.0
    assert result.requires_manual_review is True


class FakeResponse:
    def __init__(self, content: str):
        self._content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_openai_provider_retries_once(monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        if len(calls) == 1:
            raise httpx.ConnectError("connection failed")
        return FakeResponse('{"intent": "question", "confidence": 0.7}')

    monkeypatch.setattr("app.services.ai.httpx.post", fake_post)
    provider = OpenAIProvider(api_key="test-key")
    result = AIAnalysisService(provider).analyze("текст")
    assert len(calls) == 2
    assert result.intent == Intent.QUESTION
    assert result.confidence == 0.7


def test_openai_provider_fails_after_retry(monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr("app.services.ai.httpx.post", fake_post)
    provider = OpenAIProvider(api_key="test-key")
    with pytest.raises(AIProviderError):
        provider.analyze("текст")
    assert len(calls) == 2


def test_qwen_provider_uses_dashscope():
    provider = QwenProvider(api_key="key")
    assert provider.BASE_URL == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    assert provider.MODEL == "qwen-plus"
