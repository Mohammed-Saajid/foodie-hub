from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient


class TestDeliveryOrders:
    @pytest.mark.asyncio
    async def test_get_delivery_orders(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")
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
                    hotel=SimpleNamespace(name="Test Hotel", id=1, is_open=True),
                )
            ],
            1,
        )

        order_service = service_factory(list_orders=AsyncMock(return_value=orders))

        override_dependencies(
            user=user,
            order_service=order_service,
        )
        response = await client.get("/delivery/orders", params={"limit": 10, "offset": 0})
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert len(response.json()["orders"]) == 1
        assert response.json()["orders"][0]["id"] == 1

    @pytest.mark.asyncio
    async def test_place_bid(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")
        bid = SimpleNamespace(
            id=1,
            order_id=1,
            delivery_user_id=1,
            amount=150,
            upi_screenshot_url="http://example.com/screenshot.png",
            status="pending",
        )

        order_bid_service = service_factory(place_bid=AsyncMock(return_value=bid))

        override_dependencies(
            user=user,
            order_bid_service=order_bid_service,
        )

        payload = {"amount": 150}
        response = await client.post("/delivery/orders/1/bid", json=payload)
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["order_id"] == 1
        assert response.json()["delivery_user_id"] == 1
        assert response.json()["amount"] == 150

    @pytest.mark.asyncio
    async def test_delete_bid(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")

        order_bid_service = service_factory(delete_bid=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            order_bid_service=order_bid_service,
        )

        response = await client.delete("/delivery/orders/1")
        assert response.status_code == 200
        assert response.json()["message"] == "Bid deleted successfully"

    @pytest.mark.asyncio
    async def test_my_bids(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")
        bids = [
            SimpleNamespace(
                id=1,
                order_id=1,
                delivery_user_id=1,
                amount=150,
                upi_screenshot_url="http://example.com/screenshot.png",
                status="pending",
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
            )
        ]

        order_bid_service = service_factory(
            get_bids_by_delivery_user_id=AsyncMock(return_value=bids)
        )
        override_dependencies(
            user=user,
            order_bid_service=order_bid_service,
        )
        response = await client.get("/delivery/orders/bids")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == 1
        assert response.json()[0]["order_id"] == 1
        assert response.json()[0]["delivery_user_id"] == 1
        assert response.json()[0]["amount"] == 150

    @pytest.mark.asyncio
    async def test_pickup_order(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")

        order_service = service_factory(pickup_order=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.get("/delivery/orders/1/pickup")
        assert response.status_code == 200
        assert response.json()["message"] == "Order is out for delivery"

    @pytest.mark.asyncio
    async def test_complete_order(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="delivery")

        order_service = service_factory(complete_order=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            order_service=order_service,
        )

        response = await client.patch("/delivery/orders/1/complete", params={"otp": "123456"})
        assert response.status_code == 200
        assert response.json()["message"] == "Order delivered successfully"
