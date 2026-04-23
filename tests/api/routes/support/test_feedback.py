from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestFeedback:
    @pytest.mark.asyncio
    async def test_submit_feedback(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        feedback = SimpleNamespace(
            id=1, user_id=1, message="Great service!", created_at=datetime.now()
        )

        feedback_service = service_factory(submit_feedback=AsyncMock(return_value=feedback))

        override_dependencies(
            user=user,
            feedback_service=feedback_service,
        )

        payload = {"feedback": "Great service!"}

        response = await client.post("/support/feedback", json=payload)

        assert response.status_code == 200
