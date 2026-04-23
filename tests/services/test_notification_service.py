import json
from datetime import UTC, datetime
from unittest.mock import ANY, AsyncMock, MagicMock, call

import pytest

from app.models.enums import UserRole
from app.services.notifications.service import NotificationService


@pytest.mark.asyncio
async def test_publish_to_users_deduplicates_channels_and_aggregates_subscribers() -> None:
    redis = MagicMock()
    pipeline = MagicMock()
    pipeline.publish = MagicMock()
    pipeline.execute = AsyncMock(return_value=[2, 1])
    redis.pipeline.return_value = pipeline

    service = NotificationService(redis)

    channels, subscribers = await service.publish_to_users(
        user_ids=[7, 3, 7],
        event="order_update",
        message="Order status changed",
        data={"order_id": 10},
    )

    assert channels == ["notifications:user:3", "notifications:user:7"]
    assert subscribers == 3
    assert pipeline.publish.call_args_list == [
        call("notifications:user:3", ANY),
        call("notifications:user:7", ANY),
    ]
    assert pipeline.execute.await_count == 1


@pytest.mark.asyncio
async def test_stream_notifications_subscribes_channels_and_yields_events() -> None:
    redis = MagicMock()
    pubsub = AsyncMock()
    redis.pubsub.return_value = pubsub

    payload = json.dumps(
        {
            "id": "evt-1",
            "event": "order_created",
            "message": "New order is available",
            "data": {"order_id": 111},
            "sent_at": datetime.now(UTC).isoformat(),
        }
    )

    pubsub.get_message = AsyncMock(
        side_effect=[
            {
                "type": "message",
                "data": payload,
            }
        ]
    )

    service = NotificationService(redis)
    stream = service.stream_notifications(
        user_id=42,
        role=UserRole.DELIVERY,
        groups=[" Daily-Rush ", "daily-rush", "priority"],
    )

    first_event = await anext(stream)

    assert first_event["event"] == "order_created"
    assert first_event["id"] == "evt-1"

    decoded_data = json.loads(first_event["data"])
    assert decoded_data["message"] == "New order is available"

    pubsub.subscribe.assert_awaited_once_with(
        "notifications:broadcast",
        "notifications:user:42",
        "notifications:role:delivery",
        "notifications:group:daily-rush",
        "notifications:group:priority",
    )

    await stream.aclose()

    pubsub.unsubscribe.assert_awaited_once_with(
        "notifications:broadcast",
        "notifications:user:42",
        "notifications:role:delivery",
        "notifications:group:daily-rush",
        "notifications:group:priority",
    )
    pubsub.close.assert_awaited_once()
