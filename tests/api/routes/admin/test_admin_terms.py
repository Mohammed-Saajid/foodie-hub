from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.exceptions import ResourceNotFoundException


class TestAdminTermsAndConditionsRoutes:
    @pytest.mark.asyncio
    async def test_update_terms_and_conditions_success(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        terms_service = service_factory(update_terms_and_conditions=AsyncMock(return_value=2))
        cache_service = service_factory(delete=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            terms_service=terms_service,
            cache=cache_service,
        )

        response = await client.patch(
            "/admin/terms/terms-and-conditions",
            params={"content": "Updated terms and conditions content."},
        )

        assert response.status_code == 200
        assert response.json() == {
            "message": "Terms and conditions updated to version "
            "2.Users will need to accept the new terms."
        }

    @pytest.mark.asyncio
    async def test_update_terms_and_conditions_user_not_found(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=20, role="admin")
        terms_service = service_factory(
            update_terms_and_conditions=AsyncMock(
                side_effect=ResourceNotFoundException(message="User not found")
            )
        )
        cache_service = service_factory(delete=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            terms_service=terms_service,
            cache=cache_service,
        )

        response = await client.patch(
            "/admin/terms/terms-and-conditions",
            params={"content": "Updated terms and conditions content."},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_active_terms_and_conditions_success(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        active_terms = SimpleNamespace(version=3, content="Current active terms and conditions.")
        terms_service = service_factory(
            get_terms_and_conditions=AsyncMock(return_value=active_terms)
        )
        cache_service = service_factory()
        override_dependencies(
            user=user,
            terms_service=terms_service,
            cache=cache_service,
        )

        response = await client.get("/admin/terms/terms-and-conditions")

        assert response.status_code == 200
        assert response.json() == {"version": 3, "content": "Current active terms and conditions."}

    @pytest.mark.asyncio
    async def test_get_active_terms_and_conditions_not_found(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        terms_service = service_factory(
            get_terms_and_conditions=AsyncMock(
                side_effect=ResourceNotFoundException(
                    message="Active terms and conditions not found"
                )
            )
        )
        cache_service = service_factory()
        override_dependencies(
            user=user,
            terms_service=terms_service,
            cache=cache_service,
        )

        response = await client.get("/admin/terms/terms-and-conditions")

        assert response.status_code == 404
