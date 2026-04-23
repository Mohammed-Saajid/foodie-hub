import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request

from app.api.dependencies import (
    get_user_service,
    require_roles_and_terms,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.admin.user import ListUsersRequest, ListUsersResponse
from app.schemas.auth.auth import CurrentUser, MessageResponse, UserRead
from app.services.notifications.service import NotificationService
from app.services.users.service import UserService


router = APIRouter()
logger = logging.getLogger(__name__)


async def _publish_user_ban_notifications(
    *,
    request: Request,
    banned_user_id: int,
    admin_user_id: int,
) -> None:
    try:
        redis = getattr(request.app.state, "redis", None)
        if not redis:
            logger.warning(
                "Skipping ban notifications for user_id=%s because Redis is unavailable",
                banned_user_id,
            )
            return

        notification_service = NotificationService(redis)

        await notification_service.publish_to_user(
            user_id=banned_user_id,
            event="account_banned",
            message="Your account has been banned by an administrator.",
            data={"user_id": banned_user_id, "acted_by": admin_user_id},
        )
        await notification_service.publish_to_role(
            role=UserRole.ADMIN,
            event="admin_user_banned",
            message=f"User {banned_user_id} was banned by admin {admin_user_id}",
            data={"user_id": banned_user_id, "acted_by": admin_user_id},
        )
    except Exception:
        logger.exception(
            "Failed to publish ban notifications for banned_user=%s admin=%s",
            banned_user_id,
            admin_user_id,
        )


@router.patch("/users/{user_id}/ban", response_model=MessageResponse)
async def ban_user(
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: int = Path(..., description="ID of the user to ban"),
    user: User = Depends(require_roles_and_terms(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
) -> MessageResponse:
    await user_service.ban_user(user_id)
    background_tasks.add_task(
        _publish_user_ban_notifications,
        request=request,
        banned_user_id=user_id,
        admin_user_id=user.id,
    )
    logger.info(f"Admin {user.id} banned user {user_id}")
    return MessageResponse(message="User banned")


@router.get("/users", response_model=ListUsersResponse)
async def list_users(
    payload: ListUsersRequest = Depends(ListUsersRequest),
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    user_service: UserService = Depends(get_user_service),
) -> ListUsersResponse:
    users, total = await user_service.list_users(
        limit=payload.limit,
        offset=payload.offset,
        username=payload.username,
        full_name=payload.full_name,
        role=payload.role,
        mobile_number=payload.mobile_number,
        department=payload.department,
        register_number=payload.register_number,
        email=payload.email,
        is_active=payload.is_active,
        is_banned=payload.is_banned,
        terms_accepted=payload.terms_accepted,
    )
    logger.info(f"Admin {user.id} listed users, count: {total}")
    return ListUsersResponse(
        users=[UserRead.model_validate(db_user) for db_user in users], total=total
    )
