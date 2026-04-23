from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    ResourceNotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth.auth import RegisterRequest


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: Callable[[str], str] = hash_password,
        password_verifier: Callable[[str, str], bool] = verify_password,
        token_creator: Callable[[str], str] = create_access_token,
        reset_token_creator: Callable[[], str] = create_reset_token,
        token_hasher: Callable[[str], str] = hash_token,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.password_verifier = password_verifier
        self.token_creator = token_creator
        self.reset_token_creator = reset_token_creator
        self.token_hasher = token_hasher

    async def register_user(self, payload: RegisterRequest) -> User:
        existing = await self.user_repo.get_by_unique_fields(
            username=payload.username,
            email=payload.email,
            register_number=payload.register_number,
            mobile_number=payload.mobile_number,
        )
        if existing:
            raise ConflictException(
                message="Username or email already exists",
                details={"username": payload.username, "email": payload.email},
            )

        return await self.user_repo.create_user(
            username=payload.username,
            full_name=payload.full_name,
            role=payload.role,
            mobile_number=payload.mobile_number,
            department=payload.department,
            register_number=payload.register_number,
            email=payload.email,
            hashed_password=self.password_hasher(payload.password),
            terms_accepted=False,
        )

    async def authenticate_user(self, username: str, password: str) -> tuple[User, str]:
        user = await self.user_repo.get_by_username(username)
        if not user or not self.password_verifier(password, user.hashed_password):
            raise UnauthorizedException(message="Invalid username or password")
        if user.is_banned or not user.is_active:
            raise ForbiddenException(message="User is blocked", details={"username": username})
        token = self.token_creator(str(user.id))
        return user, token

    async def create_password_reset_token(self, username_or_email: str) -> None:
        """Create a password reset token and send it via email.

        For security, this doesn't indicate whether a user was found or not.
        """
        username = username_or_email if "@" not in username_or_email else None
        user = (
            await self.user_repo.get_by_username(username)
            if username
            else await self.user_repo.get_by_email(username_or_email)
        )
        if not user:
            # Don't expose whether the user exists
            return

        raw_token = self.reset_token_creator()
        await self.user_repo.create_reset_token(
            user_id=user.id,
            token_hash=self.token_hasher(raw_token),
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
        )

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        token_hash_value = self.token_hasher(raw_token)

        token = await self.user_repo.get_password_reset_token(token_hash_value)
        now_utc = datetime.now(UTC)
        token_expiry = token.expires_at if token else None
        if token_expiry and token_expiry.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=None)

        if not token or token.is_used or token.expires_at < now_utc:
            raise BadRequestException(
                message="Invalid or expired reset token", details={"token": raw_token}
            )

        user = await self.user_repo.get_by_id(token.user_id)
        if not user:
            raise ResourceNotFoundException(
                message="User not found", details={"user_id": token.user_id}
            )

        user.hashed_password = self.password_hasher(new_password)
        await self.user_repo.mark_token_as_used(token)
        await self.user_repo.save_user(user)
