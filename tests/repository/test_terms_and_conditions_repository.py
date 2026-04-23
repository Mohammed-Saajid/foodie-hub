import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.terms_and_conditions_repository import TermsAndConditionsRepository


@pytest.mark.asyncio
async def test_terms_and_conditions_repository(db_session: AsyncSession):
    repo = TermsAndConditionsRepository(db_session)

    # test create_terms
    terms = await repo.create_terms(content="Initial Terms")
    assert terms.id is not None
    assert terms.content == "Initial Terms"
    assert terms.is_active is True

    # test get_active_terms
    active_terms = await repo.get_active_terms()
    assert active_terms is not None
    assert active_terms.id == terms.id
    assert active_terms.content == "Initial Terms"

    # test get_terms_by_version
    version_terms = await repo.get_terms_by_version(terms.version)
    assert version_terms is not None
    assert version_terms.id == terms.id
    assert version_terms.version == terms.version

    # create new terms (deactivate old)
    terms.is_active = False
    await repo.save_terms(terms)

    new_terms = await repo.create_terms(content="Updated Terms")
    assert new_terms.is_active is True
    assert new_terms.id != terms.id

    # get active terms again
    latest_active_terms = await repo.get_active_terms()
    assert latest_active_terms is not None
    assert latest_active_terms.id == new_terms.id
    assert latest_active_terms.content == "Updated Terms"
