import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from src.auth import auth, router, utils


def test_access_and_refresh_tokens_round_trip():
    payload = {"sub": "person@example.com"}

    access_token = utils.create_access_token(payload)
    refresh_token = utils.create_refresh_token(payload)

    assert utils.decode_access_token(access_token)["sub"] == payload["sub"]
    assert utils.decode_refresh_token(refresh_token)["sub"] == payload["sub"]


def test_token_decoder_rejects_invalid_and_expired_tokens():
    with pytest.raises(ValueError, match="Invalid token"):
        utils.decode_access_token("not-a-jwt")

    expired_token = utils.create_token(
        {"sub": "person@example.com"},
        utils.ACCESS_TOKEN_SECRET_KEY,
        utils.ALGORITHM,
        timedelta(seconds=-1),
    )
    with pytest.raises(ValueError, match="Token has expired"):
        utils.decode_access_token(expired_token)


def test_access_and_refresh_tokens_use_different_secrets():
    refresh_token = utils.create_refresh_token({"sub": "person@example.com"})

    with pytest.raises(ValueError, match="Invalid token"):
        utils.decode_access_token(refresh_token)


def test_authenticate_user_returns_user_when_password_matches(monkeypatch):
    user = SimpleNamespace(password="stored-hash")
    lookup = AsyncMock(return_value=user)
    monkeypatch.setattr(auth.user_service, "get_user_by_email", lookup)
    monkeypatch.setattr(
        auth,
        "verify_password",
        lambda password, hashed: password == "secret" and hashed == user.password,
    )

    result = asyncio.run(auth.authenticate_user("person@example.com", "secret"))

    assert result is user
    lookup.assert_awaited_once_with("person@example.com")


@pytest.mark.parametrize("found_user,password_matches", [(None, True), (SimpleNamespace(password="hash"), False)])
def test_authenticate_user_rejects_unknown_user_or_wrong_password(monkeypatch, found_user, password_matches):
    monkeypatch.setattr(auth.user_service, "get_user_by_email", AsyncMock(return_value=found_user))
    monkeypatch.setattr(auth, "verify_password", lambda *_: password_matches)

    with pytest.raises(HTTPException) as error:
        asyncio.run(auth.authenticate_user("person@example.com", "wrong"))

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_get_current_user_resolves_token_subject(monkeypatch):
    user = SimpleNamespace(email="person@example.com")
    monkeypatch.setattr(auth, "decode_access_token", lambda _: {"sub": user.email})
    lookup = AsyncMock(return_value=user)
    monkeypatch.setattr(auth.user_service, "get_user_by_email", lookup)

    assert asyncio.run(auth.get_current_user("token")) is user
    lookup.assert_awaited_once_with(user.email)


@pytest.mark.parametrize("payload", [{}, {"sub": None}])
def test_get_current_user_rejects_token_without_subject(monkeypatch, payload):
    monkeypatch.setattr(auth, "decode_access_token", lambda _: payload)

    with pytest.raises(HTTPException) as error:
        asyncio.run(auth.get_current_user("token"))

    assert error.value.status_code == 401


def test_get_current_user_logs_and_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(auth, "decode_access_token", lambda _: (_ for _ in ()).throw(ValueError("bad token")))
    monkeypatch.setattr(auth.logger, "error", lambda *_: None)

    with pytest.raises(HTTPException) as error:
        asyncio.run(auth.get_current_user("token"))

    assert error.value.status_code == 401


def test_get_current_user_rejects_missing_database_user(monkeypatch):
    monkeypatch.setattr(auth, "decode_access_token", lambda _: {"sub": "missing@example.com"})
    monkeypatch.setattr(auth.user_service, "get_user_by_email", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as error:
        asyncio.run(auth.get_current_user("token"))

    assert error.value.status_code == 401


def test_get_current_active_user_rejects_inactive_user(monkeypatch):
    monkeypatch.setattr(auth, "get_current_user", AsyncMock(return_value=SimpleNamespace(isActive=False)))

    with pytest.raises(HTTPException) as error:
        asyncio.run(auth.get_current_active_user("token"))

    assert error.value.status_code == 400
    assert error.value.detail == "Inactive user"


def test_get_current_active_user_returns_active_user(monkeypatch):
    user = SimpleNamespace(isActive=True)
    monkeypatch.setattr(auth, "get_current_user", AsyncMock(return_value=user))

    assert asyncio.run(auth.get_current_active_user("token")) is user


def test_login_returns_access_token_and_sets_http_only_refresh_cookie(monkeypatch):
    user = SimpleNamespace(email="person@example.com")
    monkeypatch.setattr(router, "authenticate_user", AsyncMock(return_value=user))
    monkeypatch.setattr(router, "create_access_token", lambda data: f"access:{data['sub']}")
    monkeypatch.setattr(router, "create_refresh_token", lambda data: f"refresh:{data['sub']}")
    response = Response()

    form = router.OAuth2PasswordRequestForm(username=user.email, password="secret")
    result = asyncio.run(router.login(form, response))

    assert result.access_token == f"access:{user.email}"
    assert result.token_type == "bearer"
    cookie = response.headers["set-cookie"]
    assert f'refresh_token="refresh:{user.email}"' in cookie
    assert "httponly" in cookie.lower()
    assert "samesite=strict" in cookie.lower()


def make_request(cookie=None):
    headers = [] if cookie is None else [(b"cookie", f"refresh_token={cookie}".encode())]
    return Request({
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/auth/refresh",
        "raw_path": b"/api/v1/auth/refresh",
        "query_string": b"",
        "headers": headers,
        "server": ("test", 80),
        "client": ("test", 123),
    })


def test_refresh_requires_cookie():
    with pytest.raises(HTTPException) as error:
        asyncio.run(router.refresh_token(make_request()))

    assert error.value.status_code == 401
    assert error.value.detail == "Refresh token not found in cookies."


@pytest.mark.parametrize("decode_error,payload", [(True, None), (False, {})])
def test_refresh_rejects_invalid_or_subjectless_token(monkeypatch, decode_error, payload):
    if decode_error:
        monkeypatch.setattr(router, "decode_refresh_token", lambda _: (_ for _ in ()).throw(ValueError("bad token")))
    else:
        monkeypatch.setattr(router, "decode_refresh_token", lambda _: payload)

    with pytest.raises(HTTPException) as error:
        asyncio.run(router.refresh_token(make_request("bad")))

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid refresh token."


def test_refresh_issues_new_access_token(monkeypatch):
    monkeypatch.setattr(router, "decode_refresh_token", lambda _: {"sub": "person@example.com"})
    monkeypatch.setattr(router, "create_access_token", lambda data: f"access:{data['sub']}")

    result = asyncio.run(router.refresh_token(make_request("valid")))

    assert result.access_token == "access:person@example.com"
    assert result.token_type == "bearer"


def test_logout_deletes_refresh_cookie():
    response = Response()

    result = asyncio.run(router.logout(response))

    assert result == {"message": "Logged out successfully."}
    cookie = response.headers["set-cookie"]
    assert 'refresh_token=""' in cookie
    assert "max-age=0" in cookie.lower()
