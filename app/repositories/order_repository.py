from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import selectinload

from app.models.enums import BidStatus, OrderStatus
from app.models.hotel import Hotel
from app.models.order import Order, OrderBid
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    async def get_by_id(self, order_id: int) -> Order | None:
        query = (
            select(Order)
            .options(selectinload(Order.hotel), selectinload(Order.delivery_user))
            .where(Order.id == order_id)
        )
        result = await self.db.scalars(query)
        return result.first()

    async def save(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_orders_by_consumer_id(
        self, consumer_id: int, limit: int | None = 100, offset: int | None = 0
    ) -> list[Order]:
        query = (
            select(Order)
            .options(selectinload(Order.hotel))
            .where(Order.consumer_id == consumer_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.scalars(query)
        return list(result.all())

    async def delete_order(self, order: Order) -> Order | None:
        # Note: Depending on your database driver, you may not need the begin() block
        # if the session transaction is managed at the service/middleware layer.
        await self.db.delete(order)
        await self.db.flush()
        return order

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
        hotel_manager_id: int | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[list[Order], int]:
        """
        Retrieves a paginated, filtered, and sorted list of orders.
        """
        # 1. Initialize base query
        query = select(Order).options(selectinload(Order.hotel))

        # 2. Apply dynamic filters
        if consumer_id is not None:
            query = query.where(Order.consumer_id == consumer_id)
        if hotel_id is not None:
            query = query.where(Order.hotel_id == hotel_id)
        if delivery_user_id is not None:
            query = query.where(Order.delivery_user_id == delivery_user_id)
        if status is not None:
            query = query.where(Order.status == status)
        if is_text_based is not None:
            query = query.where(Order.is_text_based == is_text_based)
        if created_after is not None:
            query = query.where(Order.created_at >= created_after)
        if created_before is not None:
            query = query.where(Order.created_at <= created_before)
        if hotel_manager_id is not None:
            query = query.where(Order.hotel.has(Hotel.manager_id == hotel_manager_id))

        # 3. Calculate accurate total for pagination (respecting filters)
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # 4. Handle sorting safely to prevent SQL injection or attribute errors
        # Fallback to 'created_at' if the requested sort_by column doesn't exist
        sort_column = getattr(Order, sort_by, Order.created_at)

        query = query.order_by(desc(sort_column)) if sort_desc else query.order_by(asc(sort_column))

        # 5. Apply pagination
        query = query.limit(limit).offset(offset)

        # 6. Execute query
        result = await self.db.scalars(query)
        orders = list(result.all())

        return orders, total

    async def get_order_stats(
        self, hotel_id: int | None = None, created_after: datetime | None = None
    ) -> Sequence[Any]:
        """
        Handles grouping logic separately. Returns order counts and total amounts grouped by status.
        """
        query = select(
            Order.status,
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_amount).label("total_revenue"),
        ).group_by(Order.status)

        # Apply relevant filters for the aggregation
        if hotel_id is not None:
            query = query.where(Order.hotel_id == hotel_id)
        if created_after is not None:
            query = query.where(Order.created_at >= created_after)

        result = await self.db.execute(query)
        return result.all()

    async def create(
        self,
        consumer_id: int,
        hotel_id: int | None = None,
        status: OrderStatus = OrderStatus.BIDDING,
        delivery_user_id: int | None = None,
        total_amount: float = 0.0,
        text_order: str | None = None,
        is_text_based: bool = False,
    ) -> Order:
        """
        Create an order. Calculates total amount from items if provided.
        """
        order = Order(
            consumer_id=consumer_id,
            hotel_id=hotel_id,
            status=status,
            delivery_user_id=delivery_user_id,
            total_amount=total_amount,
            text_order=text_order,
            is_text_based=is_text_based,
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order


class OrderBidRepository(BaseRepository):
    async def create_bid(
        self, order_id: int, delivery_user_id: int, bid_amount: float, upi_screenshot_url: str
    ) -> OrderBid:
        bid = OrderBid(
            order_id=order_id,
            delivery_user_id=delivery_user_id,
            amount=bid_amount,
            upi_screenshot_url=upi_screenshot_url,
            status=BidStatus.PENDING,
        )
        self.db.add(bid)
        await self.db.flush()
        await self.db.refresh(bid)
        return bid

    async def list_bids_for_order(self, order_id: int) -> list[OrderBid]:
        bids = await self.db.execute(
            select(OrderBid)
            .options(selectinload(OrderBid.delivery_user))
            .where(OrderBid.order_id == order_id)
        )
        return list(bids.scalars().all())

    async def get_bid_by_id(self, bid_id: int) -> OrderBid | None:
        return await self.db.get(OrderBid, bid_id)

    async def get_bids_by_delivery_user_id(self, delivery_user_id: int) -> list[OrderBid]:
        result = await self.db.execute(
            select(OrderBid).where(OrderBid.delivery_user_id == delivery_user_id)
        )
        return list(result.scalars().all())

    async def save_bid(self, bid: OrderBid) -> None:
        self.db.add(bid)
        await self.db.flush()
        await self.db.refresh(bid)

    async def get_accepted_bid_by_order_id(self, order_id: int) -> OrderBid | None:
        query = select(OrderBid).where(OrderBid.order_id == order_id, OrderBid.status == "accepted")
        result = await self.db.scalars(query)
        return result.first()

    async def delete_bid(self, bid_id: int) -> None:
        order_bid = await self.get_bid_by_id(bid_id)
        if order_bid:
            await self.db.delete(order_bid)
            await self.db.flush()
