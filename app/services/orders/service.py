import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundException
from app.core.security import generate_otp
from app.models.enums import BidStatus, OrderStatus
from app.models.order import Order, OrderBid
from app.repositories.hotel_repository import HotelRepository, MenuItemRepository
from app.repositories.order_repository import OrderBidRepository, OrderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.consumer.orders import PlaceOrderItem


logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        hotel_repository: HotelRepository,
        menu_item_repository: MenuItemRepository,
        user_repository: UserRepository,
        orderbid_repository: OrderBidRepository,
    ):
        self.order_repository = order_repository
        self.hotel_repository = hotel_repository
        self.menu_item_repository = menu_item_repository
        self.user_repository = user_repository
        self.orderbid_repository = orderbid_repository

    async def get_order_by_id(self, order_id: int) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})
        return order

    async def delete_order(self, order_id: int) -> None:
        order = await self.order_repository.get_by_id(order_id)
        if order:
            await self.order_repository.delete_order(order)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})

    async def list_orders(
        self,
        limit: int = 100,
        offset: int = 0,
        consumer_id: int | None = None,
        hotel_id: int | None = None,
        delivery_user_id: int | None = None,
        status: OrderStatus | None = None,
        is_text_based: bool | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        hotel_manager_id: int | None = None,
    ) -> tuple[list[Order], int]:

        return await self.order_repository.list_orders(
            limit=limit,
            offset=offset,
            consumer_id=consumer_id,
            hotel_id=hotel_id,
            delivery_user_id=delivery_user_id,
            status=status,
            is_text_based=is_text_based,
            created_after=created_after,
            created_before=created_before,
            sort_by=sort_by,
            sort_desc=sort_desc,
            hotel_manager_id=hotel_manager_id,
        )

    async def get_order_stats(
        self, hotel_id: int | None = None, created_after: datetime | None = None
    ) -> Sequence[Any]:
        return await self.order_repository.get_order_stats(
            hotel_id=hotel_id, created_after=created_after
        )

    async def place_order(
        self,
        hotel_id: int | None,
        consumer_id: int,
        items: list[PlaceOrderItem] | None,
        text_order: str | None,
        is_text_based: bool,
    ) -> Order:
        """
        Place an order. Delegates to repository for total amount calculation.

        For structured orders (with items), total is calculated from menu prices.
        For text-based orders, total amount is 0.0.
        """
        await self._check_maximum_active_orders(consumer_id)
        total_amount = (
            await self._calculate_total_amount(items) if items and not is_text_based else 0.0
        )

        order = await self.order_repository.create(
            hotel_id=hotel_id,
            consumer_id=consumer_id,
            text_order=text_order,
            is_text_based=is_text_based,
            total_amount=total_amount,
        )
        await self._update_active_orders_count(consumer_id, increment=True)
        return order

    async def get_orders_by_consumer_id(
        self, consumer_id: int, limit: int | None = 100, offset: int | None = 0
    ) -> list[Order]:
        return await self.order_repository.get_orders_by_consumer_id(
            consumer_id, limit=limit, offset=offset
        )

    async def accept_bid(self, order_id: int, bid_id: int) -> Order:
        order = await self.get_order_by_id(order_id)
        bid = await self.orderbid_repository.get_bid_by_id(bid_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})

        if order.status != OrderStatus.BIDDING:
            logger.warning(f"Order {order_id} is in {order.status} status, cannot accept bid")
            logger.warning(
                "Attempt to accept bid on order %d which is not in BIDDING status but in %s",
                order_id,
                order.status,
            )
            raise ValueError("Only orders in BIDDING status can be accepted")

        if not bid:
            raise ResourceNotFoundException("Bid not found", details={"bid_id": bid_id})

        bid.status = BidStatus.ACCEPTED
        await self.orderbid_repository.save_bid(bid)
        order.status = OrderStatus.BID_ACCEPTED
        order.delivery_user_id = bid.delivery_user_id
        order.delivery_otp = generate_otp(6)
        await self.order_repository.save(order)
        await self._update_active_delivery_orders_count(bid.delivery_user_id, increment=True)
        return order

    async def cancel_order(self, order_id: int) -> None:
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})

        if order.status in [
            OrderStatus.CANCELLED,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ]:
            raise ValueError("Cannot cancel an order that is already cancelled or delivered")

        order.status = OrderStatus.CANCELLED
        await self.order_repository.save(order)
        await self._update_active_orders_count(order.consumer_id, increment=False)
        if order.delivery_user_id:
            bid = await self.orderbid_repository.get_accepted_bid_by_order_id(order.id)
            if bid:
                bid.status = BidStatus.ORDER_CANCELLED
                await self.orderbid_repository.save_bid(bid)
            await self._update_active_delivery_orders_count(order.delivery_user_id, increment=False)

    async def pickup_order(self, order_id: int, delivery_user_id: int) -> None:
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})

        if order.status != OrderStatus.BID_ACCEPTED:
            raise ValueError("Only orders in BID_ACCEPTED status can be picked up")

        if order.delivery_user_id != delivery_user_id:
            raise ValueError("You are not assigned to this order")

        order.status = OrderStatus.OUT_FOR_DELIVERY
        await self.order_repository.save(order)

    async def complete_order(self, order_id: int, delivery_user_id: int, otp: str) -> None:
        order = await self.get_order_by_id(order_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})

        if order.status != OrderStatus.OUT_FOR_DELIVERY:
            raise ValueError("Only orders that are out for delivery can be completed")

        if order.delivery_user_id != delivery_user_id:
            raise ValueError("You are not assigned to this order")

        if order.delivery_otp != otp:
            raise ValueError("Invalid OTP")

        order.status = OrderStatus.DELIVERED
        await self.order_repository.save(order)
        await self._update_active_orders_count(order.consumer_id, increment=False)
        await self._update_active_delivery_orders_count(delivery_user_id, increment=False)

    async def _check_maximum_active_orders(self, consumer_id: int) -> None:
        user = await self.user_repository.get_by_id(consumer_id)
        if user is None:
            raise ResourceNotFoundException("User not found", details={"user_id": consumer_id})
        if user.active_orders_count >= 3:
            raise ValueError("Maximum 3 active orders allowed")

    async def _check_maximum_active_delivery_orders(self, delivery_user_id: int) -> None:
        user = await self.user_repository.get_by_id(delivery_user_id)
        if user is None:
            raise ResourceNotFoundException("User not found", details={"user_id": delivery_user_id})
        if user.active_orders_for_delivery_count >= 3:
            raise ValueError("Maximum 3 active delivery orders allowed")

    async def _update_active_orders_count(self, consumer_id: int, increment: bool = True) -> None:
        user = await self.user_repository.get_by_id(consumer_id)
        if user is None:
            raise ResourceNotFoundException("User not found", details={"user_id": consumer_id})
        if increment:
            user.active_orders_count += 1
        else:
            user.active_orders_count = max(user.active_orders_count - 1, 0)
        await self.user_repository.save_user(user)

    async def _update_active_delivery_orders_count(
        self, delivery_user_id: int, increment: bool = True
    ) -> None:
        user = await self.user_repository.get_by_id(delivery_user_id)
        if user is None:
            raise ResourceNotFoundException("User not found", details={"user_id": delivery_user_id})
        if increment:
            user.active_orders_for_delivery_count += 1
        else:
            user.active_orders_for_delivery_count = max(
                user.active_orders_for_delivery_count - 1, 0
            )
        await self.user_repository.save_user(user)

    async def _calculate_total_amount(self, items: list[PlaceOrderItem]) -> float:
        """
        Calculate total amount from order items and menu item prices.
        """
        if not items:
            return 0.0

        try:
            menu_item_ids = [item.menu_item_id for item in items]
            menu_items = [
                await self.menu_item_repository.get_menu_item_by_id(menu_item_id)
                for menu_item_id in menu_item_ids
            ]
            menu_items_by_id = {item.id: item for item in menu_items if item is not None}

            total_amount = 0.0
            for order_item in items:
                if order_item.menu_item_id in menu_items_by_id:
                    menu_item = menu_items_by_id[order_item.menu_item_id]
                    total_amount += float(menu_item.price) * order_item.quantity

            return total_amount
        except Exception as e:
            logger.warning("Error calculating total amount for order items: %s", str(e))
            return 0.0


