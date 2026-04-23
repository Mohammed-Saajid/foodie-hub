import logging

from fastapi import APIRouter, Depends, Path, Query

from app.api.dependencies import get_order_bid_service, get_order_service, require_roles_and_terms
from app.models.enums import OrderStatus, UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.schemas.consumer.orders import OrderRead
from app.schemas.delivery.orders import (
    BidCreateRequest,
    BidRead,
    ListAvailableOrdersResponse,
)
from app.services.orders.service import OrderBidService, OrderService


router = APIRouter(prefix="/orders")
logger = logging.getLogger(__name__)


@router.get("", response_model=ListAvailableOrdersResponse)
async def find_orders(
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    orders_service: OrderService = Depends(get_order_service),
    limit: int = 100,
    offset: int = 0,
) -> ListAvailableOrdersResponse:
    orders, total = await orders_service.list_orders(
        limit=limit, offset=offset, status=OrderStatus.BIDDING
    )
    logger.info(
        f"Available orders listed for delivery user {current_user.id},"
        "total available orders: {total}"
    )

    return ListAvailableOrdersResponse(
        orders=[OrderRead.model_validate(order) for order in orders],
        total=total,
    )


@router.post("/{order_id}/bid", response_model=BidRead)
async def place_bid(
    payload: BidCreateRequest,
    order_id: int = Path(..., description="ID of the order to place a bid on"),
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    order_bid_service: OrderBidService = Depends(get_order_bid_service),
) -> BidRead:
    bid = await order_bid_service.place_bid(
        order_id=order_id,
        delivery_user_id=current_user.id,
        bid_amount=payload.amount,
    )
    logger.info(
        f"Bid placed by delivery user {current_user.id} on order {order_id}"
        "with amount ₹{payload.amount}"
    )
    return BidRead.model_validate(bid)


@router.delete("/{bid_id}", response_model=MessageResponse)
async def delete_bid(
    bid_id: int = Path(..., description="ID of the bid to delete"),
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    order_bid_service: OrderBidService = Depends(get_order_bid_service),
) -> MessageResponse:
    await order_bid_service.delete_bid(bid_id)
    logger.info(f"Bid {bid_id} deleted by delivery user {current_user.id}")
    return MessageResponse(message="Bid deleted successfully")


@router.get("/bids", response_model=list[BidRead])
async def my_bids(
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    order_bid_service: OrderBidService = Depends(get_order_bid_service),
) -> list[BidRead]:
    bids = await order_bid_service.get_bids_by_delivery_user_id(current_user.id)
    logger.info(f"Bids listed for delivery user {current_user.id}, total bids: {len(bids)}")
    return [BidRead.model_validate(bid) for bid in bids]


@router.get("/{order_id}/pickup", response_model=MessageResponse)
async def pickup_order(
    order_id: int = Path(..., description="ID of the order to pickup"),
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    order_service: OrderService = Depends(get_order_service),
) -> MessageResponse:
    await order_service.pickup_order(order_id, current_user.id)
    logger.info(f"Order {order_id} picked up by delivery user {current_user.id}")
    return MessageResponse(message="Order is out for delivery")


@router.patch("/{order_id}/complete", response_model=MessageResponse)
async def complete_order(
    order_id: int = Path(..., description="ID of the order to complete"),
    otp: str = Query(..., description="OTP provided by the consumer for order completion"),
    current_user: User = Depends(require_roles_and_terms(UserRole.DELIVERY)),
    order_service: OrderService = Depends(get_order_service),
) -> MessageResponse:
    await order_service.complete_order(order_id, current_user.id, otp)
    logger.info(f"Order {order_id} completed by delivery user {current_user.id}")
    return MessageResponse(message="Order delivered successfully")
