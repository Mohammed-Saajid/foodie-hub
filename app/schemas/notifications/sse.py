from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class NotificationPublishRequest(BaseModel):
    event: str = Field(min_length=1, max_length=100, description="Event type")
    message: str = Field(min_length=1, max_length=1000, description="Human-readable message")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured payload",
    )

    @field_validator("event")
    @classmethod
    def normalize_event(cls, value: str) -> str:
        return value.strip()


class UsersNotificationPublishRequest(NotificationPublishRequest):
    user_ids: list[int] = Field(min_length=1, description="Target user IDs")


class NotificationPublishResponse(BaseModel):
    message: str = Field(description="Operation status")
    channels: list[str] = Field(description="Published Redis channels")
    subscriber_count_hint: int = Field(
        description="Redis publish return sum across channels (active subscribers hint)",
    )


class NotificationEnvelope(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    event: str
    message: str
    data: dict[str, object] = Field(default_factory=dict)
    sent_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
