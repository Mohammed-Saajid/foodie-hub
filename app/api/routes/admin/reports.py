import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Request

from app.api.dependencies import (
    get_report_service,
    require_roles_and_terms,
)
from app.models.enums import UserRole
from app.schemas.admin.reports import (
    ListReportsRequest,
    ListReportsResponse,
    ReportRead,
    ReviewReportRequest,
)
from app.schemas.auth.auth import CurrentUser, MessageResponse
from app.services.notifications.service import NotificationService
from app.services.support.report_service import ReportService


router = APIRouter(prefix="/reports")
logger = logging.getLogger(__name__)


async def _publish_report_review_notification(
    *,
    request: Request,
    report_id: int,
    reporter_id: int | None,
    dismissed: bool,
    comment: str | None,
    report_status: str,
) -> None:
    try:
        if reporter_id is None:
            return

        redis = getattr(request.app.state, "redis", None)
        if not redis:
            logger.warning(
                "Skipping report review notification for report_id=%s because Redis is unavailable",
                report_id,
            )
            return

        status_msg = "was dismissed" if dismissed else "has been reviewed"
        notification_service = NotificationService(redis)
        await notification_service.publish_to_user(
            user_id=reporter_id,
            event="report_reviewed",
            message=f"Your report #{report_id} {status_msg} by admins",
            data={"report_id": report_id, "status": report_status, "comment": comment},
        )
    except Exception:
        logger.exception("Failed to publish report review notification for report_id=%s", report_id)


@router.get("", response_model=ListReportsResponse)
async def list_reports(
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    report_service: ReportService = Depends(get_report_service),
    payload: ListReportsRequest = Depends(),
) -> ListReportsResponse:
    reports, total = await report_service.list_reports(
        limit=payload.limit, offset=payload.offset, asc=payload.asc
    )
    logger.info(f"Admin {user.id} listed reports, count: {total}")
    return ListReportsResponse(
        reports=[ReportRead.model_validate(report) for report in reports], total=total
    )


@router.patch("/{report_id}/review", response_model=MessageResponse)
async def review_report(
    background_tasks: BackgroundTasks,
    request: Request,
    report_id: int = Path(description="ID of the report to review", gt=0),
    payload: ReviewReportRequest = Depends(),
    user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    report_service: ReportService = Depends(get_report_service),
) -> MessageResponse:

    dismiss = payload.dismiss
    comment = payload.comment

    report = await report_service.review_report(report_id, dismiss, comment)
    background_tasks.add_task(
        _publish_report_review_notification,
        request=request,
        report_id=report_id,
        reporter_id=getattr(report, "reporter_id", None),
        dismissed=dismiss,
        comment=comment,
        report_status=getattr(report.status, "value", str(report.status)),
    )
    logger.info(f"Admin {user.id} reviewed report {report_id}, status: {report.status}")
    return MessageResponse(
        message=f"Report {report_id} has been {'dismissed' if dismiss else 'reviewed'} successfully"
    )
