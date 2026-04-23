from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import OrderStatus
from app.schemas.consumer.orders import OrderRead


class ListOrdersRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    consumer_id: int | None = None
    hotel_id: int | None = None
    delivery_user_id: int | None = None
    status: OrderStatus | None = None
    is_text_based: bool | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    sort_by: str = Field(default="created_at")
    sort_desc: bool = Field(default=True)

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str) -> str:
        allowed_fields = {"id", "created_at", "total_amount"}
        if value not in allowed_fields:
            raise ValueError(f"sort_by must be one of {allowed_fields}")
        return value


class ListOrdersResponse(BaseModel):
    orders: list[OrderRead] = Field(..., description="List of orders matching the criteria")
    total: int
