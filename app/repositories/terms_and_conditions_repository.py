from sqlalchemy import func, select

from app.models.terms import TermsAndConditions
from app.repositories.base import BaseRepository


class TermsAndConditionsRepository(BaseRepository):
    async def get_active_terms(self) -> TermsAndConditions | None:
        result = await self.db.execute(
            select(TermsAndConditions).where(TermsAndConditions.is_active)
        )
        return result.scalars().first()

    async def create_terms(self, content: str) -> TermsAndConditions:
        result = await self.db.execute(select(func.max(TermsAndConditions.version)))
        latest_version = result.scalar_one_or_none() or 0

        new_terms = TermsAndConditions(
            version=latest_version + 1,
            content=content,
            is_active=True,
        )
        self.db.add(new_terms)
        await self.db.flush()
        await self.db.refresh(new_terms)
        return new_terms

    async def get_terms_by_version(self, version: int) -> TermsAndConditions | None:
        result = await self.db.execute(
            select(TermsAndConditions).where(TermsAndConditions.version == version)
        )
        return result.scalars().first()

    async def save_terms(self, terms: TermsAndConditions) -> TermsAndConditions:
        self.db.add(terms)
        await self.db.flush()
        await self.db.refresh(terms)
        return terms
