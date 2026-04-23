from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestReport:
    @pytest.mark.asyncio
    async def test_submit_report(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="consumer")
        report = SimpleNamespace(
            id=1,
            reporter_id=1,
            reason="Inappropriate content",
            status="open",
            comment=None,
            created_at=datetime.now(),
        )

        report_service = service_factory(submit_report=AsyncMock(return_value=report))

        override_dependencies(
            user=user,
            report_service=report_service,
        )

        payload = {"report_str": "Inappropriate content"}

        response = await client.post("/support/report", json=payload)

        assert response.status_code == 200
