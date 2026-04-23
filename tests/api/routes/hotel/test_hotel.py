from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestHotel:
    @pytest.mark.asyncio
    async def test_create_hotel(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
        hotel_data = {"name": "Test Hotel", "description": "Test hotel description"}

        hotel_service = service_factory(
            create_hotel=AsyncMock(
                return_value=SimpleNamespace(
                    id=1, name="Test Hotel", is_open=True, description="Test hotel description"
                )
            )
        )

        override_dependencies(
            user=user,
            hotel_service=hotel_service,
        )
        response = await client.post("/hotel-manager/hotels/create", json=hotel_data)
        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Test Hotel"
        assert response.json()["description"] == "Test hotel description"

    @pytest.mark.asyncio
    async def test_set_hotel_status(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")

        hotel_service = service_factory(set_hotel_open_status=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            hotel_service=hotel_service,
        )

        response = await client.patch("/hotel-manager/hotels/status", json={"is_open": False})
        assert response.status_code == 200
        assert response.json()["message"] == "Hotel status updated successfully"
