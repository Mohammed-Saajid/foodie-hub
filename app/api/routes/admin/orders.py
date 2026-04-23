import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_order_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.admin.orders import (
    ListOrdersRequest,
    ListOrdersResponse,
)
from app.schemas.auth.auth import CurrentUser, MessageResponse
from app.schemas.consumer.orders import OrderRead
from app.services.orders.service import OrderService


router = APIRouter(prefix="/orders")

logger = logging.getLogger(__name__)


@router.delete("/{order_id}", response_model=MessageResponse)
async def delete_order(
    order_id: int,
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    order_service: OrderService = Depends(get_order_service),
) -> MessageResponse:
    await order_service.delete_order(order_id)
    logger.info(f"Admin {user.id} deleted order {order_id}")
    return MessageResponse(message=f"Order {order_id} deleted")


@router.get("", response_model=ListOrdersResponse)
async def list_all_orders(
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    order_service: OrderService = Depends(get_order_service),
    payload: ListOrdersRequest = Depends(),
) -> ListOrdersResponse:
    result = await order_service.list_orders(
        limit=payload.limit,
        offset=payload.offset,
        consumer_id=payload.consumer_id,
        hotel_id=payload.hotel_id,
        delivery_user_id=payload.delivery_user_id,
        status=payload.status,
        is_text_based=payload.is_text_based,
        created_after=payload.created_after,
        created_before=payload.created_before,
        sort_by=payload.sort_by,
        sort_desc=payload.sort_desc,
    )
    orders = result[0]
    total = result[1]
    logger.info(f"Admin {user.id} listed orders with filters: {payload.model_dump_json()}")
    return ListOrdersResponse(
        orders=[OrderRead.model_validate(order) for order in orders], total=total
    )
