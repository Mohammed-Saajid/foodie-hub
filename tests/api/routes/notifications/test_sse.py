from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dependencies import get_notification_service
from app.main import app


def _single_event_stream():
    async def _generator():
        yield {"event": "ping", "data": "ok"}

    return _generator()


class TestNotificationSSE:
    @pytest.mark.asyncio
    async def test_stream_notifications(
        self,
        client,
        user_factory,
        override_dependencies,
    ):
        user = user_factory(id=17, role="consumer", terms_accepted=True)
        notification_service = SimpleNamespace(
            stream_notifications=Mock(return_value=_single_event_stream())
        )

        override_dependencies(user=user)

        async def _notification_service_override():
            return notification_service

        app.dependency_overrides[get_notification_service] = _notification_service_override

        response = await client.get("/notifications/stream", params={"groups": ["orders"]})

        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-accel-buffering"] == "no"
        notification_service.stream_notifications.assert_called_once_with(
            user_id=17,
            role="consumer",
            groups=["orders"],
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("path", "service_method", "expected_message", "payload"),
        [
            (
                "/notifications/publish/user/7",
                "publish_to_user",
                "Notification published to user",
                {"event": "order_created", "message": "created", "data": {"id": 1}},
            ),
            (
                "/notifications/publish/role/admin",
                "publish_to_role",
                "Notification published to role",
                {"event": "role_event", "message": "role-msg", "data": {"k": "v"}},
            ),
            (
                "/notifications/publish/users",
                "publish_to_users",
                "Notification published to selected users",
                {
                    "user_ids": [2, 3],
                    "event": "users_event",
                    "message": "users-msg",
                    "data": {"batch": True},
                },
            ),
            (
                "/notifications/publish/group/campus",
                "publish_to_group",
                "Notification published to group",
                {"event": "group_event", "message": "group-msg", "data": {"g": 1}},
            ),
            (
                "/notifications/publish/broadcast",
                "publish_broadcast",
                "Notification broadcast published",
                {
                    "event": "broadcast_event",
                    "message": "broadcast-msg",
                    "data": {"all": True},
                },
            ),
        ],
    )
    async def test_publish_endpoints(
        self,
        client,
        user_factory,
        override_dependencies,
        path,
        service_method,
        expected_message,
        payload,
    ):
        user = user_factory(id=1, role="admin", terms_accepted=True)

        notification_service = SimpleNamespace(
            publish_to_user=AsyncMock(return_value=(["notifications:user:7"], 1)),
            publish_to_role=AsyncMock(return_value=(["notifications:role:admin"], 2)),
            publish_to_users=AsyncMock(
                return_value=(["notifications:user:2", "notifications:user:3"], 3)
            ),
            publish_to_group=AsyncMock(return_value=(["notifications:group:campus"], 4)),
            publish_broadcast=AsyncMock(return_value=(["notifications:broadcast"], 5)),
        )

        override_dependencies(user=user)

        async def _notification_service_override():
            return notification_service

        app.dependency_overrides[get_notification_service] = _notification_service_override

        response = await client.post(path, json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == expected_message
        assert isinstance(body["channels"], list)
        assert body["subscriber_count_hint"] >= 1
        assert getattr(notification_service, service_method).await_count == 1
