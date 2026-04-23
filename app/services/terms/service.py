from app.core.exceptions import ResourceNotFoundException
from app.models.terms import TermsAndConditions
from app.repositories.terms_and_conditions_repository import TermsAndConditionsRepository


class TermsService:
    def __init__(self, terms_repository: TermsAndConditionsRepository):
        self.terms_repository = terms_repository

    async def get_terms_and_conditions(self) -> TermsAndConditions:
        active_terms = await self.terms_repository.get_active_terms()
        if not active_terms:
            raise ResourceNotFoundException("Active terms and conditions not found")
        return active_terms

    async def update_terms_and_conditions(self, content: str) -> int:
        existing_terms = await self.terms_repository.get_active_terms()
        if existing_terms:
            existing_terms.is_active = False
            await self.terms_repository.save_terms(existing_terms)
        terms = await self.terms_repository.create_terms(content)
        return terms.version
