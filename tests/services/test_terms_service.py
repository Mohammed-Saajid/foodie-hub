from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.services.terms.service import TermsService


class TestTermsService:
    @pytest.mark.asyncio
    async def test_get_terms_and_conditions_success(self, repository_factory):
        active_terms = SimpleNamespace(version=1, content="v1", is_active=True)
        terms_repository = repository_factory(get_active_terms=AsyncMock(return_value=active_terms))
        terms_service = TermsService(terms_repository=terms_repository)

        result = await terms_service.get_terms_and_conditions()

        assert result is active_terms

    @pytest.mark.asyncio
    async def test_get_terms_and_conditions_not_found(self, repository_factory):
        terms_repository = repository_factory(get_active_terms=AsyncMock(return_value=None))
        terms_service = TermsService(terms_repository=terms_repository)

        with pytest.raises(ResourceNotFoundException):
            await terms_service.get_terms_and_conditions()

    @pytest.mark.asyncio
    async def test_update_terms_and_conditions_with_existing_active_terms(self, repository_factory):
        existing_terms = SimpleNamespace(version=1, content="v1", is_active=True)
        created_terms = SimpleNamespace(version=2, content="v2", is_active=True)

        terms_repository = repository_factory(
            get_active_terms=AsyncMock(return_value=existing_terms),
            save_terms=AsyncMock(return_value=existing_terms),
            create_terms=AsyncMock(return_value=created_terms),
        )
        terms_service = TermsService(terms_repository=terms_repository)

        version = await terms_service.update_terms_and_conditions("updated content")

        assert existing_terms.is_active is False
        terms_repository.save_terms.assert_awaited_once_with(existing_terms)
        terms_repository.create_terms.assert_awaited_once_with("updated content")
        assert version == 2

    @pytest.mark.asyncio
    async def test_update_terms_and_conditions_without_existing_terms(self, repository_factory):
        created_terms = SimpleNamespace(version=1, content="v1", is_active=True)

        terms_repository = repository_factory(
            get_active_terms=AsyncMock(return_value=None),
            save_terms=AsyncMock(),
            create_terms=AsyncMock(return_value=created_terms),
        )
        terms_service = TermsService(terms_repository=terms_repository)

        version = await terms_service.update_terms_and_conditions("first terms")

        terms_repository.save_terms.assert_not_called()
        terms_repository.create_terms.assert_awaited_once_with("first terms")
        assert version == 1
