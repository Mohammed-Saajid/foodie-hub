from app.core.exceptions import ResourceNotFoundException
from app.models.enums import ReportStatus
from app.models.support import Report
from app.repositories.support_repository import ReportRepository


class ReportService:
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository

    async def list_reports(
        self, limit: int = 100, offset: int = 0, asc: bool = True
    ) -> tuple[list[Report], int]:
        # TODO: Add filtering and sorting capabilities as needed
        return await self.report_repository.list_reports(limit=limit, offset=offset, asc=asc)

    async def review_report(self, report_id: int, dismiss: bool, comment: str | None) -> Report:
        report = await self.report_repository.get_by_id(report_id)
        if not report:
            raise ResourceNotFoundException("Report not found", details={"report_id": report_id})
        report.status = ReportStatus.DISMISSED if dismiss else ReportStatus.REVIEWED
        report.comment = comment
        return await self.report_repository.save_report(report)

    async def get_report_by_id(self, report_id: int) -> Report:
        report = await self.report_repository.get_by_id(report_id)
        if not report:
            raise ResourceNotFoundException("Report not found", details={"report_id": report_id})
        return report

    async def create_report(self, user_id: int, reason: str) -> Report:
        report = Report(reporter_id=user_id, reason=reason)
        return await self.report_repository.save_report(report)
