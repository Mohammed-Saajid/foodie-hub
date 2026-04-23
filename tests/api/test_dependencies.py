from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    extract_user_id,
    get_auth_service,
    get_current_user,
    get_feedback_repository,
    get_feedback_service,
    get_hotel_repository,
    get_hotel_service,
    get_menu_item_repository,
    get_menu_service,
    get_notification_service,
    get_order_bid_repository,
    get_order_bid_service,
    get_order_repository,
    get_order_service,
    get_report_repository,
    get_report_service,
    get_terms_repository,
    get_terms_service,
    get_user_repository,
    get_user_service,
    require_roles_and_terms,
)
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.enums import UserRole
from app.schemas.auth.auth import CurrentUser
from app.services.auth.service import AuthService
from app.services.hotels.service import HotelService
from app.services.menu.service import MenuService
from app.services.notifications.service import NotificationService
from app.services.orders.service import OrderBidService, OrderService
from app.services.support.feedback_service import FeedbackService
from app.services.support.report_service import ReportService
from app.services.terms.service import TermsService
from app.services.users.service import UserService


class TestExtractUserID:
    def test_extract_user_id_valid_payload(self):
        assert extract_user_id({"sub": "42"}) == 42

    @pytest.mark.parametrize("payload", [None, {}, {"foo": "bar"}, {"sub": "abc"}, {"sub": None}])
    def test_extract_user_id_invalid_payload(self, payload):
        with pytest.raises(UnauthorizedException):
            extract_user_id(payload)


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_from_cache(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        cached_user = CurrentUser(
            id=1,
            full_name="Cached User",
            role=UserRole.CONSUMER,
            is_active=True,
            is_banned=False,
            terms_accepted=True,
        )
        cache = AsyncMock()
        cache.get_model = AsyncMock(return_value=cached_user)
        cache.set_model = AsyncMock()

        with patch("app.api.dependencies.decode_token", return_value={"sub": "1"}):
            user = await get_current_user(credentials=credentials, db=AsyncMock(), cache=cache)

        assert user.id == 1
        cache.get_model.assert_awaited_once()
        cache.set_model.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_from_db_and_caches(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        db_user = MagicMock()
        db_user.id = 2
        db_user.full_name = "DB User"
        db_user.role = UserRole.CONSUMER
        db_user.is_active = True
        db_user.is_banned = False
        db_user.terms_accepted = True

        cache = AsyncMock()
        cache.get_model = AsyncMock(return_value=None)
        cache.set_model = AsyncMock()

        built_user = CurrentUser(
            id=2,
            full_name="DB User",
            role=UserRole.CONSUMER,
            is_active=True,
            is_banned=False,
            terms_accepted=True,
        )

        with (
            patch("app.api.dependencies.decode_token", return_value={"sub": "2"}),
            patch("app.api.dependencies.fetch_user_from_db", new=AsyncMock(return_value=db_user)),
            patch("app.api.dependencies.build_current_user", return_value=built_user),
        ):
            user = await get_current_user(credentials=credentials, db=AsyncMock(), cache=cache)

        assert user.id == 2
        cache.set_model.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        cache = AsyncMock()
        cache.get_model = AsyncMock(return_value=None)

        with (
            patch("app.api.dependencies.decode_token", return_value={"sub": "5"}),
            patch("app.api.dependencies.fetch_user_from_db", new=AsyncMock(return_value=None)),
            pytest.raises(UnauthorizedException),
        ):
            await get_current_user(credentials=credentials, db=AsyncMock(), cache=cache)

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_or_banned(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        cache = AsyncMock()
        cache.get_model = AsyncMock(
            return_value=CurrentUser(
                id=6,
                full_name="Inactive User",
                role=UserRole.CONSUMER,
                is_active=False,
                is_banned=False,
                terms_accepted=True,
            )
        )

        with (
            patch("app.api.dependencies.decode_token", return_value={"sub": "6"}),
            pytest.raises(UnauthorizedException),
        ):
            await get_current_user(credentials=credentials, db=AsyncMock(), cache=cache)


class TestRoleChecks:
    @pytest.mark.asyncio
    async def test_require_roles_and_terms_success(self):
        checker = require_roles_and_terms(UserRole.CONSUMER)
        user = CurrentUser(
            id=1,
            full_name="Allowed User",
            role=UserRole.CONSUMER,
            is_active=True,
            is_banned=False,
            terms_accepted=True,
        )

        result = await checker(current_user=user)
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_require_roles_and_terms_role_failure(self):
        checker = require_roles_and_terms(UserRole.ADMIN)
        user = CurrentUser(
            id=1,
            full_name="No Access",
            role=UserRole.CONSUMER,
            is_active=True,
            is_banned=False,
            terms_accepted=True,
        )

        with pytest.raises(ForbiddenException):
            await checker(current_user=user)

    @pytest.mark.asyncio
    async def test_require_roles_and_terms_terms_failure(self):
        checker = require_roles_and_terms(UserRole.CONSUMER)
        user = CurrentUser(
            id=1,
            full_name="Terms Missing",
            role=UserRole.CONSUMER,
            is_active=True,
            is_banned=False,
            terms_accepted=False,
        )

        with pytest.raises(ForbiddenException):
            await checker(current_user=user)


class TestDependencyFactories:
    @pytest.mark.asyncio
    async def test_repository_factories(self):
        db = MagicMock(spec=AsyncSession)
        assert get_user_repository(db).__class__.__name__ == "UserRepository"
        assert get_hotel_repository(db).__class__.__name__ == "HotelRepository"
        assert get_menu_item_repository(db).__class__.__name__ == "MenuItemRepository"
        assert get_order_repository(db).__class__.__name__ == "OrderRepository"
        assert get_order_bid_repository(db).__class__.__name__ == "OrderBidRepository"
        assert get_report_repository(db).__class__.__name__ == "ReportRepository"
        assert get_terms_repository(db).__class__.__name__ == "TermsAndConditionsRepository"
        assert get_feedback_repository(db).__class__.__name__ == "FeedbackRepository"

    @pytest.mark.asyncio
    async def test_service_factories(self):
        db = MagicMock(spec=AsyncSession)
        order_repo = get_order_repository(db)
        hotel_repo = get_hotel_repository(db)
        menu_repo = get_menu_item_repository(db)
        user_repo = get_user_repository(db)
        order_bid_repo = get_order_bid_repository(db)
        report_repo = get_report_repository(db)
        terms_repo = get_terms_repository(db)
        feedback_repo = get_feedback_repository(db)

        order_service = await get_order_service(
            order_repo, hotel_repo, menu_repo, user_repo, order_bid_repo
        )
        assert isinstance(order_service, OrderService)

        report_service = await get_report_service(report_repo)
        assert isinstance(report_service, ReportService)

        terms_service = await get_terms_service(terms_repo)
        assert isinstance(terms_service, TermsService)

        user_service = await get_user_service(user_repo)
        assert isinstance(user_service, UserService)

        feedback_service = await get_feedback_service(feedback_repo)
        assert isinstance(feedback_service, FeedbackService)

        order_bid_service = await get_order_bid_service(db, order_bid_repo, order_repo, user_repo)
        assert isinstance(order_bid_service, OrderBidService)

        hotel_service = await get_hotel_service(
            order_repo, hotel_repo, menu_repo, user_repo, order_bid_repo
        )
        assert isinstance(hotel_service, HotelService)

        menu_service = await get_menu_service(
            order_repo, hotel_repo, menu_repo, user_repo, order_bid_repo
        )
        assert isinstance(menu_service, MenuService)

    @pytest.mark.asyncio
    async def test_get_auth_and_notification_service(self):
        db = MagicMock(spec=AsyncSession)
        user_repo = get_user_repository(db)
        auth_service = await get_auth_service(user_repo)
        assert isinstance(auth_service, AuthService)

        redis_client = AsyncMock()
        notification_service = await get_notification_service(redis_client)
        assert isinstance(notification_service, NotificationService)
