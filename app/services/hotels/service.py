import logging

from app.core.exceptions import ResourceNotFoundException
from app.models.hotel import Hotel
from app.repositories.hotel_repository import HotelRepository, MenuItemRepository
from app.repositories.order_repository import OrderBidRepository, OrderRepository
from app.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class HotelService:
    def __init__(
        self,
        order_repository: OrderRepository,
        hotel_repository: HotelRepository,
        menu_item_repository: MenuItemRepository,
        user_repository: UserRepository,
        orderbid_repository: OrderBidRepository,
    ):
        self.order_repository = order_repository
        self.hotel_repository = hotel_repository
        self.menu_item_repository = menu_item_repository
        self.user_repository = user_repository
        self.orderbid_repository = orderbid_repository

    async def list_hotels(
        self, limit: int = 100, offset: int = 0, is_open: bool | None = None
    ) -> tuple[list[Hotel], int]:
        hotels, total = await self.hotel_repository.list_hotels(
            limit=limit, offset=offset, is_open=is_open
        )
        return hotels, total

    async def get_hotel_by_id(self, hotel_id: int) -> Hotel:
        hotel = await self.hotel_repository.get_hotel_by_id(hotel_id)
        if not hotel:
            logger.warning(f"Hotel with ID {hotel_id} not found")
            raise ResourceNotFoundException("Hotel not found")
        return hotel

    async def create_hotel(self, name: str, manager_id: int, description: str | None = "") -> Hotel:
        hotel = await self.hotel_repository.create_hotel(
            name=name, manager_id=manager_id, description=description or ""
        )
        logger.info(f"Hotel created with ID {hotel.id} by manager {manager_id}")
        return hotel

    async def set_hotel_open_status(self, manager_id: int, is_open: bool) -> None:
        hotel = await self.hotel_repository.get_hotel_by_manager_id(manager_id)
        if not hotel:
            logger.warning(f"Hotel not found for manager ID {manager_id}")
            raise ResourceNotFoundException("Hotel not found")
        hotel.is_open = is_open
        await self.hotel_repository.save(hotel)
