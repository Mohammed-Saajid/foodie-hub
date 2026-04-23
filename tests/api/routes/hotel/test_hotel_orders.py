from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestHotelOrders:
    @pytest.mark.asyncio
    async def test_get_hotel_orders(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
        orders = (
            [
                SimpleNamespace(
                    id=1,
                    hotel_id=1,
                    consumer_id=1,
                    status="bidding",
                    created_at=datetime.now(),
                    total_amount=100,
                    delivery_user_id=None,
                    text_order=None,
                    is_text_based=False,
                    hotel=SimpleNamespace(
                        name="Test Hotel", id=1, is_open=True, description="A test hotel"
                    ),
                )
            ],
            1,
        )

        order_service = service_factory(list_orders=AsyncMock(return_value=orders))

        override_dependencies(
            user=user,
            order_service=order_service,
        )
        response = await client.get("/hotel-manager/orders", params={"limit": 10, "offset": 0})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_order_details(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
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
            hotel=SimpleNamespace(
                name="Test Hotel", id=1, is_open=True, description="A test hotel"
            ),
        )

        order_service = service_factory(get_order_by_id=AsyncMock(return_value=order))

        override_dependencies(
            user=user,
            order_service=order_service,
        )
        response = await client.get("/hotel-manager/orders/1")
        assert response.status_code == 200
