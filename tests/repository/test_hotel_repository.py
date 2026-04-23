import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Departments, UserRole
from app.models.hotel import Hotel
from app.models.user import User
from app.repositories.hotel_repository import HotelRepository, MenuItemRepository


async def create_test_user(db_session: AsyncSession, prefix: str) -> User:
    user = User(
        username=f"{prefix}_user",
        email=f"{prefix}@example.com",
        hashed_password="password",
        role=UserRole.HOTEL_MANAGER,
        full_name=f"{prefix} Name",
        mobile_number=f"12345{prefix}",
        department=Departments.CSE,
        register_number=f"REG{prefix}",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_create_and_get_hotel(db_session: AsyncSession):
    repo = HotelRepository(db_session)
    user = await create_test_user(db_session, "1")

    hotel = await repo.create_hotel(
        name="Test Hotel", manager_id=user.id, description="A test hotel"
    )
    assert hotel.id is not None
    assert hotel.name == "Test Hotel"
    assert hotel.manager_id == user.id
    assert hotel.description == "A test hotel"

    fetched = await repo.get_hotel_by_id(hotel.id)
    assert fetched is not None
    assert fetched.name == "Test Hotel"


@pytest.mark.asyncio
async def test_get_hotel_by_manager_id(db_session: AsyncSession):
    repo = HotelRepository(db_session)
    user = await create_test_user(db_session, "2")
    user2 = await create_test_user(db_session, "2b")

    hotel = Hotel(name="Manager Hotel", manager_id=user.id, description="Desc")
    db_session.add(hotel)
    await db_session.flush()

    fetched = await repo.get_hotel_by_manager_id(user.id)
    assert fetched is not None
    assert fetched.id == hotel.id

    not_fetched = await repo.get_hotel_by_manager_id(user2.id)
    assert not_fetched is None


@pytest.mark.asyncio
async def test_list_hotels(db_session: AsyncSession):
    repo = HotelRepository(db_session)
    user = await create_test_user(db_session, "3")

    h1 = Hotel(name="Hotel A", manager_id=user.id, is_open=True)
    h2 = Hotel(name="Hotel B", manager_id=user.id, is_open=False)
    db_session.add_all([h1, h2])
    await db_session.flush()

    _, total = await repo.list_hotels()
    assert total >= 2

    hotels_open, _ = await repo.list_hotels(is_open=True)
    assert all(h.is_open for h in hotels_open)

    hotels_closed, _ = await repo.list_hotels(is_open=False)
    assert all(not h.is_open for h in hotels_closed)


@pytest.mark.asyncio
async def test_save_hotel(db_session: AsyncSession):
    repo = HotelRepository(db_session)
    user = await create_test_user(db_session, "4")

    hotel = Hotel(name="Old Name", manager_id=user.id)
    db_session.add(hotel)
    await db_session.flush()

    hotel.name = "New Name"
    await repo.save(hotel)

    fetched = await repo.get_hotel_by_id(hotel.id)
    assert fetched.name == "New Name"


@pytest.mark.asyncio
async def test_menu_item_repository(db_session: AsyncSession):
    repo = MenuItemRepository(db_session)
    hotel_repo = HotelRepository(db_session)
    user = await create_test_user(db_session, "5")

    hotel = await hotel_repo.create_hotel(name="Menu Hotel", manager_id=user.id)

    # Create menu item
    item = await repo.create_menu_item(
        hotel_id=hotel.id,
        name="Burger",
        description="A tasty burger",
        price=10.50,
        is_available=True,
    )
    assert item.id is not None
    assert item.name == "Burger"

    # Get by ID
    fetched = await repo.get_menu_item_by_id(item.id)
    assert fetched is not None
    assert fetched.name == "Burger"

    # Save (update)
    item.price = 12.00
    await repo.save(item)
    fetched2 = await repo.get_menu_item_by_id(item.id)
    assert float(fetched2.price) == 12.0

    # Delete
    await repo.delete(item)
    fetched3 = await repo.get_menu_item_by_id(item.id)
    assert fetched3 is None
