import logging

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_order_service, require_roles_and_terms
from app.models.enums import OrderStatus, UserRole
from app.models.user import User
from app.schemas.consumer.orders import OrderRead
from app.services.orders.service import OrderService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders")


@router.get("", response_model=list[OrderRead])
async def list_hotel_orders(
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    order_service: OrderService = Depends(get_order_service),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to retrieve"),
    offset: int = Query(0, ge=0, description="Number of orders to skip for pagination"),
    status: OrderStatus | None = Query(None, description="Filter orders by status"),
) -> list[OrderRead]:
    orders, _ = await order_service.list_orders(
        limit=limit, offset=offset, hotel_manager_id=current_user.id, status=status
    )
    logger.info(
        f"Hotel manager {current_user.id} retrieved {len(orders)} orders"
        f" with status filter: {status}"
    )
    return [OrderRead.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_details(
    order_id: int,
    current_user: User = Depends(require_roles_and_terms(UserRole.HOTEL_MANAGER)),
    orders_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    order = await orders_service.get_order_by_id(order_id)
    logger.info(f"Order details requested for order {order.id} by user {current_user.id}")
    return OrderRead.model_validate(order)
