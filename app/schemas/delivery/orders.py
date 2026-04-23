from pydantic import BaseModel, Field

from app.models.enums import BidStatus
from app.schemas.consumer.orders import OrderRead


class ListAvailableOrdersResponse(BaseModel):
    model_config = {"from_attributes": True}
    orders: list[OrderRead] = Field(..., description="List of available orders for bidding")
    total: int = Field(..., description="Pagination total count of available orders")


class BidCreateRequest(BaseModel):
    model_config = {"from_attributes": True}
    amount: float = Field(gt=0)


class BidRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int = Field(..., description="ID of the bid")
    order_id: int = Field(..., description="ID of the order for which the bid is placed")
    delivery_user_id: int = Field(..., description="ID of the delivery user who placed the bid")
    amount: float = Field(..., gt=0, description="Bid amount offered by the delivery user")
    upi_screenshot_url: str = Field(
        ..., description="URL of the UPI payment screenshot provided by the delivery user"
    )
    status: BidStatus = Field(
        ..., description="Current status of the bid (pending, accepted, rejected)"
    )
