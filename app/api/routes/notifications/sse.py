import logging

from fastapi import APIRouter, Depends, Query
from sse_starlette import EventSourceResponse

from app.api.dependencies import get_current_user, get_notification_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.auth.auth import CurrentUser
from app.schemas.notifications.sse import (
    NotificationPublishRequest,
    NotificationPublishResponse,
    UsersNotificationPublishRequest,
)
from app.services.notifications.service import NotificationService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stream")
async def stream_notifications(
    groups: list[str] | None = Query(
        default=None,
        description="Optional group subscriptions (repeat query param for multiple groups)",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> EventSourceResponse:
    event_generator = notification_service.stream_notifications(
        user_id=current_user.id,
        role=current_user.role,
        groups=groups,
    )

    logger.info("Opening SSE stream for user_id=%s role=%s", current_user.id, current_user.role)

    return EventSourceResponse(
        event_generator,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/publish/user/{user_id}", response_model=NotificationPublishResponse)
async def publish_to_user(
    user_id: int,
    payload: NotificationPublishRequest,
    _: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPublishResponse:
    channels, subscriber_count = await notification_service.publish_to_user(
        user_id=user_id,
        event=payload.event,
        message=payload.message,
        data=payload.data,
    )
    return NotificationPublishResponse(
        message="Notification published to user",
        channels=channels,
        subscriber_count_hint=subscriber_count,
    )


@router.post("/publish/role/{role}", response_model=NotificationPublishResponse)
async def publish_to_role(
    role: UserRole,
    payload: NotificationPublishRequest,
    _: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPublishResponse:
    channels, subscriber_count = await notification_service.publish_to_role(
        role=role,
        event=payload.event,
        message=payload.message,
        data=payload.data,
    )
    return NotificationPublishResponse(
        message="Notification published to role",
        channels=channels,
        subscriber_count_hint=subscriber_count,
    )


@router.post("/publish/users", response_model=NotificationPublishResponse)
async def publish_to_users(
    payload: UsersNotificationPublishRequest,
    _: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPublishResponse:
    channels, subscriber_count = await notification_service.publish_to_users(
        user_ids=payload.user_ids,
        event=payload.event,
        message=payload.message,
        data=payload.data,
    )
    return NotificationPublishResponse(
        message="Notification published to selected users",
        channels=channels,
        subscriber_count_hint=subscriber_count,
    )


@router.post("/publish/group/{group_name}", response_model=NotificationPublishResponse)
async def publish_to_group(
    group_name: str,
    payload: NotificationPublishRequest,
    _: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPublishResponse:
    channels, subscriber_count = await notification_service.publish_to_group(
        group_name=group_name,
        event=payload.event,
        message=payload.message,
        data=payload.data,
    )
    return NotificationPublishResponse(
        message="Notification published to group",
        channels=channels,
        subscriber_count_hint=subscriber_count,
    )


@router.post("/publish/broadcast", response_model=NotificationPublishResponse)
async def publish_broadcast(
    payload: NotificationPublishRequest,
    _: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPublishResponse:
    channels, subscriber_count = await notification_service.publish_broadcast(
        event=payload.event,
        message=payload.message,
        data=payload.data,
    )
    return NotificationPublishResponse(
        message="Notification broadcast published",
        channels=channels,
        subscriber_count_hint=subscriber_count,
    )
