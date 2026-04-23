from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestHotelMenu:
    @pytest.mark.asyncio
    async def test_create_menu_item(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )

        menu_service = service_factory(create_menu_item=AsyncMock(return_value=menu_item))

        override_dependencies(
            user=user,
            menu_service=menu_service,
        )

        payload = {
            "name": "Pasta",
            "description": "Delicious pasta with tomato sauce",
            "price": 12.99,
            "is_available": True,
        }

        response = await client.post("hotel-manager/menu/create", json=payload)

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Pasta"

    @pytest.mark.asyncio
    async def test_update_menu_item(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )

        menu_service = service_factory(update_menu_item=AsyncMock(return_value=menu_item))

        override_dependencies(
            user=user,
            menu_service=menu_service,
        )

        payload = {
            "name": "Pasta",
            "description": "Delicious pasta with tomato sauce",
            "price": 12.99,
            "is_available": True,
        }

        response = await client.patch("hotel-manager/menu/update/1", json=payload)

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Pasta"

    @pytest.mark.asyncio
    async def test_delete_menu_item(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")

        menu_service = service_factory(delete_menu_item=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            menu_service=menu_service,
        )

        response = await client.delete("hotel-manager/menu/delete/1")

        assert response.status_code == 200
        assert response.json()["message"] == "Menu item 1 deleted"

    @pytest.mark.asyncio
    async def test_get_menu_item(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="hotel_manager")
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )

        menu_service = service_factory(get_menu_item=AsyncMock(return_value=menu_item))

        override_dependencies(
            user=user,
            menu_service=menu_service,
        )

        response = await client.get("hotel-manager/menu/1")

        assert response.status_code == 200
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Pasta"
        assert response.json()["description"] == "Delicious pasta with tomato sauce"
