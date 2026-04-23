from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, computed_field, model_validator

from app.models.enums import BidStatus, OrderStatus
from app.schemas.auth.auth import UserRead
from app.schemas.consumer.hotel import HotelRead


class PlaceOrderItem(BaseModel):
    model_config = {"from_attributes": True}
    menu_item_id: int
    quantity: int = Field(ge=1, le=20)


class PlaceOrderRequest(BaseModel):
    model_config = {"from_attributes": True}
    hotel_id: int | None = None
    items: list[PlaceOrderItem] | None = None
    text_order: str | None = Field(None, min_length=10, max_length=1000)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        hotel_id = self.hotel_id
        items = self.items
        text_order = self.text_order

        # Case 1: Structured order
        if hotel_id is not None and items is not None:
            if text_order is not None:
                raise ValueError("Cannot provide both structured order and text order")
            return self

        # Case 2: Text-based order
        if hotel_id is None and items is None:
            if text_order is None:
                raise ValueError("Either provide hotel_id + items, or text_order")
            return self

        # Invalid mixed case
        raise ValueError("Invalid order format: either provide hotel_id + items, or text_order")


class OrderRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    consumer_id: int
    hotel_id: int | None
    status: OrderStatus
    total_amount: float
    delivery_user_id: int | None = None
    text_order: str | None = None
    is_text_based: bool
    created_at: datetime

    hotel: HotelRead | None = None

    @computed_field
    def hotel_name(self) -> str | None:
        return self.hotel.name if self.hotel else None


class OrderBidRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    order_id: int
    amount: float
    status: BidStatus

    delivery_user: UserRead | None = None

    @computed_field
    def delivery_user_name(self) -> str | None:
        return self.delivery_user.full_name if self.delivery_user else None


class AcceptBidResponse(BaseModel):
    model_config = {"from_attributes": True}
    message: str = Field(description="Confirmation message for the accepted bid")
    delivery_user_id: int = Field(description="ID of the delivery user whose bid was accepted")
    delivery_mobile: str = Field(description="Mobile number of the delivery user")
    delivery_email: str = Field(description="Email address of the delivery user")
    upi_screenshot_url: str | None = Field(
        None, description="URL of the UPI screenshot", title="UPIScreenshotURL"
    )
    delivery_otp: str | None = Field(
        None, description="OTP for the delivery user", title="DeliveryOTP"
    )
