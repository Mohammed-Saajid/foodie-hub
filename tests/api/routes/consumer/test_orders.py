from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestConsumerOrders:
    @pytest.mark.asyncio
    async def test_place_order_non_text(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        order_data = {
            "hotel_id": 1,
            "items": [{"menu_item_id": 1, "quantity": 1}],
            "text_order": None,
        }

        order_service = service_factory(
            place_order=AsyncMock(
                return_value=SimpleNamespace(
                    id=1,
                    consumer_id=1,
                    hotel_id=1,
                    total_amount=100,
                    status="created",
                    is_text_based=False,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )
        )

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.post("/consumer/orders", json=order_data)
        assert response.status_code == 200
        assert response.json()["id"] == 1

    @pytest.mark.asyncio
    async def test_get_order_history(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        orders = [
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
            )
        ]

        order_service = service_factory(get_orders_by_consumer_id=AsyncMock(return_value=orders))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.get("/consumer/orders/history")

        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_get_order_details(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        order = SimpleNamespace(
            id=1,
            consumer_id=1,
            hotel_id=1,
            total_amount=100,
            status="bidding",
            delivery_user_id=None,
            text_order=None,
            is_text_based=False,
            created_at=datetime.now(),
            hotel=SimpleNamespace(name="Test Hotel", is_open=True, id=1),
        )

        order_service = service_factory(get_order_by_id=AsyncMock(return_value=order))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.get("/consumer/orders/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1

    @pytest.mark.asyncio
    async def test_list_bids_for_order(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        bids = [
            SimpleNamespace(
                id=1,
                order_id=1,
                amount=50,
                delivery_user=SimpleNamespace(
                    id=2,
                    full_name="Delivery User",
                    role="delivery",
                    mobile_number="1234567890",
                    username="deliveryuser",
                    department="AIML",
                    register_number="212223240096",
                    email="delivery@example.com",
                    terms_accepted=True,
                    terms_accepted_at=datetime.now(),
                ),
                status="pending",
            )
        ]

        order_bid_service = service_factory(list_bids_for_order=AsyncMock(return_value=bids))

        override_dependencies(
            user=user,
            order_bid_service=order_bid_service,
        )

        response = await client.get("/consumer/orders/1/bids")

        assert response.status_code == 200
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_accept_bid(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        delivery_user = SimpleNamespace(
            id=2,
            mobile_number="1234567890",
            email="delivery@example.com",
            upi_screenshot_url="http://example.com/upi.jpg",
        )
        order = SimpleNamespace(
            id=1, delivery_user_id=2, delivery_user=delivery_user, delivery_otp="123456"
        )

        order_service = service_factory(accept_bid=AsyncMock(return_value=order))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.post("/consumer/orders/1/accept-bid/1")

        assert response.status_code == 200
        assert response.json()["message"] == "Bid accepted successfully"

    @pytest.mark.asyncio
    async def test_cancel_order(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")

        order_service = service_factory(cancel_order=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.post("/consumer/orders/1/cancel")

        assert response.status_code == 200
        assert response.json()["message"] == "Order cancelled successfully"
