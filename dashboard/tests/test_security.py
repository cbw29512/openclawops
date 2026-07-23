import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials
from starlette.requests import Request

from app.security import require_authentication, require_same_origin


def _request(method: str, origin: str | None = None) -> Request:
    headers = []
    if origin is not None:
        headers.append((b"origin", origin.encode("utf-8")))
    return Request(
        {
            "type": "http",
            "method": method,
            "scheme": "http",
            "server": ("127.0.0.1", 8788),
            "path": "/vote",
            "headers": headers,
        }
    )


def test_authentication_fails_closed_without_configuration(monkeypatch) -> None:
    monkeypatch.delenv("NOVA_DASHBOARD_USERNAME", raising=False)
    monkeypatch.delenv("NOVA_DASHBOARD_PASSWORD", raising=False)

    with pytest.raises(HTTPException) as error:
        require_authentication(None)

    assert error.value.status_code == 503


def test_authentication_rejects_wrong_password(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_DASHBOARD_USERNAME", "operator")
    monkeypatch.setenv("NOVA_DASHBOARD_PASSWORD", "correct-password")
    credentials = HTTPBasicCredentials(
        username="operator",
        password="wrong-password",
    )

    with pytest.raises(HTTPException) as error:
        require_authentication(credentials)

    assert error.value.status_code == 401


def test_authentication_accepts_exact_credentials(monkeypatch) -> None:
    monkeypatch.setenv("NOVA_DASHBOARD_USERNAME", "operator")
    monkeypatch.setenv("NOVA_DASHBOARD_PASSWORD", "correct-password")
    credentials = HTTPBasicCredentials(
        username="operator",
        password="correct-password",
    )

    assert require_authentication(credentials) == "operator"


def test_cross_origin_post_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv(
        "NOVA_DASHBOARD_ALLOWED_ORIGINS",
        "http://127.0.0.1:8788",
    )

    with pytest.raises(HTTPException) as error:
        require_same_origin(_request("POST", "https://attacker.example"))

    assert error.value.status_code == 403


def test_same_origin_post_is_accepted(monkeypatch) -> None:
    monkeypatch.setenv(
        "NOVA_DASHBOARD_ALLOWED_ORIGINS",
        "http://127.0.0.1:8788",
    )

    assert require_same_origin(
        _request("POST", "http://127.0.0.1:8788")
    ) is None
