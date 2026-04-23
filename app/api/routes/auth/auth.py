import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_auth_service,
    get_current_user,
    get_terms_service,
    get_user_service,
)
from app.core.session import get_cache
from app.schemas.auth.auth import (
    AuthResponse,
    CurrentUser,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TermsRead,
    UserRead,
)
from app.services.auth.service import AuthService
from app.services.cache import CacheService
from app.services.terms.service import TermsService
from app.services.users.service import UserService


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserRead)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    user = await auth_service.register_user(payload)

    logger.info(
        f"New user registered: {user.full_name} ({user.role}) with username: {user.username}"
    )
    return UserRead.model_validate(user)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    result = await auth_service.authenticate_user(payload.username, payload.password)
    user, token = result
    logger.info(f"User logged in: {user.full_name} ({user.role}) with username: {user.username}")
    return AuthResponse(
        access_token=token,
        first_login_terms_required=not user.terms_accepted,
        user=UserRead.model_validate(user),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.create_password_reset_token(payload.username_or_email)
    logger.info(f"Password reset requested for: {payload.username_or_email}")
    logger.debug(f"Password reset token created for: {payload.username_or_email} (if user exists)")
    return MessageResponse(
        message="If an account exists with this username or email, "
        "a password reset link has been sent to the associated email address",
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.reset_password(payload.token, payload.new_password)
    logger.info(f"Password reset successful for token: {payload.token}")
    return MessageResponse(message="Password reset successful")


@router.get("/terms", response_model=TermsRead)
async def get_current_terms(terms_service: TermsService = Depends(get_terms_service)) -> TermsRead:
    """Get the current active terms and conditions."""
    terms = await terms_service.get_terms_and_conditions()
    logger.info("Fetched current terms and conditions")
    return TermsRead.model_validate(terms)


@router.post("/accept-terms", response_model=MessageResponse)
async def accept_terms(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
    cache: CacheService = Depends(get_cache),
) -> MessageResponse:

    await user_service.accept_terms(current_user.id)
    # Invalidate cache for the user to reflect updated terms acceptance
    cache_key = f"auth:user:{current_user.id}"
    await cache.delete(cache_key)
    logger.debug(f"Cache invalidated for user ID: {current_user.id} after accepting terms")
    logger.info(
        f"User accepted terms: {current_user.full_name}"
        "({current_user.role}) with username: {current_user.username}"
    )
    return MessageResponse(message="Terms and conditions accepted")
