from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.services.orders.service import OrderService


@pytest.mark.asyncio
async def test_get_order_by_id(
    repository_factory,
    override_dependencies,
):
    order = SimpleNamespace(
        id=1,
        hotel_id=1,
        consumer_id=1,
        status="bidding",
        created_at=datetime.now(),
        total_amount=100,
        delivery_user_id=None,
        text_order=None,
        is_text_based=False,
        hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
    )
    order_repository = repository_factory(get_by_id=AsyncMock(return_value=order))

    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    result = await order_service.get_order_by_id(1)
    assert result.id == 1


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(
    repository_factory,
    override_dependencies,
):
    order_repository = repository_factory(get_by_id=AsyncMock(return_value=None))

    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    with pytest.raises(ResourceNotFoundException):
        await order_service.get_order_by_id(999)


@pytest.mark.asyncio
async def test_delete_order_by_id(
    repository_factory,
    override_dependencies,
):
    order_repository = repository_factory(delete_by_id=AsyncMock(return_value=None))

    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    result = await order_service.delete_order(1)
    assert result is None


@pytest.mark.asyncio
async def test_list_orders(repository_factory, override_dependencies):
    orders = []
    for i in range(1, 6):
        orders.append(
            SimpleNamespace(
                id=i,
                hotel_id=1,
                consumer_id=1,
                status="bidding",
                created_at=datetime.now(),
                total_amount=100,
                delivery_user_id=None,
                text_order=None,
                is_text_based=False,
                hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            )
        )
    order_repository = repository_factory(list_orders=AsyncMock(return_value=(orders, len(orders))))
    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )
    result, total = await order_service.list_orders(limit=100, offset=0)
    assert len(result) == 5
    assert total == 5
    assert result[0].id == 1
    assert result[4].id == 5


@pytest.mark.asyncio
async def test_place_text_order(
    repository_factory,
    override_dependencies,
):
    order = SimpleNamespace(
        id=1,
        hotel_id=1,
        consumer_id=1,
        status="bidding",
        created_at=datetime.now(),
        total_amount=100,
        delivery_user_id=None,
        text_order="I want a burger and fries",
        is_text_based=True,
        hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
    )
    order_repository = repository_factory(create=AsyncMock(return_value=order))
    user_repository = repository_factory(
        get_by_id=AsyncMock(
            return_value=SimpleNamespace(id=1, name="Test User", active_orders_count=0)
        ),
        save_user=AsyncMock(return_value=None),
    )

    override_dependencies(order_repository=order_repository, user_repository=user_repository)
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=user_repository,
        menu_item_repository=AsyncMock(),
    )

    result = await order_service.place_order(
        consumer_id=1,
        hotel_id=1,
        text_order="I want a burger and fries",
        is_text_based=True,
        items=None,
    )
    assert result.id == 1
    assert result.is_text_based is True
    assert result.text_order == "I want a burger and fries"


@pytest.mark.asyncio
async def test_get_orders_by_consumer_id(repository_factory, override_dependencies):
    orders = []
    for i in range(1, 4):
        orders.append(
            SimpleNamespace(
                id=i,
                hotel_id=1,
                consumer_id=1,
                status="bidding",
                created_at=datetime.now(),
                total_amount=100,
                delivery_user_id=None,
                text_order=None,
                is_text_based=False,
                hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            )
        )
    order_repository = repository_factory(get_orders_by_consumer_id=AsyncMock(return_value=orders))
    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )
    result = await order_service.get_orders_by_consumer_id(1)
    assert len(result) == 3
    assert result[0].id == 1
    assert result[2].id == 3


