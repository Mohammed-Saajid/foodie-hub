from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException


class TestConsumerHotels:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_role",
        ["consumer", "admin", "delivery", "hotel_manager"],
        ids=["consumer", "admin", "delivery", "hotel_manager"],
    )
    async def test_get_hotels(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        user_role,
        override_dependencies,
    ):
        user = user_factory(id=1, role=user_role)
        hotels = ([SimpleNamespace(id=1, name="Hotel A", is_open=True)], 1)

        hotel_service = service_factory(list_hotels=AsyncMock(return_value=hotels))

        override_dependencies(
            user=user,
            hotel_service=hotel_service,
        )

        response = await client.get("/consumer/hotels", params={"limit": 10, "offset": 0})

        assert response.status_code == 200
        data = response.json()
        assert len(data["hotels"]) == 1
        assert data["hotels"][0]["id"] == 1
        assert data["hotels"][0]["name"] == "Hotel A"

    @pytest.mark.asyncio
    async def test_get_hotel_details(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        hotel = SimpleNamespace(id=1, name="Hotel A", is_open=True)

        hotel_service = service_factory(get_hotel_by_id=AsyncMock(return_value=hotel))

        override_dependencies(
            user=user,
            hotel_service=hotel_service,
        )

        response = await client.get("/consumer/hotels/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Hotel A"

    @pytest.mark.asyncio
    async def test_get_hotel_details_not_found(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")

        hotel_service = service_factory(
            get_hotel_by_id=AsyncMock(side_effect=ResourceNotFoundException("Hotel not found"))
        )

        override_dependencies(
            user=user,
            hotel_service=hotel_service,
        )

        response = await client.get("/consumer/hotels/999")

        assert response.status_code == 404
