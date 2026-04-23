from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestAdminOrders:
    @pytest.mark.asyncio
    async def test_get_orders(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        orders = (
            [
                SimpleNamespace(
                    id=1,
                    consumer_id=1,
                    hotel_id=1,
                    status="bidding",
                    total_amount=25.0,
                    delivery_user_id=None,
                    text_order="1 burger, 1 fries",
                    is_text_based=True,
                    created_at=date(2023, 1, 1),
                    hotel=SimpleNamespace(id=1, name="Test Hotel", is_open=True),
                )
            ],
            1,
        )

        order_service = service_factory(list_orders=AsyncMock(return_value=orders))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.get("/admin/orders", params={"limit": 10, "offset": 0, "asc": True})

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_orders_unauthorized(
        self,
        client: AsyncMock,
        user_factory: callable,
        override_dependencies,
    ):
        user = user_factory(id=2, role="consumer")

        override_dependencies(user=user)

        response = await client.get("/admin/orders")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_order(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")

        order_service = service_factory(delete_order=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.delete("/admin/orders/1")

        assert response.status_code == 200
