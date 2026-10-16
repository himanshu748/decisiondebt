import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Settings:
    host = os.getenv("DD_GRAPH_HOST", "127.0.0.1")
    port = int(os.getenv("DD_GRAPH_PORT", "16380"))
    graph_name = os.getenv("DD_GRAPH_NAME", "decisiondebt")
    mode = os.getenv("DD_MODE", "local-admin")
    admin_token = os.getenv("ADMIN_TOKEN", "")
    agent_mode = os.getenv("DD_AGENT_MODE", "deterministic")
    base_url = os.getenv("DD_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = os.getenv("DD_LLM_MODEL", "openai/gpt-oss-120b")
    api_key = os.getenv("DD_LLM_API_KEY", "")
    if mode == "public-readonly":
        # Public deployments never retain an admin credential or provider key,
        # even if the process environment is accidentally over-configured.
        admin_token = ""
        api_key = ""
        agent_mode = "disabled"


settings = Settings()
