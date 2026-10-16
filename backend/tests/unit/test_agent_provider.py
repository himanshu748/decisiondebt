import httpx
import pytest
import asyncio
import time
from backend.app.agent.provider import completion
from backend.app.graph.client import DomainError
from backend.app.settings import settings


@pytest.mark.parametrize("free", [True, False])
def test_provider_payload_caps_free_openrouter_without_changing_groq(monkeypatch, free):
    monkeypatch.setattr(settings, "agent_mode", "llm")
    monkeypatch.setattr(settings, "api_key", "test-only-key")
    monkeypatch.setattr(
        settings,
        "base_url",
        "https://openrouter.ai/api/v1" if free else "https://api.groq.com/openai/v1",
    )
    monkeypatch.setattr(
        settings,
        "model",
        "nvidia/nemotron-3-super-120b-a12b:free" if free else "openai/gpt-oss-120b",
    )
    captured = {}

    async def fake_post(self, url, **kwargs):
        captured.update(kwargs["json"])
        return httpx.Response(
            200,
            json={
                "id": "test-response-id",
                "model": settings.model,
                "provider": "test-provider",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Summary",
                            "reasoning": "excluded",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 12},
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    message, usage = completion([], [], timeout=2)
    assert captured["max_tokens"] == 2000
    if free:
        assert captured["provider"] == {
            "allow_fallbacks": False,
            "max_price": {"prompt": 0, "completion": 0},
        }
        assert captured["reasoning"] == {"enabled": False, "exclude": True}
    else:
        assert "provider" not in captured and "reasoning" not in captured
    assert "reasoning" not in message
    assert usage["provider_response_id"] == "test-response-id"


def test_provider_deadline_cancels_a_slow_response(monkeypatch):
    monkeypatch.setattr(settings, "agent_mode", "llm")
    monkeypatch.setattr(settings, "api_key", "test-only-key")

    async def delayed(self, url, **kwargs):
        await asyncio.sleep(1)

    monkeypatch.setattr(httpx.AsyncClient, "post", delayed)
    start = time.monotonic()
    with pytest.raises(DomainError) as error:
        completion([], [], timeout=0.02)
    assert error.value.code == "AGENT_PROVIDER_UNAVAILABLE"
    assert time.monotonic() - start < 0.5
