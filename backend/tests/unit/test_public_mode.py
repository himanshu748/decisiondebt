import json
import os
import subprocess
import sys

from backend.app.rate_limit import PublicRateLimiter


def test_per_client_budget_refills_and_does_not_trust_an_unbounded_map():
    limiter = PublicRateLimiter(per_minute=60, burst=2, global_burst=5000)
    assert limiter.allow("one", now=0)
    assert limiter.allow("one", now=0)
    assert not limiter.allow("one", now=0)
    assert limiter.allow("two", now=0)
    assert limiter.allow("one", now=1)
    for index in range(3000):
        limiter.allow(str(index), now=1)
    assert len(limiter.clients) == 2048


def test_global_budget_cannot_be_bypassed_with_new_client_addresses():
    limiter = PublicRateLimiter(global_per_minute=60, global_burst=2)
    assert limiter.allow("one", now=0)
    assert limiter.allow("two", now=0)
    assert not limiter.allow("three", now=0)
    assert limiter.allow("three", now=1)


def test_public_process_discards_provider_and_admin_credentials():
    environment = {
        **os.environ,
        "DD_MODE": "public-readonly",
        "ADMIN_TOKEN": "test-admin",
        "DD_LLM_API_KEY": "test-provider",
        "DD_AGENT_MODE": "llm",
    }
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "import json; from backend.app.settings import settings; print(json.dumps([settings.api_key, settings.admin_token, settings.agent_mode]))",
        ],
        env=environment,
        text=True,
    )
    assert json.loads(output) == ["", "", "disabled"]
