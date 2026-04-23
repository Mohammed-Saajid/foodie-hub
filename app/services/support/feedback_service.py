from app.core.exceptions import ResourceNotFoundException
from app.models.support import Feedback
from app.repositories.support_repository import FeedbackRepository


class FeedbackService:
    def __init__(self, feedback_repository: FeedbackRepository):
        self.feedback_repository = feedback_repository

    async def submit_feedback(self, user_id: int, feedback_text: str) -> Feedback:
        feedback = Feedback(user_id=user_id, feedback=feedback_text)
        return await self.feedback_repository.create_feedback(feedback)

    async def list_feedbacks(
        self, limit: int = 100, offset: int = 0, asc: bool = True
    ) -> tuple[list[Feedback], int]:
        feedbacks, total = await self.feedback_repository.list_feedbacks(limit, offset, asc)
        return feedbacks, total

    async def get_feedback_by_id(self, feedback_id: int) -> Feedback:
        feedback = await self.feedback_repository.get_feedback_by_id(feedback_id)
        if not feedback:
            raise ResourceNotFoundException("Feedback not found")
        return feedback
