import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request

from app.api.dependencies import (
    get_hotel_service,
    get_order_bid_service,
    get_order_service,
    require_roles_and_terms,
)
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.schemas.consumer.orders import (
    AcceptBidResponse,
    OrderBidRead,
    OrderRead,
    PlaceOrderRequest,
)
from app.services.hotels.service import HotelService
from app.services.notifications.service import NotificationService
from app.services.orders.service import OrderBidService, OrderService


router = APIRouter(prefix="/orders")
logger = logging.getLogger(__name__)


async def _publish_order_created_notifications(
    *,
    request: Request,
    order_id: int,
    order_total_amount: float,
    order_is_text_based: bool,
    consumer_id: int,
    hotel_id: int | None,
    hotel_manager_id: int | None,
) -> None:
    try:
        redis = getattr(request.app.state, "redis", None)
        if not redis:
            logger.warning(
                "Skipping order created notifications for order_id=%s because Redis is unavailable",
                order_id,
            )
            return

        notification_service = NotificationService(redis)

        if not order_is_text_based and hotel_manager_id:
            await notification_service.publish_to_user(
                user_id=hotel_manager_id,
                event="order_received",
                message=f"New order received for ₹{order_total_amount}",
                data={"order_id": order_id, "consumer_id": consumer_id},
            )

        order_message = (
            "New text order available"
            if order_is_text_based
            else f"New order available: ₹{order_total_amount}"
        )
        await notification_service.publish_to_role(
            role=UserRole.DELIVERY,
            event="order_available",
            message=order_message,
            data={"order_id": order_id, "hotel_id": hotel_id},
        )
    except Exception:
        logger.exception(
            "Failed to publish order placement notifications for order_id=%s", order_id
        )


async def _publish_bid_accepted_notification(
    *,
    request: Request,
    order_id: int,
    bid_id: int,
    delivery_user_id: int | None,
) -> None:
    try:
        if not delivery_user_id:
            return

        redis = getattr(request.app.state, "redis", None)
        if not redis:
            logger.warning(
                "Skipping bid accepted notification for order_id=%s because Redis is unavailable",
                order_id,
            )
            return

        notification_service = NotificationService(redis)
        await notification_service.publish_to_user(
            user_id=delivery_user_id,
            event="bid_accepted",
            message="Your bid has been accepted. Proceed to pickup.",
            data={"order_id": order_id, "bid_id": bid_id},
        )
    except Exception:
        logger.exception(
            "Failed to publish bid acceptance notification for order_id=%s bid_id=%s",
            order_id,
            bid_id,
        )


@router.post("", response_model=OrderRead)
async def place_order(
    payload: PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.DELIVERY, UserRole.HOTEL_MANAGER, UserRole.ADMIN
        )
    ),
    orders_service: OrderService = Depends(get_order_service),
    hotel_service: HotelService = Depends(get_hotel_service),
) -> OrderRead:
    order = await orders_service.place_order(
        consumer_id=current_user.id,
        hotel_id=payload.hotel_id,
        items=payload.items,
        text_order=payload.text_order,
        is_text_based=payload.text_order is not None,
    )

    hotel_manager_id: int | None = None
    if not order.is_text_based and order.hotel_id:
        try:
            hotel = await hotel_service.get_hotel_by_id(order.hotel_id)
            hotel_manager_id = hotel.manager_id
        except Exception:
            logger.exception("Could not resolve hotel manager for order_id=%s", order.id)

    background_tasks.add_task(
        _publish_order_created_notifications,
        request=request,
        order_id=order.id,
        order_total_amount=float(order.total_amount),
        order_is_text_based=order.is_text_based,
        consumer_id=order.consumer_id,
        hotel_id=order.hotel_id,
        hotel_manager_id=hotel_manager_id,
    )
    logger.info(
        f"Order {order.id} placed by consumer {current_user.id}"
        "for hotel {payload.hotel_id} with total amount ₹{order.total_amount}"
    )
    return OrderRead.model_validate(order)


@router.get("/history", response_model=list[OrderRead])
async def get_order_history(
    current_user: User = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.DELIVERY, UserRole.HOTEL_MANAGER, UserRole.ADMIN
        )
    ),
    orders_service: OrderService = Depends(get_order_service),
) -> list[OrderRead]:
    orders = await orders_service.get_orders_by_consumer_id(current_user.id)
    logger.info(
        f"Order history requested by consumer {current_user.id}, total orders: {len(orders)}"
    )
    return [OrderRead.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.DELIVERY, UserRole.HOTEL_MANAGER, UserRole.ADMIN
        )
    ),
    orders_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await orders_service.get_order_by_id(order_id)
    logger.info(f"Order details requested for order {order.id} by user {current_user.id}")
    return OrderRead.model_validate(order)


@router.get("/{order_id}/bids", response_model=list[OrderBidRead])
async def list_bids_for_order(
    order_id: int = Path(..., description="ID of the order to list bids for"),
    current_user: User = Depends(
        require_roles_and_terms(
            UserRole.CONSUMER, UserRole.DELIVERY, UserRole.HOTEL_MANAGER, UserRole.ADMIN
        )
    ),
    order_bid_service: OrderBidService = Depends(get_order_bid_service),
) -> list[OrderBidRead]:
    bids = await order_bid_service.list_bids_for_order(order_id)
    logger.info(
        f"Bids listed for order {order_id} by user {current_user.id}, total bids: {len(bids)}"
    )
    return [OrderBidRead.model_validate(bid) for bid in bids]


@router.post("/{order_id}/accept-bid/{bid_id}", response_model=AcceptBidResponse)
async def accept_bid(
    background_tasks: BackgroundTasks,
    request: Request,
    order_id: int = Path(..., description="ID of the order for which to accept a bid"),
    bid_id: int = Path(..., description="ID of the bid to accept"),
    current_user: User = Depends(require_roles_and_terms(UserRole.CONSUMER)),
    orders_service: OrderService = Depends(get_order_service),
) -> AcceptBidResponse:
    order = await orders_service.accept_bid(order_id, bid_id)
    background_tasks.add_task(
        _publish_bid_accepted_notification,
        request=request,
        order_id=order_id,
        bid_id=bid_id,
        delivery_user_id=order.delivery_user_id,
    )
    logger.info(
        f"Bid {bid_id} accepted for order {order_id} by consumer {current_user.id},"
        "delivery user {order.delivery_user_id}"
    )
    return AcceptBidResponse(
        message="Bid accepted successfully",
        delivery_user_id=order.delivery_user.id,
        delivery_mobile=order.delivery_user.mobile_number,
        delivery_email=order.delivery_user.email,
        upi_screenshot_url=order.delivery_user.upi_screenshot_url,
        delivery_otp=order.delivery_otp,
    )


@router.post("/{order_id}/cancel", response_model=MessageResponse)
async def cancel_order(
    order_id: int = Path(..., description="ID of the order to cancel"),
    current_user: User = Depends(require_roles_and_terms(UserRole.CONSUMER)),
    orders_service: OrderService = Depends(get_order_service),
) -> MessageResponse:
    await orders_service.cancel_order(order_id)
    logger.info(f"Order {order_id} cancelled by consumer {current_user.id}")
    return MessageResponse(message="Order cancelled successfully")
