from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestConsumerUsers:
    @pytest.mark.asyncio
    async def test_get_user_profile(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")

        user_service = service_factory(
            get_user_by_id=AsyncMock(
                return_value=SimpleNamespace(
                    id=1,
                    full_name="John Doe",
                    email="john.doe@example.com",
                    mobile_number="1234567890",
                    username="johndoe",
                    role="consumer",
                    department="AIML",
                    register_number="212223240096",
                    terms_accepted=True,
                    terms_accepted_at=date(2023, 1, 1),
                    about_me="Hello, I'm John!",
                    profile_picture_url="http://example.com/profile.jpg",
                    upi_screenshot_url="http://example.com/upi.jpg",
                )
            )
        )
        override_dependencies(
            user=user,
            user_service=user_service,
        )
        response = await client.get("consumer/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["full_name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")

        updated_user = SimpleNamespace(
            id=1,
            full_name="John Doe Updated",
            email="john.doe.updated@example.com",
            mobile_number="0987654321",
            username="johndoe",
            role="consumer",
            department="AIML",
            register_number="212223240096",
            terms_accepted=True,
            terms_accepted_at=date(2023, 1, 1),
            about_me="Hello, I'm John Updated!",
            profile_picture_url="http://example.com/profile_updated.jpg",
            upi_screenshot_url="http://example.com/upi_updated.jpg",
        )

        user_service = service_factory(update_user_profile=AsyncMock(return_value=updated_user))
        override_dependencies(
            user=user,
            user_service=user_service,
        )
        response = await client.patch(
            "consumer/profile",
            json={
                "name": "John Doe Updated",
                "email": "john.doe.updated@example.com",
                "phone_number": "0987654321",
                "about_me": "Hello, I'm John Updated!",
                "profile_picture_url": "http://example.com/profile_updated.jpg",
                "upi_screenshot_url": "http://example.com/upi_updated.jpg",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["full_name"] == "John Doe Updated"
        assert data["email"] == "john.doe.updated@example.com"
