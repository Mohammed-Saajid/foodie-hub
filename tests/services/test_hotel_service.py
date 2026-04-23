from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.hotels.service import HotelService


class TestHotelService:
    @pytest.mark.asyncio
    async def test_list_hotels(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotels = [
            SimpleNamespace(
                id=1,
                name="Test Hotel",
                is_open=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]
        total = 1
        hotel_repository = repository_factory(list_hotels=AsyncMock(return_value=(hotels, total)))

        override_dependencies(
            hotel_repository=hotel_repository,
        )
        hotel_service = HotelService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=AsyncMock(),
        )

        result = await hotel_service.list_hotels()
        print(result)
        assert result[0][0].id == 1
        assert result[0][0].name == "Test Hotel"
        assert result[0][0].is_open is True

    @pytest.mark.asyncio
    async def test_get_hotel_by_id_not_found(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel_repository = repository_factory(get_hotel_by_id=AsyncMock(return_value=None))

        override_dependencies(
            hotel_repository=hotel_repository,
        )
        hotel_service = HotelService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=AsyncMock(),
        )

        with pytest.raises(Exception) as exc_info:
            await hotel_service.get_hotel_by_id(1)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_hotel_by_id_success(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(
            id=1,
            name="Test Hotel",
            is_open=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        hotel_repository = repository_factory(get_hotel_by_id=AsyncMock(return_value=hotel))

        override_dependencies(
            hotel_repository=hotel_repository,
        )
        hotel_service = HotelService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=AsyncMock(),
        )

        result = await hotel_service.get_hotel_by_id(1)
        assert result.id == 1
        assert result.name == "Test Hotel"
        assert result.is_open is True

    @pytest.mark.asyncio
    async def test_create_hotel_success(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(
            id=1,
            name="Test Hotel",
            is_open=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        hotel_repository = repository_factory(create_hotel=AsyncMock(return_value=hotel))

        override_dependencies(
            hotel_repository=hotel_repository,
        )
        hotel_service = HotelService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=AsyncMock(),
        )

        result = await hotel_service.create_hotel(name="Test Hotel", manager_id=5)
        assert result.id == 1
        assert result.name == "Test Hotel"
        assert result.is_open is True

    @pytest.mark.asyncio
    async def test_set_hotel_status_success(
        self,
        repository_factory,
        override_dependencies,
    ):
        hotel = SimpleNamespace(
            id=1,
            name="Test Hotel",
            is_open=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        hotel_repository = repository_factory(
            get_hotel_by_manager_id=AsyncMock(return_value=hotel), save=AsyncMock(return_value=None)
        )

        override_dependencies(
            hotel_repository=hotel_repository,
        )
        hotel_service = HotelService(
            hotel_repository=hotel_repository,
            orderbid_repository=AsyncMock(),
            order_repository=AsyncMock(),
            user_repository=AsyncMock(),
            menu_item_repository=AsyncMock(),
        )

        await hotel_service.set_hotel_open_status(manager_id=5, is_open=False)
        assert hotel.is_open is False
