from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.session import get_cache, get_db, get_redis
from app.core.utils import build_current_user, fetch_user_from_db
from app.models.enums import UserRole
from app.repositories.hotel_repository import HotelRepository, MenuItemRepository
from app.repositories.order_repository import OrderBidRepository, OrderRepository
from app.repositories.support_repository import FeedbackRepository, ReportRepository
from app.repositories.terms_and_conditions_repository import TermsAndConditionsRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth.auth import CurrentUser
from app.services.auth.service import AuthService
from app.services.cache import CacheService
from app.services.hotels.service import HotelService
from app.services.menu.service import MenuService
from app.services.notifications.service import NotificationService
from app.services.orders.service import OrderBidService, OrderService
from app.services.support.feedback_service import FeedbackService
from app.services.support.report_service import ReportService
from app.services.terms.service import TermsService
from app.services.users.service import UserService


security = HTTPBearer()

CACHE_TTL_SECONDS = 1300  # 30 minutes


def extract_user_id(payload: dict[str, Any] | None) -> int:
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid authentication token")

    try:
        return int(payload["sub"])
    except (ValueError, TypeError) as err:
        raise UnauthorizedException("Invalid authentication token") from err


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
) -> CurrentUser:
    token = credentials.credentials  # Implement your token decoding logic here
    payload = decode_token(token)

    user_id = extract_user_id(payload)
    cache_key = f"auth:user:{user_id}"

    # 1. Try cache
    user_data = await cache.get_model(cache_key, CurrentUser)

    # 2. Fallback to DB
    if user_data is None:
        user = await fetch_user_from_db(db, user_id)

        if not user:
            raise UnauthorizedException("User not found")

        user_data = build_current_user(user)

        await cache.set_model(cache_key, user_data, CACHE_TTL_SECONDS)

    # 3. State validation
    if not user_data.is_active or user_data.is_banned:
        raise UnauthorizedException("Inactive or invalid user")

    return user_data


def require_roles_and_terms(
    *roles: UserRole,
) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    async def checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise ForbiddenException("Insufficient permissions")
        if not current_user.terms_accepted:
            raise ForbiddenException("Terms of service not accepted")
        return current_user

    return checker


def get_order_repository(db: AsyncSession = Depends(get_db)) -> OrderRepository:
    return OrderRepository(db)


def get_hotel_repository(db: AsyncSession = Depends(get_db)) -> HotelRepository:
    return HotelRepository(db)


def get_menu_item_repository(db: AsyncSession = Depends(get_db)) -> MenuItemRepository:
    return MenuItemRepository(db)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_order_bid_repository(db: AsyncSession = Depends(get_db)) -> OrderBidRepository:
    return OrderBidRepository(db)


def get_report_repository(db: AsyncSession = Depends(get_db)) -> ReportRepository:
    return ReportRepository(db)


def get_terms_repository(db: AsyncSession = Depends(get_db)) -> TermsAndConditionsRepository:
    return TermsAndConditionsRepository(db)


def get_feedback_repository(db: AsyncSession = Depends(get_db)) -> FeedbackRepository:
    return FeedbackRepository(db)


async def get_order_service(
    order_repository: OrderRepository = Depends(get_order_repository),
    hotel_repository: HotelRepository = Depends(get_hotel_repository),
    menu_item_repository: MenuItemRepository = Depends(get_menu_item_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    order_bid_repository: OrderBidRepository = Depends(get_order_bid_repository),
) -> OrderService:
    return OrderService(
        order_repository=order_repository,
        hotel_repository=hotel_repository,
        menu_item_repository=menu_item_repository,
        user_repository=user_repository,
        orderbid_repository=order_bid_repository,
    )


async def get_report_service(
    report_repository: ReportRepository = Depends(get_report_repository),
) -> ReportService:
    return ReportService(report_repository)


async def get_terms_service(
    terms_repository: TermsAndConditionsRepository = Depends(get_terms_repository),
) -> TermsService:
    return TermsService(terms_repository)


async def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repository)


async def get_feedback_service(
    feedback_repository: FeedbackRepository = Depends(get_feedback_repository),
) -> FeedbackService:
    return FeedbackService(feedback_repository)


async def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(
        user_repo=user_repository,
        password_hasher=hash_password,
        password_verifier=verify_password,
        token_creator=create_access_token,
        reset_token_creator=create_reset_token,
        token_hasher=hash_token,
    )


async def get_order_bid_service(
    db: AsyncSession = Depends(get_db),
    order_bid_repository: OrderBidRepository = Depends(get_order_bid_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> OrderBidService:
    return OrderBidService(
        db,
        order_bid_repository,
        order_repository,
        user_repository,
    )


async def get_hotel_service(
    order_repository: OrderRepository = Depends(get_order_repository),
    hotel_repository: HotelRepository = Depends(get_hotel_repository),
    menu_item_repository: MenuItemRepository = Depends(get_menu_item_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    order_bid_repository: OrderBidRepository = Depends(get_order_bid_repository),
) -> HotelService:
    return HotelService(
        order_repository,
        hotel_repository,
        menu_item_repository,
        user_repository,
        order_bid_repository,
    )


async def get_menu_service(
    order_repository: OrderRepository = Depends(get_order_repository),
    hotel_repository: HotelRepository = Depends(get_hotel_repository),
    menu_item_repository: MenuItemRepository = Depends(get_menu_item_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    order_bid_repository: OrderBidRepository = Depends(get_order_bid_repository),
) -> MenuService:
    return MenuService(
        order_repository,
        hotel_repository,
        menu_item_repository,
        user_repository,
        order_bid_repository,
    )


async def get_notification_service(
    redis: Redis = Depends(get_redis),
) -> NotificationService:
    return NotificationService(redis)
