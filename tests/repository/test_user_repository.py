import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession):
    """Test retrieving a user by ID."""
    repo = UserRepository(db_session)
    user = User(
        username="testuser1",
        email="test1@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Test User 1",
        mobile_number="6221009951",
        department="CSE",
        register_number="RG21009951",
    )
    db_session.add(user)
    await db_session.flush()

    found_user = await repo.get_by_id(user.id)
    assert found_user is not None
    assert found_user.id == user.id

    not_found_user = await repo.get_by_id(999)
    assert not_found_user is None


@pytest.mark.asyncio
async def test_get_user_by_username(db_session: AsyncSession):
    """Test retrieving a user by username."""
    repo = UserRepository(db_session)
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Test User 2",
        mobile_number="0878086834",
        department="CSE",
        register_number="RG78086834",
    )
    db_session.add(user)
    await db_session.flush()

    found_user = await repo.get_by_username("testuser2")
    assert found_user is not None
    assert found_user.username == "testuser2"

    not_found_user = await repo.get_by_username("nonexistent")
    assert not_found_user is None


@pytest.mark.asyncio
async def test_get_by_unique_fields(db_session: AsyncSession):
    """Test retrieving a user by various unique fields."""
    repo = UserRepository(db_session)
    user = User(
        username="testuser3",
        email="test3@example.com",
        register_number="12345",
        mobile_number="9876543210",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Test User 3",
        department="CSE",
    )
    db_session.add(user)
    await db_session.flush()

    assert (await repo.get_by_unique_fields(username="testuser3")) is not None
    assert (await repo.get_by_unique_fields(email="test3@example.com")) is not None
    assert (await repo.get_by_unique_fields(register_number="12345")) is not None
    assert (await repo.get_by_unique_fields(mobile_number="9876543210")) is not None
    assert (await repo.get_by_unique_fields(username="nonexistent")) is None


@pytest.mark.asyncio
async def test_get_by_email(db_session: AsyncSession):
    """Test retrieving a user by email."""
    repo = UserRepository(db_session)
    user = User(
        username="testuser4",
        email="test4@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Test User 4",
        mobile_number="0406347728",
        department="CSE",
        register_number="RG06347728",
    )
    db_session.add(user)
    await db_session.flush()

    found_user = await repo.get_by_email("test4@example.com")
    assert found_user is not None
    assert found_user.email == "test4@example.com"

    not_found_user = await repo.get_by_email("nonexistent@example.com")
    assert not_found_user is None


@pytest.mark.asyncio
async def test_list_all_users(db_session: AsyncSession):
    """Test listing all users with filtering and pagination."""
    repo = UserRepository(db_session)
    user1 = User(
        username="listuser1",
        email="list1@example.com",
        hashed_password="pw",
        role=UserRole.CONSUMER,
        full_name="List One",
        mobile_number="2200703384",
        department="CSE",
        register_number="RG00703384",
    )
    user2 = User(
        username="listuser2",
        email="list2@example.com",
        hashed_password="pw",
        role=UserRole.DELIVERY,
        full_name="List Two",
        mobile_number="9912470059",
        department="CSE",
        register_number="RG12470059",
    )
    db_session.add_all([user1, user2])
    await db_session.flush()

    # Test no filters
    users, total = await repo.list_all()
    assert total >= 2

    # Test filtering
    users, total = await repo.list_all(role=UserRole.DELIVERY)
    assert total >= 1
    assert all(u.role == UserRole.DELIVERY for u in users)

    users, total = await repo.list_all(full_name="List One")
    assert total >= 1
    assert users[0].full_name == "List One"

    # Test pagination
    users, total = await repo.list_all(limit=1, offset=0)
    assert len(users) == 1


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a new user."""
    repo = UserRepository(db_session)
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "hashed_password": "newpassword",
        "role": UserRole.HOTEL_MANAGER,
        "full_name": "Full Name",
        "mobile_number": "1234567890",
        "department": "CSE",
        "register_number": "REG123",
    }
    new_user = await repo.create_user(**user_data)
    assert new_user.id is not None
    assert new_user.username == "newuser"


@pytest.mark.asyncio
async def test_save_user(db_session: AsyncSession):
    """Test saving changes to a user."""
    repo = UserRepository(db_session)
    user = User(
        username="saveuser",
        email="save@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Save User",
        mobile_number="1969823108",
        department="CSE",
        register_number="RG69823108",
    )
    db_session.add(user)
    await db_session.flush()

    user.full_name = "Updated Name"
    await repo.save_user(user)

    updated_user = await repo.get_by_id(user.id)
    assert updated_user.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_accept_terms(db_session: AsyncSession):
    """Test accepting terms for a user."""
    repo = UserRepository(db_session)
    user = User(
        username="termsuser",
        email="terms@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        terms_accepted=False,
        full_name="Terms User",
        mobile_number="6411878905",
        department="CSE",
        register_number="RG11878905",
    )
    db_session.add(user)
    await db_session.flush()

    await repo.accept_terms(user.id)

    updated_user = await repo.get_by_id(user.id)
    assert updated_user.terms_accepted is True
    assert updated_user.terms_accepted_at is not None


@pytest.mark.asyncio
async def test_password_reset_token_flow(db_session: AsyncSession):
    """Test the full password reset token flow."""
    repo = UserRepository(db_session)
    user = User(
        username="pwresetuser",
        email="pwreset@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name="Password Reset User",
        mobile_number="7961985048",
        department="CSE",
        register_number="RG61985048",
    )
    db_session.add(user)
    await db_session.flush()

    token_hash = "test_token_hash"
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)

    # Create
    await repo.create_reset_token(user.id, token_hash, expires_at)
    await db_session.flush()

    # Get
    token_record = await repo.get_password_reset_token(token_hash)
    assert token_record is not None
    assert token_record.user_id == user.id
    assert token_record.is_used is False

    # Mark as used
    await repo.mark_token_as_used(token_record)
    await db_session.flush()

    used_token_record = await repo.get_password_reset_token(token_hash)
    assert used_token_record.is_used is True
