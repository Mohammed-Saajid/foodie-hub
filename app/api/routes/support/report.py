import logging

from fastapi import APIRouter, Body, Depends

from app.api.dependencies import get_report_service, require_roles_and_terms
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.services.support.report_service import ReportService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report")


@router.post("", response_model=MessageResponse)
async def submit_report(
    report_str: str = Body(
        min_length=3, max_length=1000, embed=True, description="Reason for reporting"
    ),
    current_user: User = Depends(
        require_roles_and_terms(UserRole.CONSUMER, UserRole.HOTEL_MANAGER, UserRole.DELIVERY),
    ),
    report_service: ReportService = Depends(get_report_service),
) -> MessageResponse:

    report = await report_service.create_report(user_id=current_user.id, reason=report_str)

    logger.info(f"New report submitted by user {current_user.id}. Report id: {report.id}")
    # Notify admins about new report
    return MessageResponse(message="Thank you for your report!")