@pytest.mark.asyncio
async def test_accept_bid(repository_factory, override_dependencies):
    order_bid = SimpleNamespace(
        id=1,
        order_id=1,
        delivery_user_id=1,
        amount=150,
        created_at=datetime.now(),
        order=SimpleNamespace(
            id=1,
            hotel_id=1,
            consumer_id=1,
            status="bidding",
            created_at=datetime.now(),
            total_amount=100,
            delivery_user_id=None,
            text_order=None,
            is_text_based=False,
            hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            order=SimpleNamespace(
                id=1,
                hotel_id=1,
                consumer_id=1,
                status="bidding",
                created_at=datetime.now(),
                total_amount=100,
                delivery_user_id=None,
                text_order=None,
                is_text_based=False,
                hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            ),
        ),
    )
    order_bid_repository = repository_factory(
        get_bid_by_id=AsyncMock(return_value=order_bid), save=AsyncMock(return_value=None)
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=order_bid.order), save=AsyncMock(return_value=None)
    )

    override_dependencies(
        order_bid_repository=order_bid_repository, order_repository=order_repository
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=order_bid_repository,
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    result = await order_service.accept_bid(1, 1)
    assert result is not None
    assert result.delivery_user_id == 1
    assert result.status == "bid_accepted"


@pytest.mark.asyncio
async def test_accept_bid_invalid_status(repository_factory, override_dependencies):
    order_bid = SimpleNamespace(
        id=1,
        order_id=1,
        delivery_user_id=1,
        amount=150,
        created_at=datetime.now(),
        order=SimpleNamespace(
            id=1,
            hotel_id=1,
            consumer_id=1,
            status="accepted",
            created_at=datetime.now(),
            total_amount=100,
            delivery_user_id=None,
            text_order=None,
            is_text_based=False,
            hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            order=SimpleNamespace(
                id=1,
                hotel_id=1,
                consumer_id=1,
                status="accepted",
                created_at=datetime.now(),
                total_amount=100,
                delivery_user_id=None,
                text_order=None,
                is_text_based=False,
                hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
            ),
        ),
    )
    order_bid_repository = repository_factory(
        get_bid_by_id=AsyncMock(return_value=order_bid), save=AsyncMock(return_value=None)
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=order_bid.order), save=AsyncMock(return_value=None)
    )

    override_dependencies(
        order_bid_repository=order_bid_repository, order_repository=order_repository
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=order_bid_repository,
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    with pytest.raises(ValueError):
        await order_service.accept_bid(1, 1)


@pytest.mark.asyncio
async def test_accept_bid_order_not_found(repository_factory, override_dependencies):
    order_bid = SimpleNamespace(
        id=1, order_id=999, delivery_user_id=1, amount=150, created_at=datetime.now(), order=None
    )
    order_bid_repository = repository_factory(
        get_bid_by_id=AsyncMock(return_value=order_bid), save=AsyncMock(return_value=None)
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=None), save=AsyncMock(return_value=None)
    )

    override_dependencies(
        order_bid_repository=order_bid_repository, order_repository=order_repository
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=order_bid_repository,
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    with pytest.raises(ResourceNotFoundException):
        await order_service.accept_bid(1, 1)


@pytest.mark.asyncio
async def test_cancel_order(repository_factory, override_dependencies):
    order = SimpleNamespace(
        id=1,
        hotel_id=1,
        consumer_id=1,
        status="bidding",
        created_at=datetime.now(),
        total_amount=100,
        delivery_user_id=None,
        text_order=None,
        is_text_based=False,
        hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=order), save=AsyncMock(return_value=None)
    )
    user_repository = repository_factory(
        get_by_id=AsyncMock(
            return_value=SimpleNamespace(
                id=1, name="Test User", active_orders_count=0, active_orders_for_delivery_count=0
            )
        ),
        save_user=AsyncMock(return_value=None),
    )
    override_dependencies(order_repository=order_repository, user_repository=user_repository)
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=user_repository,
        menu_item_repository=AsyncMock(),
    )

    await order_service.cancel_order(1)
    assert order.status == "cancelled"


@pytest.mark.asyncio
async def test_pickup_order(repository_factory, override_dependencies):
    order = SimpleNamespace(
        id=1,
        hotel_id=1,
        consumer_id=1,
        status="bid_accepted",
        created_at=datetime.now(),
        total_amount=100,
        delivery_user_id=1,
        text_order=None,
        is_text_based=False,
        hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=order), save=AsyncMock(return_value=None)
    )

    override_dependencies(
        order_repository=order_repository,
    )
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=AsyncMock(),
        menu_item_repository=AsyncMock(),
    )

    await order_service.pickup_order(1, 1)
    assert order.status == "out_for_delivery"


@pytest.mark.asyncio
async def test_complete_order(repository_factory, override_dependencies):
    order = SimpleNamespace(
        id=1,
        hotel_id=1,
        consumer_id=1,
        status="out_for_delivery",
        created_at=datetime.now(),
        total_amount=100,
        delivery_user_id=1,
        text_order=None,
        is_text_based=False,
        hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
        delivery_otp="123456",
    )
    order_repository = repository_factory(
        get_by_id=AsyncMock(return_value=order), save=AsyncMock(return_value=None)
    )
    user_repository = repository_factory(
        get_by_id=AsyncMock(
            return_value=SimpleNamespace(
                id=1, name="Test User", active_orders_count=0, active_orders_for_delivery_count=0
            )
        ),
        save_user=AsyncMock(return_value=None),
    )
    override_dependencies(order_repository=order_repository, user_repository=user_repository)
    order_service = OrderService(
        hotel_repository=AsyncMock(),
        orderbid_repository=AsyncMock(),
        order_repository=order_repository,
        user_repository=user_repository,
        menu_item_repository=AsyncMock(),
    )

    await order_service.complete_order(1, 1, "123456")
    assert order.status == "delivered"
