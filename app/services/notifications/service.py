import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from time import monotonic

from redis.asyncio import Redis

from app.core.config import settings
from app.models.enums import UserRole
from app.schemas.notifications.sse import NotificationEnvelope


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = settings.NOTIFICATION_CHANNEL_PREFIX

    def _broadcast_channel(self) -> str:
        return f"{self.prefix}:broadcast"

    def _user_channel(self, user_id: int) -> str:
        return f"{self.prefix}:user:{user_id}"

    def _role_channel(self, role: UserRole) -> str:
        return f"{self.prefix}:role:{role.value}"

    def _group_channel(self, group_name: str) -> str:
        return f"{self.prefix}:group:{group_name}"

    @staticmethod
    def normalize_group_name(group_name: str) -> str:
        return group_name.strip().lower()

    def _build_payload(self, event: str, message: str, data: dict[str, object]) -> str:
        payload = NotificationEnvelope(event=event.strip(), message=message, data=data)
        return payload.model_dump_json()

    async def _publish_to_channels(self, channels: list[str], payload: str) -> int:
        if not channels:
            return 0

        pipeline = self.redis.pipeline(transaction=False)
        for channel in channels:
            pipeline.publish(channel, payload)

        publish_results = await pipeline.execute()
        return sum(result for result in publish_results if isinstance(result, int))

    async def publish_to_user(
        self,
        *,
        user_id: int,
        event: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> tuple[list[str], int]:
        channel = self._user_channel(user_id)
        payload = self._build_payload(event, message, data or {})
        subscriber_count = await self._publish_to_channels([channel], payload)
        return [channel], subscriber_count

    async def publish_to_role(
        self,
        *,
        role: UserRole,
        event: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> tuple[list[str], int]:
        channel = self._role_channel(role)
        payload = self._build_payload(event, message, data or {})
        subscriber_count = await self._publish_to_channels([channel], payload)
        return [channel], subscriber_count

    async def publish_to_users(
        self,
        *,
        user_ids: list[int],
        event: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> tuple[list[str], int]:
        unique_user_ids = sorted(set(user_ids))
        channels = [self._user_channel(user_id) for user_id in unique_user_ids]
        payload = self._build_payload(event, message, data or {})
        subscriber_count = await self._publish_to_channels(channels, payload)
        return channels, subscriber_count

    async def publish_to_group(
        self,
        *,
        group_name: str,
        event: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> tuple[list[str], int]:
        normalized_group = self.normalize_group_name(group_name)
        channel = self._group_channel(normalized_group)
        payload = self._build_payload(event, message, data or {})
        subscriber_count = await self._publish_to_channels([channel], payload)
        return [channel], subscriber_count

    async def publish_broadcast(
        self,
        *,
        event: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> tuple[list[str], int]:
        channel = self._broadcast_channel()
        payload = self._build_payload(event, message, data or {})
        subscriber_count = await self._publish_to_channels([channel], payload)
        return [channel], subscriber_count

    async def stream_notifications(
        self,
        *,
        user_id: int,
        role: UserRole,
        groups: list[str] | None = None,
    ) -> AsyncIterator[dict[str, object]]:
        normalized_groups = []
        for group_name in groups or []:
            normalized_name = self.normalize_group_name(group_name)
            if normalized_name:
                normalized_groups.append(normalized_name)

        unique_groups = sorted(set(normalized_groups))[: settings.SSE_MAX_GROUPS_PER_CONNECTION]

        channels = [
            self._broadcast_channel(),
            self._user_channel(user_id),
            self._role_channel(role),
            *[self._group_channel(group_name) for group_name in unique_groups],
        ]

        pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(*channels)

        logger.info(
            "SSE subscription established for user_id=%s role=%s channels=%s",
            user_id,
            role,
            channels,
        )

        last_heartbeat = monotonic()

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=settings.SSE_POLL_TIMEOUT_SECONDS,
                )

                if message and message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")

                    if isinstance(raw_data, str):
                        try:
                            envelope = NotificationEnvelope.model_validate_json(raw_data)
                        except Exception:
                            logger.warning("Skipping malformed notification payload")
                            continue

                        yield {
                            "id": envelope.id,
                            "event": envelope.event,
                            "retry": settings.SSE_RETRY_MS,
                            "data": envelope.model_dump_json(),
                        }
                        continue

                if monotonic() - last_heartbeat >= settings.SSE_HEARTBEAT_SECONDS:
                    heartbeat_payload = {
                        "sent_at": datetime.now(UTC).isoformat(),
                        "kind": "heartbeat",
                    }
                    yield {
                        "event": "heartbeat",
                        "retry": settings.SSE_RETRY_MS,
                        "data": json.dumps(heartbeat_payload),
                    }
                    last_heartbeat = monotonic()

                await asyncio.sleep(0)
        except asyncio.CancelledError:
            logger.info("SSE subscription closed for user_id=%s", user_id)
            raise
        finally:
            await pubsub.unsubscribe(*channels)
            await pubsub.close()
