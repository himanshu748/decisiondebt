import hmac
from fastapi import Header
from backend.app.settings import settings
from backend.app.graph.client import DomainError


def require_admin(authorization: str | None = Header(default=None)):
    if settings.mode == "public-readonly":
        raise DomainError("FORBIDDEN", "Public demo is read-only", 403)
    supplied = (
        authorization.removeprefix("Bearer ")
        if authorization and authorization.startswith("Bearer ")
        else ""
    )
    if not settings.admin_token or not hmac.compare_digest(
        supplied, settings.admin_token
    ):
        raise DomainError("FORBIDDEN", "A valid local admin token is required", 403)
    return "local-admin"
