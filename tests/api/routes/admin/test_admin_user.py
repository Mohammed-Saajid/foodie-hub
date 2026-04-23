from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.exceptions import (
    ResourceNotFoundException,
)


class TestAdminUserRoutes:
    @pytest.mark.asyncio
    async def test_ban_user_success(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        user_service = service_factory(ban_user=AsyncMock(return_value=None))
        override_dependencies(
            user=user,
            user_service=user_service,
        )

        response = await client.patch("/admin/users/2/ban")
        assert response.status_code == 200
        assert response.json() == {"message": "User banned"}

    @pytest.mark.asyncio
    async def test_list_users_success(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        users = [
            user_factory(id=2, username="user1"),
            user_factory(id=3, username="user2"),
        ]
        user_service = service_factory(list_users=AsyncMock(return_value=(users, 2)))

        override_dependencies(
            user=user,
            user_service=user_service,
        )

        response = await client.get("/admin/users")
        assert response.status_code == 200
        assert response.json() == {
            "users": [
                {
                    "id": 2,
                    "username": "user1",
                    "full_name": "Test User",
                    "role": "consumer",
                    "terms_accepted": True,
                    "mobile_number": "1234567890",
                    "department": "AIML",
                    "register_number": "212223240096",
                    "email": "example@example.com",
                    "terms_accepted_at": None,
                },
                {
                    "id": 3,
                    "username": "user2",
                    "full_name": "Test User",
                    "role": "consumer",
                    "terms_accepted": True,
                    "mobile_number": "1234567890",
                    "department": "AIML",
                    "register_number": "212223240096",
                    "email": "example@example.com",
                    "terms_accepted_at": None,
                },
            ],
            "total": 2,
        }

    @pytest.mark.asyncio
    async def test_ban_user_not_found(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        user_service = service_factory(
            ban_user=AsyncMock(side_effect=ResourceNotFoundException(message="User not found"))
        )

        override_dependencies(
            user=user,
            user_service=user_service,
        )

        response = await client.patch("/admin/users/999/ban")
        assert response.status_code == 404
