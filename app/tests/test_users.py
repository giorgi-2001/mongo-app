import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.users import model, router, service, utils


def test_password_hash_verifies_only_original_password():
    hashed = utils.hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert utils.verify_password("correct horse battery staple", hashed)
    assert not utils.verify_password("different password", hashed)


def test_user_base_validates_email_and_defaults_skills():
    user = model.UserBase(email="person@example.com", password="secret", age=30, role="member")
    another_user = model.UserBase(email="other@example.com", password="secret", age=20, role="member")

    assert user.skills == []
    assert another_user.skills == []
    assert user.skills is not another_user.skills

    with pytest.raises(ValidationError):
        model.UserBase(email="not-an-email", password="secret", age=30, role="member")


def test_user_response_contains_public_profile_fields():
    user = model.UserResponse(
        email="person@example.com",
        age=30,
        skills=["python"],
        role="member",
        isActive=True,
    )

    assert user.model_dump() == {
        "email": "person@example.com",
        "age": 30,
        "skills": ["python"],
        "role": "member",
        "isActive": True,
    }


def test_create_user_hashes_password_and_inserts_document(monkeypatch):
    created = {}

    class FakeUser:
        def __init__(self, **data):
            self.data = data
            created["user"] = self

        async def insert(self):
            created["inserted"] = True

    monkeypatch.setattr(service, "hash_password", lambda password: f"hashed:{password}")
    monkeypatch.setattr(service, "User", FakeUser)

    result = asyncio.run(service.create_user({"email": "person@example.com", "password": "secret", "role": "member"}))

    assert result is created["user"]
    assert result.data["password"] == "hashed:secret"
    assert created["inserted"] is True


def test_get_user_by_email_queries_user_document(monkeypatch):
    expected_user = object()
    captured = {}

    class FakeEmailField:
        def __eq__(self, value):
            return ("email", value)

    class FakeUser:
        email = FakeEmailField()

        @classmethod
        async def find_one(cls, expression):
            captured["expression"] = expression
            return expected_user

    monkeypatch.setattr(service, "User", FakeUser)

    result = asyncio.run(service.get_user_by_email("person@example.com"))

    assert result is expected_user
    assert captured["expression"] == ("email", "person@example.com")


def test_list_users_returns_all_documents(monkeypatch):
    expected_users = [object(), object()]

    class FakeQuery:
        async def to_list(self):
            return expected_users

    class FakeUser:
        @classmethod
        def find_all(cls):
            return FakeQuery()

    monkeypatch.setattr(service, "User", FakeUser)

    assert asyncio.run(service.list_users()) == expected_users


def test_register_user_creates_new_user(monkeypatch):
    user = model.UserBase(email="person@example.com", password="secret", age=30, role="member")
    lookup = AsyncMock(return_value=None)
    create = AsyncMock()
    monkeypatch.setattr(router.service, "get_user_by_email", lookup)
    monkeypatch.setattr(router.service, "create_user", create)

    result = asyncio.run(router.register_user(user))

    assert result == {"message": "User registered successfully."}
    lookup.assert_awaited_once_with(user.email)
    create.assert_awaited_once_with(user.model_dump())


def test_register_user_rejects_duplicate_email(monkeypatch):
    user = model.UserBase(email="person@example.com", password="secret", age=30, role="member")
    monkeypatch.setattr(router.service, "get_user_by_email", AsyncMock(return_value=object()))
    create = AsyncMock()
    monkeypatch.setattr(router.service, "create_user", create)

    with pytest.raises(HTTPException) as error:
        asyncio.run(router.register_user(user))

    assert error.value.status_code == 409
    assert error.value.detail == "User with this email already exists."
    create.assert_not_awaited()


def test_list_users_returns_service_results(monkeypatch):
    users = [object(), object()]
    lookup = AsyncMock(return_value=users)
    monkeypatch.setattr(router.service, "list_users", lookup)

    assert asyncio.run(router.list_users()) == users
    lookup.assert_awaited_once_with()


def test_get_current_user_info_returns_authenticated_user():
    user = SimpleNamespace(email="person@example.com")

    assert asyncio.run(router.get_current_user_info(user)) is user
