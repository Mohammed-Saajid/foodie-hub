from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.services.menu.service import MenuService


class TestMenuService:
    @pytest.mark.asyncio
    async def test_get_menu_item_by_id(
        self,
        repository_factory,
        override_dependencies,
    ):
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )
        menu_item_repository = repository_factory(
            get_menu_item_by_id=AsyncMock(return_value=menu_item)
        )

        override_dependencies(
            menu_item_repository=menu_item_repository,
        )
        menu_service = MenuService(
            hotel_repository=AsyncMock(),
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=menu_item_repository,
        )

        result = await menu_service.get_menu_item(1)
        assert result.id == 1
        assert result.name == "Pasta"
        assert result.is_available is True

    @pytest.mark.asyncio
    async def test_get_menu_item_by_id_not_found(
        self,
        repository_factory,
        override_dependencies,
    ):
        menu_item_repository = repository_factory(get_menu_item_by_id=AsyncMock(return_value=None))

        override_dependencies(
            menu_item_repository=menu_item_repository,
        )
        menu_service = MenuService(
            hotel_repository=AsyncMock(),
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=menu_item_repository,
        )

        with pytest.raises(ResourceNotFoundException, match="Menu item not found"):
            await menu_service.get_menu_item(1)

    @pytest.mark.asyncio
    async def test_create_menu_item(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(id=1, name="Test Hotel", is_open=True)
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )
        hotel_repository = repository_factory(get_hotel_by_manager_id=AsyncMock(return_value=hotel))
        menu_item_repository = repository_factory(
            create_menu_item=AsyncMock(return_value=menu_item)
        )

        override_dependencies(
            hotel_repository=hotel_repository,
            menu_item_repository=menu_item_repository,
        )
        menu_service = MenuService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=menu_item_repository,
        )

        result = await menu_service.create_menu_item(
            hotel_manager_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )
        assert result.id == 1
        assert result.name == "Pasta"
        assert result.is_available is True

    @pytest.mark.asyncio
    async def test_update_menu_item(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(id=1, name="Test Hotel", is_open=True)
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )
        hotel_repository = repository_factory(get_hotel_by_manager_id=AsyncMock(return_value=hotel))
        menu_item_repository = repository_factory(
            get_menu_item_by_id=AsyncMock(return_value=menu_item), save=AsyncMock(return_value=None)
        )

        override_dependencies(
            hotel_repository=hotel_repository,
            menu_item_repository=menu_item_repository,
        )
        menu_service = MenuService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=menu_item_repository,
        )

        result = await menu_service.update_menu_item(
            hotel_manager_id=1,
            item_id=1,
            name="Spaghetti",
            description=None,
            price=None,
            is_available=None,
        )
        assert result.id == 1
        assert result.name == "Spaghetti"
        assert result.is_available is True

    @pytest.mark.asyncio
    async def test_delete_menu_item(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(id=1, name="Test Hotel", is_open=True)
        menu_item = SimpleNamespace(
            id=1,
            hotel_id=1,
            name="Pasta",
            description="Delicious pasta with tomato sauce",
            price=12.99,
            is_available=True,
        )
        hotel_repository = repository_factory(get_hotel_by_manager_id=AsyncMock(return_value=hotel))
        menu_item_repository = repository_factory(
            get_menu_item_by_id=AsyncMock(return_value=menu_item),
            delete_menu_item=AsyncMock(return_value=None),
        )

        override_dependencies(
            hotel_repository=hotel_repository,
            menu_item_repository=menu_item_repository,
        )
        menu_service = MenuService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=menu_item_repository,
        )

        await menu_service.delete_menu_item(hotel_manager_id=1, item_id=1)
