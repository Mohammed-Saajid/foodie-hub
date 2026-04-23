import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_feedback_service, require_roles_and_terms
from app.models.enums import UserRole
from app.schemas.admin.feedbacks import FeedbackRead, ListFeedbackResponse, ListFeedbacksRequest
from app.schemas.auth.auth import CurrentUser
from app.services.support.feedback_service import FeedbackService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedbacks")


@router.get("", response_model=ListFeedbackResponse)
async def list_feedbacks(
    current_user: CurrentUser = Depends(require_roles_and_terms(UserRole.ADMIN)),
    feedback_service: FeedbackService = Depends(get_feedback_service),
    payload: ListFeedbacksRequest = Depends(),
) -> ListFeedbackResponse:
    feedbacks, total = await feedback_service.list_feedbacks(
        payload.limit, payload.offset, payload.asc
    )
    logger.info(
        f"Admin {current_user.id} listed feedbacks with filters: {payload.model_dump_json()}"
    )
    return ListFeedbackResponse(
        feedbacks=[FeedbackRead.model_validate(feedback) for feedback in feedbacks],
        total=total,
    )
