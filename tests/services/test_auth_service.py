"""
Professional tests for authentication service.

Tests cover:
- User registration (success, duplicates, validation)
- User authentication (valid/invalid credentials, banned users)
- Password reset flow (token generation, expiration, validation)
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.models.enums import Departments, UserRole
from app.models.user import User
from app.schemas.auth.auth import RegisterRequest
from app.services.auth.service import AuthService


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        repository_factory,
    ):
        # Arrange
        payload = RegisterRequest(
            username="testuser",
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            password="securepassword",
        )
        user_repo = repository_factory(
            get_by_unique_fields=AsyncMock(return_value=None),
            create_user=AsyncMock(
                return_value=User(
                    id=1,
                    **payload.model_dump(exclude={"password"}),
                    hashed_password="hashedpassword",
                )
            ),
        )
        auth_service = AuthService(user_repo=user_repo)
        # Act
        result = await auth_service.register_user(payload)
        # Assert
        assert result.id == 1
        assert result.username == payload.username
        assert result.email == payload.email

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(
        self,
        repository_factory,
    ):
        # Arrange
        payload = RegisterRequest(
            username="testuser",
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            password="securepassword",
        )
        user_repo = repository_factory(
            get_by_unique_fields=AsyncMock(
                return_value=User(
                    id=1,
                    **payload.model_dump(exclude={"password"}),
                    hashed_password="hashedpassword",
                )
            ),
            create_user=AsyncMock(return_value=None),
        )
        auth_service = AuthService(user_repo=user_repo)
        # Act & Assert
        with pytest.raises(ConflictException):
            await auth_service.register_user(payload)

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self,
        repository_factory,
    ):
        # Arrange
        payload = RegisterRequest(
            username="testuser",
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            password="securepassword",
        )
        user_repo = repository_factory(
            get_by_unique_fields=AsyncMock(
                return_value=User(
                    id=1,
                    **payload.model_dump(exclude={"password"}),
                    hashed_password="hashedpassword",
                )
            ),
            create_user=AsyncMock(return_value=None),
        )
        auth_service = AuthService(user_repo=user_repo)
        # Act & Assert
        with pytest.raises(ConflictException):
            await auth_service.register_user(payload)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self,
        repository_factory,
    ):
        # Arrange
        username = "testuser"
        password = "securepassword"
        hashed_password = "hashedpassword"
        user = User(
            id=1,
            username=username,
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_banned=False,
        )
        user_repo = repository_factory(get_by_username=AsyncMock(return_value=user))
        auth_service = AuthService(
            user_repo=user_repo,
            password_verifier=MagicMock(return_value=True),
            token_creator=MagicMock(return_value="testtoken"),
        )
        # Act
        result_user, token = await auth_service.authenticate_user(username, password)
        # Assert
        assert result_user.id == user.id
        assert token == "testtoken"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(
        self,
        repository_factory,
    ):
        # Arrange
        username = "testuser"
        password = "wrongpassword"
        hashed_password = "hashedpassword"
        user = User(
            id=1,
            username=username,
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_banned=False,
        )
        user_repo = repository_factory(get_by_username=AsyncMock(return_value=user))
        auth_service = AuthService(
            user_repo=user_repo, password_verifier=MagicMock(return_value=False)
        )
        # Act & Assert
        with pytest.raises(UnauthorizedException) as exc_info:
            await auth_service.authenticate_user(username, password)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_blocked_user(
        self,
        repository_factory,
    ):
        username = "testuser"
        password = "securepassword"
        user = User(
            id=1,
            username=username,
            full_name="Test User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="testuser@example.com",
            hashed_password="hashedpassword",
            is_active=True,
            is_banned=True,
        )
        user_repo = repository_factory(get_by_username=AsyncMock(return_value=user))
        auth_service = AuthService(
            user_repo=user_repo,
            password_verifier=MagicMock(return_value=True),
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await auth_service.authenticate_user(username, password)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_password_reset_token_user_not_found(self, repository_factory):
        user_repo = repository_factory(
            get_by_username=AsyncMock(return_value=None),
            create_reset_token=AsyncMock(),
        )
        auth_service = AuthService(user_repo=user_repo)

        await auth_service.create_password_reset_token("ghostuser")

        user_repo.create_reset_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_password_reset_token_username_success(self, repository_factory):
        user = User(
            id=2,
            username="resetuser",
            full_name="Reset User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="resetuser@example.com",
            hashed_password="hashedpassword",
            is_active=True,
            is_banned=False,
        )
        user_repo = repository_factory(
            get_by_username=AsyncMock(return_value=user),
            create_reset_token=AsyncMock(),
        )
        auth_service = AuthService(
            user_repo=user_repo,
            reset_token_creator=MagicMock(return_value="raw-reset-token"),
            token_hasher=MagicMock(return_value="hashed-reset-token"),
        )

        before_call = datetime.now(UTC)
        await auth_service.create_password_reset_token("resetuser")

        user_repo.create_reset_token.assert_awaited_once()
        call_kwargs = user_repo.create_reset_token.await_args.kwargs
        assert call_kwargs["user_id"] == user.id
        assert call_kwargs["token_hash"] == "hashed-reset-token"
        expires_at = call_kwargs["expires_at"]
        assert expires_at > before_call
        assert expires_at <= before_call + timedelta(
            minutes=settings.RESET_TOKEN_EXPIRE_MINUTES + 1
        )

    @pytest.mark.asyncio
    async def test_create_password_reset_token_email_path(self, repository_factory):
        user = User(
            id=3,
            username="emailuser",
            full_name="Email User",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="emailuser@example.com",
            hashed_password="hashedpassword",
            is_active=True,
            is_banned=False,
        )
        user_repo = repository_factory(
            get_by_email=AsyncMock(return_value=user),
            create_reset_token=AsyncMock(),
        )
        auth_service = AuthService(user_repo=user_repo)

        await auth_service.create_password_reset_token("emailuser@example.com")

        user_repo.get_by_email.assert_awaited_once_with("emailuser@example.com")
        user_repo.create_reset_token.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, repository_factory):
        user_repo = repository_factory(
            get_password_reset_token=AsyncMock(return_value=None),
        )
        auth_service = AuthService(
            user_repo=user_repo,
            token_hasher=MagicMock(return_value="hashed-token"),
        )

        with pytest.raises(BadRequestException):
            await auth_service.reset_password("raw-token", "NewStrongPass123")

    @pytest.mark.asyncio
    async def test_reset_password_used_token(self, repository_factory):
        used_token = SimpleNamespace(
            user_id=1,
            is_used=True,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        user_repo = repository_factory(
            get_password_reset_token=AsyncMock(return_value=used_token),
        )
        auth_service = AuthService(
            user_repo=user_repo,
            token_hasher=MagicMock(return_value="hashed-token"),
        )

        with pytest.raises(BadRequestException):
            await auth_service.reset_password("raw-token", "NewStrongPass123")

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, repository_factory):
        valid_token = SimpleNamespace(
            user_id=42,
            is_used=False,
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
        user_repo = repository_factory(
            get_password_reset_token=AsyncMock(return_value=valid_token),
            get_by_id=AsyncMock(return_value=None),
        )
        auth_service = AuthService(
            user_repo=user_repo,
            token_hasher=MagicMock(return_value="hashed-token"),
        )

        with pytest.raises(ResourceNotFoundException):
            await auth_service.reset_password("raw-token", "NewStrongPass123")

    @pytest.mark.asyncio
    async def test_reset_password_success_with_naive_expiry(self, repository_factory):
        token = SimpleNamespace(
            user_id=7,
            is_used=False,
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        user = User(
            id=7,
            username="reset_ok",
            full_name="Reset Ok",
            role=UserRole.CONSUMER,
            mobile_number="1234567890",
            department=Departments.AIML,
            register_number="212223240096",
            email="resetok@example.com",
            hashed_password="old-hash",
            is_active=True,
            is_banned=False,
        )

        user_repo = repository_factory(
            get_password_reset_token=AsyncMock(return_value=token),
            get_by_id=AsyncMock(return_value=user),
            mark_token_as_used=AsyncMock(),
            save_user=AsyncMock(),
        )
        auth_service = AuthService(
            user_repo=user_repo,
            token_hasher=MagicMock(return_value="hashed-token"),
            password_hasher=MagicMock(return_value="new-hash"),
        )

        await auth_service.reset_password("raw-token", "NewStrongPass123")

        assert user.hashed_password == "new-hash"
        user_repo.mark_token_as_used.assert_awaited_once_with(token)
        user_repo.save_user.assert_awaited_once_with(user)

    # TODO: Add tests for password reset flow (token generation, expiration, validation)
