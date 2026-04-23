import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": subject,
        "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
    }
    return cast(str, jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM))


def decode_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        return cast(
            dict[str, Any],
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]),
        )
    except JWTError:
        return None


def create_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_otp(length: int) -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))
