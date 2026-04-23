import logging

from fastapi import APIRouter, Body, Depends

from app.api.dependencies import get_feedback_service, require_roles_and_terms
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth.auth import MessageResponse
from app.services.support.feedback_service import FeedbackService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback")


@router.post("", response_model=MessageResponse)
async def submit_feedback(
    feedback_text: str = Body(
        min_length=3,
        max_length=1000,
        embed=True,
        alias="feedback",
        description="The feedback message from the user",
    ),
    current_user: User = Depends(
        require_roles_and_terms(UserRole.CONSUMER, UserRole.HOTEL_MANAGER, UserRole.DELIVERY),
    ),
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> MessageResponse:

    submitted_feedback = await feedback_service.submit_feedback(
        user_id=current_user.id, feedback_text=feedback_text
    )

    logger.info(
        f"New feedback submitted by user {current_user.id}. Feedback id: {submitted_feedback.id}"
    )
    # Notify admins about new feedback
    return MessageResponse(message="Thank you for your feedback!")
