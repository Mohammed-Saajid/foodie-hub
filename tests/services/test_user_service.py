from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.services.users.service import UserService


@pytest.mark.asyncio
async def test_ban_user_success(user_factory):
    """Test successfully banning a user."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(id=1, is_banned=False)
    user_repository.get_by_id.return_value = user

    await user_service.ban_user(1)

    user_repository.get_by_id.assert_called_once_with(1)
    assert user.is_banned is True
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_ban_user_already_banned(user_factory):
    """Test banning a user who is already banned."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(id=1, is_banned=True)
    user_repository.get_by_id.return_value = user

    await user_service.ban_user(1)

    user_repository.get_by_id.assert_called_once_with(1)
    user_repository.save_user.assert_not_called()


@pytest.mark.asyncio
async def test_ban_user_not_found():
    """Test banning a user who does not exist."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user_repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        await user_service.ban_user(1)

    user_repository.get_by_id.assert_called_once_with(1)
    user_repository.save_user.assert_not_called()


@pytest.mark.asyncio
async def test_list_users(user_factory):
    """Test listing users."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    users = [user_factory(id=1), user_factory(id=2)]
    user_repository.list_all.return_value = (users, 2)

    result_users, total = await user_service.list_users(limit=10, offset=0)

    assert len(result_users) == 2
    assert total == 2
    user_repository.list_all.assert_called_once()


@pytest.mark.asyncio
async def test_accept_terms():
    """Test accepting terms and conditions for a user."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    await user_service.accept_terms(1)
    user_repository.accept_terms.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_update_user_profile_success(user_factory):
    """Test successfully updating a user profile."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(id=1, full_name="Old Name")
    user_repository.get_by_id.return_value = user

    updated_user = await user_service.update_user_profile(1, name="New Name")

    assert updated_user.full_name == "New Name"
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_update_user_profile_optional_fields(user_factory):
    """Test updating optional profile fields to cover all assignment branches."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(
        id=1,
        mobile_number="1111111111",
        about_me="old about",
        profile_picture_url="old.png",
        upi_screenshot_url="old-upi.png",
    )
    user_repository.get_by_id.return_value = user

    updated_user = await user_service.update_user_profile(
        1,
        phone_number="9999999999",
        about_me="new about",
        profile_picture_url="new.png",
        upi_screenshot_url="new-upi.png",
    )

    assert updated_user.mobile_number == "9999999999"
    assert updated_user.about_me == "new about"
    assert updated_user.profile_picture_url == "new.png"
    assert updated_user.upi_screenshot_url == "new-upi.png"
    user_repository.save_user.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_update_user_profile_not_found():
    """Test updating a profile for a user who does not exist."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user_repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        await user_service.update_user_profile(1, name="New Name")


@pytest.mark.asyncio
async def test_update_user_profile_conflict(user_factory):
    """Test updating a profile that results in a conflict (e.g., duplicate email)."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(id=1)
    user_repository.get_by_id.return_value = user
    user_repository.save_user.side_effect = ConflictException("Email already in use")

    with pytest.raises(ConflictException):
        await user_service.update_user_profile(1, email="test@example.com")


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_factory):
    """Test retrieving a user by ID successfully."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user = user_factory(id=1)
    user_repository.get_by_id.return_value = user

    result_user = await user_service.get_user_by_id(1)

    assert result_user.id == 1
    user_repository.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found():
    """Test retrieving a user by ID that does not exist."""
    user_repository = AsyncMock()
    user_service = UserService(user_repository)
    user_repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        await user_service.get_user_by_id(1)

    user_repository.get_by_id.assert_called_once_with(1)
