import pytest

from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import select
from tests.conftest import TestingSessionLocal

from src.entity.models import User
from src.services.auth import auth_service
from tests.conftest import TestingSessionLocal, test_user
from src.conf import messages

user_data = {"username": "Boogerman", "email": "boogerman@example.com", "password": "12345678"}


def test_signup(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

        mock_send_email = Mock()
        monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
        response = client.post("api/auth/signup", json=user_data)
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "password" not in data
        assert "avatar" in data
        assert mock_send_email.called


def test_repeat_signup(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

        mock_send_email = Mock()
        monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

        class MockFastAPIError(Exception):
            status_code = 409

        monkeypatch.setattr("fastapi.exceptions.FastAPIError", MockFastAPIError)
        response = client.post("api/auth/signup", json=user_data)
        assert response.status_code == 409, response.text
        data = response.data.decode()
        assert data["detail"] == messages.ACCOUNT_EXIST


def test_not_confirmed_login(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

        response = client.post("api/auth/login", data={"username": user_data.get("username"),
                                                       "password": user_data.get("password")})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["detail"] == messages.NOT_CONFIRM


@pytest.mark.asyncio
async def test_login(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        async with TestingSessionLocal() as session:
            current_user = await session.execute(
                select(User).where(User.email == user_data.get("email"))
            )
            current_user = current_user.scalar_one_or_none()
            if current_user:
                current_user.confirmed = True
                await session.commit()

        response = client.post(
            "api/auth/login",
            data={
                "username": user_data.get("email"),
                "password": user_data.get("password"),
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data


def test_wrong_password_login(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        response = client.post("api/auth/login",
                               data={"username": user_data.get("email"), "password": "password"})
        assert response.status_code == 401, response.text
        data = response.json()
        assert data["detail"] == messages.INVALID_CREDENTIALS


def test_wrong_email_login(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        response = client.post("api/auth/login",
                               data={"username": "test@email.com", "password": user_data.get("password")})
        assert response.status_code == 401, response.text
        data = response.json()
        assert "detail" in data


def test_validation_error_login(client, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
        monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())
        response = client.post("api/auth/login",
                               data={"password": user_data.get("password")})
        assert response.status_code == 422, response.text
        data = response.json()
        assert "detail" in data
