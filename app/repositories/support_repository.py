from sqlalchemy import asc as sql_asc, desc as sql_desc, func, select

from app.models.support import Feedback, Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    async def get_by_id(self, report_id: int) -> Report | None:
        result = await self.db.scalars(select(Report).where(Report.id == report_id))
        return result.first()

    async def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        asc: bool = True,
    ) -> tuple[list[Report], int]:

        # Safety limit
        limit = min(limit, 1000)

        # Build query
        query = select(Report).order_by(
            sql_asc(Report.created_at) if asc else sql_desc(Report.created_at)
        )

        # Count query
        count_query = select(func.count()).select_from(Report)
        total = await self.db.scalar(count_query) or 0

        # Pagination
        query = query.offset(offset).limit(limit)

        # Execute
        result = await self.db.scalars(query)
        reports = list(result.all())

        return reports, total

    async def save_report(self, report: Report) -> Report:
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report


class FeedbackRepository(BaseRepository):
    async def create_feedback(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback

    async def list_feedbacks(
        self,
        limit: int = 100,
        offset: int = 0,
        asc: bool = True,
    ) -> tuple[list[Feedback], int]:

        # Safety limit
        limit = min(limit, 1000)

        # Build query
        query = select(Feedback).order_by(
            sql_asc(Feedback.created_at) if asc else sql_desc(Feedback.created_at)
        )

        # Count query
        count_query = select(func.count()).select_from(Feedback)
        total = await self.db.scalar(count_query) or 0

        # Pagination
        query = query.offset(offset).limit(limit)

        # Execute
        result = await self.db.scalars(query)
        feedbacks = list(result.all())

        return feedbacks, total

    async def get_feedback_by_id(self, feedback_id: int) -> Feedback | None:
        result = await self.db.scalars(select(Feedback).where(Feedback.id == feedback_id))
        return result.first()
