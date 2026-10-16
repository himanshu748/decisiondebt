import asyncio
import httpx
from backend.app.settings import settings
from backend.app.graph.client import DomainError


def completion(messages, tools, timeout=30):
    if settings.agent_mode != "llm" or not settings.api_key:
        raise DomainError(
            "AGENT_PROVIDER_UNAVAILABLE",
            "Set DD_AGENT_MODE=llm and supply DD_LLM_API_KEY for a genuine LLM run.",
            503,
        )
    try:
        payload = {
            "model": settings.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "max_tokens": 2000,
            "temperature": 0.2,
        }
        if settings.base_url.rstrip(
            "/"
        ) == "https://openrouter.ai/api/v1" and settings.model.endswith(":free"):
            payload["provider"] = {
                "allow_fallbacks": False,
                "max_price": {"prompt": 0, "completion": 0},
            }
            payload["reasoning"] = {"enabled": False, "exclude": True}
            payload["parallel_tool_calls"] = True

        async def request():
            async with httpx.AsyncClient() as client:
                return await asyncio.wait_for(
                    client.post(
                        settings.base_url.rstrip("/") + "/chat/completions",
                        headers={"Authorization": "Bearer " + settings.api_key},
                        json=payload,
                        timeout=None,
                    ),
                    timeout=min(30, timeout),
                )

        r = asyncio.run(request())
        if r.status_code == 429:
            raise DomainError(
                "RATE_LIMITED", "Provider rate limit reached; this run stopped.", 429
            )
        if r.status_code >= 400:
            raise DomainError(
                "AGENT_PROVIDER_UNAVAILABLE",
                f"Provider returned HTTP {r.status_code}.",
                503,
            )
        data = r.json()
        choice = data["choices"][0]
        message = {
            k: v
            for k, v in choice["message"].items()
            if k in ("role", "content", "tool_calls")
        }
        usage = {
            **data.get("usage", {}),
            "provider_response_id": data.get("id"),
            "provider_model": data.get("model"),
            "upstream_provider": data.get("provider"),
            "finish_reason": choice.get("finish_reason"),
            "provider_request_id": r.headers.get("x-request-id"),
        }
        return message, usage
    except (httpx.HTTPError, KeyError, ValueError, TimeoutError) as e:
        raise DomainError(
            "AGENT_PROVIDER_UNAVAILABLE",
            "Provider request failed. No LLM result was fabricated.",
            503,
        ) from e
