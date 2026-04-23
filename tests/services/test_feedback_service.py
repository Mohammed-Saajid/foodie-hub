from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.services.support.feedback_service import FeedbackService


@pytest.mark.asyncio
async def test_submit_feedback(service_factory, repository_factory):
    feedback_repository = repository_factory(
        create_feedback=AsyncMock(
            return_value=SimpleNamespace(id=1, user_id=1, feedback="Great service!")
        )
    )

    feedback_service = FeedbackService(feedback_repository=feedback_repository)

    feedback = await feedback_service.submit_feedback(user_id=1, feedback_text="Great service!")

    assert feedback.id == 1
    assert feedback.user_id == 1
    assert feedback.feedback == "Great service!"
    feedback_repository.create_feedback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_feedbacks(service_factory, repository_factory):
    feedback_repository = repository_factory(
        list_feedbacks=AsyncMock(
            return_value=([SimpleNamespace(id=1, user_id=1, feedback="Great service!")], 1)
        )
    )

    feedback_service = FeedbackService(feedback_repository=feedback_repository)

    feedbacks, total = await feedback_service.list_feedbacks(limit=10, offset=0, asc=True)

    assert total == 1
    assert len(feedbacks) == 1
    assert feedbacks[0].id == 1
    assert feedbacks[0].user_id == 1
    assert feedbacks[0].feedback == "Great service!"
    feedback_repository.list_feedbacks.assert_awaited_once_with(10, 0, True)


@pytest.mark.asyncio
async def test_get_feedback_by_id(service_factory, repository_factory):
    feedback_repository = repository_factory(
        get_feedback_by_id=AsyncMock(
            return_value=SimpleNamespace(id=1, user_id=1, feedback="Great service!")
        )
    )

    feedback_service = FeedbackService(feedback_repository=feedback_repository)

    feedback = await feedback_service.get_feedback_by_id(feedback_id=1)

    assert feedback.id == 1
    assert feedback.user_id == 1
    assert feedback.feedback == "Great service!"
    feedback_repository.get_feedback_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_feedback_by_id_not_found(service_factory, repository_factory):
    feedback_repository = repository_factory(get_feedback_by_id=AsyncMock(return_value=None))

    feedback_service = FeedbackService(feedback_repository=feedback_repository)

    with pytest.raises(ResourceNotFoundException):
        await feedback_service.get_feedback_by_id(feedback_id=999)

    feedback_repository.get_feedback_by_id.assert_awaited_once_with(999)