class OrderBidService:
    def __init__(
        self,
        db: AsyncSession,
        orderbid_repository: OrderBidRepository,
        order_repository: OrderRepository,
        user_repository: UserRepository,
    ):
        self.db = db
        self.orderbid_repository = orderbid_repository
        self.order_repository = order_repository
        self.user_repository = user_repository

    async def place_bid(
        self,
        order_id: int,
        delivery_user_id: int,
        bid_amount: float,
    ) -> OrderBid:
        order = await self.order_repository.get_by_id(order_id)
        delivery_user = await self.user_repository.get_by_id(delivery_user_id)
        if not order:
            raise ResourceNotFoundException("Order not found", details={"order_id": order_id})
        if order.status != OrderStatus.BIDDING:
            raise ValueError("Bids can only be placed on orders in BIDDING status")
        existing_bids = await self.orderbid_repository.list_bids_for_order(order_id)
        if any(bid.delivery_user_id == delivery_user_id for bid in existing_bids):
            raise ValueError("You have already placed a bid on this order")
        upi_screenshot_url = delivery_user.upi_screenshot_url if delivery_user else None
        if not upi_screenshot_url:
            raise ValueError("Delivery user has not provided UPI screenshot, cannot place bid")
        return await self.orderbid_repository.create_bid(
            order_id, delivery_user_id, bid_amount, upi_screenshot_url
        )

    async def delete_bid(self, bid_id: int) -> None:
        bid = await self.orderbid_repository.get_bid_by_id(bid_id)
        if not bid:
            raise ResourceNotFoundException("Bid not found", details={"bid_id": bid_id})
        await self.orderbid_repository.delete_bid(bid_id)

    async def list_bids_for_order(self, order_id: int) -> list[OrderBid]:
        return await self.orderbid_repository.list_bids_for_order(order_id)

    async def get_bid_by_id(self, bid_id: int) -> OrderBid | None:
        return await self.orderbid_repository.get_bid_by_id(bid_id)

    async def save_bid(self, bid: OrderBid) -> None:
        await self.orderbid_repository.save_bid(bid)

    async def get_accepted_bid_by_order_id(self, order_id: int) -> OrderBid | None:
        return await self.orderbid_repository.get_accepted_bid_by_order_id(order_id)

    async def get_bids_by_delivery_user_id(self, delivery_user_id: int) -> list[OrderBid]:
        return await self.orderbid_repository.get_bids_by_delivery_user_id(delivery_user_id)
