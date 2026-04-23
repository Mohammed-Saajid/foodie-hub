import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Departments, ReportStatus, UserRole
from app.models.support import Feedback, Report
from app.models.user import User
from app.repositories.support_repository import FeedbackRepository, ReportRepository


async def create_test_user(db_session: AsyncSession, prefix: str) -> User:
    p = prefix[:4]
    user = User(
        username=f"{prefix}_su",
        email=f"{prefix}@example.com",
        hashed_password="password",
        role=UserRole.CONSUMER,
        full_name=f"{prefix} Name",
        mobile_number=f"5{p}{len(prefix)}",
        department=Departments.CSE,
        register_number=f"SU{p}",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_report_repository(db_session: AsyncSession):
    repo = ReportRepository(db_session)
    user = await create_test_user(db_session, "rprep")

    # test save_report (create)
    report = Report(
        reporter_id=user.id,
        reason="Test report reason",
        status=ReportStatus.OPEN,
        comment="Test comment",
    )

    saved_report = await repo.save_report(report)
    assert saved_report.id is not None
    assert saved_report.reason == "Test report reason"

    # test get_by_id
    fetched_report = await repo.get_by_id(saved_report.id)
    assert fetched_report is not None
    assert fetched_report.id == saved_report.id

    # Add another report
    user2 = await create_test_user(db_session, "rprep2")
    report2 = Report(reporter_id=user2.id, reason="Second issue", status=ReportStatus.DISMISSED)
    await repo.save_report(report2)

    # test list_reports (asc and desc)
    reports_asc, total_asc = await repo.list_reports(asc=True)
    assert total_asc >= 2
    assert len(reports_asc) >= 2
    assert reports_asc[0].created_at <= reports_asc[-1].created_at

    reports_desc, total_desc = await repo.list_reports(asc=False)
    assert total_desc == total_asc
    assert reports_desc[0].created_at >= reports_desc[-1].created_at

    # test pagination
    reports_paginated, _ = await repo.list_reports(limit=1, offset=0)
    assert len(reports_paginated) == 1


@pytest.mark.asyncio
async def test_feedback_repository(db_session: AsyncSession):
    repo = FeedbackRepository(db_session)
    user = await create_test_user(db_session, "fbrep")

    # test create_feedback
    feedback = Feedback(user_id=user.id, feedback="Great app!")
    saved_feedback = await repo.create_feedback(feedback)
    assert saved_feedback.id is not None
    assert saved_feedback.feedback == "Great app!"

    user2 = await create_test_user(db_session, "fbrep2")
    feedback2 = Feedback(user_id=user2.id, feedback="Could be better")
    await repo.create_feedback(feedback2)

    # test list_feedbacks (asc and desc)
    feedbacks_asc, total_asc = await repo.list_feedbacks(asc=True)
    assert total_asc >= 2
    assert len(feedbacks_asc) >= 2
    assert feedbacks_asc[0].created_at <= feedbacks_asc[-1].created_at

    feedbacks_desc, total_desc = await repo.list_feedbacks(asc=False)
    assert total_desc == total_asc
    assert feedbacks_desc[0].created_at >= feedbacks_desc[-1].created_at

    # test pagination
    feedbacks_paginated, _ = await repo.list_feedbacks(limit=1, offset=0)
    assert len(feedbacks_paginated) == 1
