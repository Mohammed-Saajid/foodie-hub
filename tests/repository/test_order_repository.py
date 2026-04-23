import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import BidStatus, Departments, OrderStatus, UserRole
from app.models.hotel import Hotel
from app.models.order import Order
from app.models.user import User
from app.repositories.order_repository import OrderBidRepository, OrderRepository


async def create_test_user(db_session: AsyncSession, prefix: str, role: UserRole) -> User:
    # Use shorter prefixes to avoid database constraint violations
    p = prefix[:4]
    user = User(
        username=f"{prefix}_usr",
        email=f"{prefix}@example.com",
        hashed_password="password",
        role=role,
        full_name=f"{prefix} Name",
        mobile_number=f"123{p}",
        department=Departments.CSE,
        register_number=f"RG{p}",
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def create_test_hotel(db_session: AsyncSession, manager_id: int, prefix: str) -> Hotel:
    hotel = Hotel(name=f"Hotel {prefix}", manager_id=manager_id, description="Desc")
    db_session.add(hotel)
    await db_session.flush()
    return hotel


@pytest.mark.asyncio
async def test_order_repository_crud(db_session: AsyncSession):
    repo = OrderRepository(db_session)
    consumer = await create_test_user(db_session, "consumer1", UserRole.CONSUMER)
    manager = await create_test_user(db_session, "manager1", UserRole.HOTEL_MANAGER)
    hotel = await create_test_hotel(db_session, manager.id, "1")

    # test create
    order = Order(
        consumer_id=consumer.id,
        hotel_id=hotel.id,
        status=OrderStatus.BIDDING,
        total_amount=100.0,
        text_order="I want 2 burgers",
    )

    saved_order = await repo.save(order)
    assert saved_order.id is not None
    assert saved_order.total_amount == 100.0

    # test get_by_id
    fetched_order = await repo.get_by_id(saved_order.id)
    assert fetched_order is not None
    assert fetched_order.id == saved_order.id
    assert fetched_order.hotel is not None

    # test get_orders_by_consumer_id
    consumer_orders = await repo.get_orders_by_consumer_id(consumer.id)
    assert len(consumer_orders) == 1
    assert consumer_orders[0].id == saved_order.id

    # test list_orders
    orders, total = await repo.list_orders(consumer_id=consumer.id)
    assert total >= 1
    assert len(orders) >= 1

    # test list_orders via search params
    orders_by_status, _ = await repo.list_orders(status=OrderStatus.BIDDING)
    assert len(orders_by_status) > 0
    orders_by_hotel, _ = await repo.list_orders(hotel_id=hotel.id)
    assert len(orders_by_hotel) > 0

    # test order stats
    stats = await repo.get_order_stats(hotel_id=hotel.id)
    assert len(stats) >= 1
    assert stats[0][0] == OrderStatus.BIDDING

    # test delete_order
    await repo.delete_order(saved_order)
    fetched_deleted = await repo.get_by_id(saved_order.id)
    assert fetched_deleted is None


@pytest.mark.asyncio
async def test_order_bid_repository_crud(db_session: AsyncSession):
    order_repo = OrderRepository(db_session)
    bid_repo = OrderBidRepository(db_session)

    consumer = await create_test_user(db_session, "b_consumer1", UserRole.CONSUMER)
    delivery = await create_test_user(db_session, "b_delivery1", UserRole.DELIVERY)

    order = Order(
        consumer_id=consumer.id, status=OrderStatus.BIDDING, total_amount=0.0, is_text_based=True
    )
    saved_order = await order_repo.save(order)

    # test create_bid
    bid = await bid_repo.create_bid(
        order_id=saved_order.id,
        delivery_user_id=delivery.id,
        bid_amount=20.0,
        upi_screenshot_url="http://screenshot",
    )
    assert bid.id is not None
    assert bid.amount == 20.0

    # test list_bids_for_order
    bids = await bid_repo.list_bids_for_order(saved_order.id)
    assert len(bids) == 1
    assert bids[0].id == bid.id

    # test get_bid_by_id
    fetched_bid = await bid_repo.get_bid_by_id(bid.id)
    assert fetched_bid is not None

    # test get_bids_by_delivery_user_id
    bids_by_user = await bid_repo.get_bids_by_delivery_user_id(delivery.id)
    assert len(bids_by_user) == 1

    # test save_bid (update)
    bid.status = BidStatus.ACCEPTED
    await bid_repo.save_bid(bid)

    # test get_accepted_bid_by_order_id
    accepted_bid = await bid_repo.get_accepted_bid_by_order_id(saved_order.id)
    assert accepted_bid is not None
    assert accepted_bid.id == bid.id

    # test delete_bid
    await bid_repo.delete_bid(bid.id)
    fet = await bid_repo.get_bid_by_id(bid.id)
    assert fet is None
