from sqlalchemy import func, select

from app.models.hotel import Hotel, MenuItem
from app.repositories.base import BaseRepository


class HotelRepository(BaseRepository):
    async def get_hotel_by_id(self, hotel_id: int) -> Hotel | None:
        result = await self.db.scalars(select(Hotel).where(Hotel.id == hotel_id))
        return result.first()

    async def list_hotels(
        self, limit: int = 100, offset: int = 0, is_open: bool | None = None
    ) -> tuple[list[Hotel], int]:
        query = select(Hotel)
        if is_open is not None:
            query = query.where(Hotel.is_open == is_open)
        result = await self.db.scalars(query.offset(offset).limit(limit))
        hotels = list(result.all())
        # Calculate total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        return hotels, total

    async def create_hotel(self, name: str, manager_id: int, description: str = "") -> Hotel:
        hotel = Hotel(name=name, manager_id=manager_id, description=description)
        self.db.add(hotel)
        await self.db.flush()
        await self.db.refresh(hotel)
        return hotel

    async def get_hotel_by_manager_id(self, manager_id: int) -> Hotel | None:
        result = await self.db.scalars(select(Hotel).where(Hotel.manager_id == manager_id))
        return result.first()

    async def save(self, hotel: Hotel) -> Hotel:

        self.db.add(hotel)
        await self.db.flush()
        await self.db.refresh(hotel)
        return hotel


class MenuItemRepository(BaseRepository):
    async def get_menu_item_by_id(self, menu_item_id: int) -> MenuItem | None:
        result = await self.db.scalars(select(MenuItem).where(MenuItem.id == menu_item_id))
        return result.first()

    async def create_menu_item(
        self, hotel_id: int, name: str, description: str, price: float, is_available: bool
    ) -> MenuItem:
        menu_item = MenuItem(
            hotel_id=hotel_id,
            name=name,
            description=description,
            price=price,
            is_available=is_available,
        )

        self.db.add(menu_item)
        await self.db.flush()
        await self.db.refresh(menu_item)
        return menu_item

    async def save(self, menu_item: MenuItem) -> MenuItem:

        self.db.add(menu_item)
        await self.db.flush()
        await self.db.refresh(menu_item)
        return menu_item

    async def delete(self, menu_item: MenuItem) -> None:
        await self.db.delete(menu_item)
        await self.db.flush()
