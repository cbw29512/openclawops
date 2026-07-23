"""Authentication, trusted-host, and same-origin controls for Nova Dashboard."""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic_auth = HTTPBasic(auto_error=False)


def _csv_environment(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def allowed_hosts() -> list[str]:
    return _csv_environment(
        "NOVA_DASHBOARD_ALLOWED_HOSTS",
        "localhost,127.0.0.1,[::1]",
    )


def allowed_origins() -> set[str]:
    return set(
        _csv_environment(
            "NOVA_DASHBOARD_ALLOWED_ORIGINS",
            "http://127.0.0.1:8788,http://localhost:8788",
        )
    )


def require_authentication(
    credentials: Optional[HTTPBasicCredentials] = Depends(basic_auth),
) -> str:
    """Fail closed unless deployment-only credentials are configured."""
    expected_username = os.getenv("NOVA_DASHBOARD_USERNAME")
    expected_password = os.getenv("NOVA_DASHBOARD_PASSWORD")
    if not expected_username or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard authentication is not configured.",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Basic realm=nova-dashboard"},
        )

    username_valid = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        expected_username.encode("utf-8"),
    )
    password_valid = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        expected_password.encode("utf-8"),
    )
    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Basic realm=nova-dashboard"},
        )
    return credentials.username


def require_same_origin(request: Request) -> None:
    """Reject cross-origin state-changing requests to local operator actions."""
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    origin = request.headers.get("origin")
    if not origin or origin.rstrip("/") not in allowed_origins():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-origin request rejected.",
        )
