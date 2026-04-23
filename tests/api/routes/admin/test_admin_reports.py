from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class TestAdminReports:
    @pytest.mark.asyncio
    async def test_list_reports(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")
        reports = (
            [
                SimpleNamespace(
                    id=1,
                    reporter_id=1,
                    reason="Verbal Abuse",
                    status="open",
                    comment=None,
                    created_at=date(2023, 1, 1),
                )
            ],
            1,
        )

        report_service = service_factory(list_reports=AsyncMock(return_value=reports))

        override_dependencies(
            user=user,
            report_service=report_service,
        )

        response = await client.get("/admin/reports", params={"limit": 10, "offset": 0})

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_review_report(
        self,
        client: AsyncMock,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=1, role="admin")

        report_service = service_factory(
            review_report=AsyncMock(return_value=SimpleNamespace(status="dismissed"))
        )

        override_dependencies(
            user=user,
            report_service=report_service,
        )

        response = await client.patch(
            "/admin/reports/1/review", params={"dismiss": True, "comment": "Inappropriate content"}
        )
        print(response.json())
        assert response.status_code == 200
