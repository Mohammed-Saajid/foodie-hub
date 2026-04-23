import logging
from decimal import Decimal

from app.core.exceptions import ResourceNotFoundException
from app.models.hotel import MenuItem
from app.repositories.hotel_repository import HotelRepository, MenuItemRepository
from app.repositories.order_repository import OrderBidRepository, OrderRepository
from app.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class MenuService:
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

    async def get_menu_item(self, item_id: int) -> MenuItem:
        menu_item = await self.menu_item_repository.get_menu_item_by_id(item_id)
        if not menu_item:
            raise ResourceNotFoundException("Menu item not found")
        return menu_item

    async def create_menu_item(
        self, hotel_manager_id: int, name: str, description: str, price: float, is_available: bool
    ) -> MenuItem:
        hotel = await self.hotel_repository.get_hotel_by_manager_id(hotel_manager_id)
        if not hotel:
            raise ResourceNotFoundException("Hotel not found for manager")
        return await self.menu_item_repository.create_menu_item(
            hotel_id=hotel.id,
            name=name,
            description=description,
            price=price,
            is_available=is_available,
        )

    async def update_menu_item(
        self,
        hotel_manager_id: int,
        item_id: int,
        name: str | None,
        description: str | None,
        price: float | None,
        is_available: bool | None,
    ) -> MenuItem:
        hotel = await self.hotel_repository.get_hotel_by_manager_id(hotel_manager_id)
        if not hotel:
            raise ResourceNotFoundException("Hotel not found for manager")

        menu_item = await self.menu_item_repository.get_menu_item_by_id(item_id)
        if not menu_item or menu_item.hotel_id != hotel.id:
            raise ResourceNotFoundException("Menu item not found for this hotel")

        if name is not None:
            menu_item.name = name
        if description is not None:
            menu_item.description = description
        if price is not None:
            menu_item.price = Decimal(str(price))
        if is_available is not None:
            menu_item.is_available = is_available

        await self.menu_item_repository.save(menu_item)
        return menu_item

    async def delete_menu_item(self, hotel_manager_id: int, item_id: int) -> None:
        hotel = await self.hotel_repository.get_hotel_by_manager_id(hotel_manager_id)
        if not hotel:
            raise ResourceNotFoundException("Hotel not found for manager")

        menu_item = await self.menu_item_repository.get_menu_item_by_id(item_id)
        if not menu_item or menu_item.hotel_id != hotel.id:
            raise ResourceNotFoundException("Menu item not found for this hotel")

        await self.menu_item_repository.delete(menu_item)
