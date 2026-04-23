from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.services.support.report_service import ReportService


@pytest.mark.asyncio
async def test_list_reports(repository_factory, service_factory):
    # Arrange
    reports = [SimpleNamespace(id=1, reason="Reason 1"), SimpleNamespace(id=2, reason="Reason 2")]
    report_repository = repository_factory(list_reports=AsyncMock(return_value=reports))
    report_service = ReportService(report_repository=report_repository)

    # Act
    result = await report_service.list_reports()
    # Assert
    assert result == reports


@pytest.mark.asyncio
async def test_review_report(repository_factory, service_factory):
    # Arrange
    report = SimpleNamespace(id=1, reason="Reason 1", status=None, comment=None)
    report_repository = repository_factory(
        get_by_id=AsyncMock(return_value=report), save_report=AsyncMock(return_value=report)
    )
    report_service = ReportService(report_repository=report_repository)

    # Act
    result = await report_service.review_report(report_id=1, dismiss=True, comment="Dismissed")

    # Assert
    assert result.status == "dismissed"
    assert result.comment == "Dismissed"


@pytest.mark.asyncio
async def test_review_report_not_found(repository_factory, service_factory):
    # Arrange
    report_repository = repository_factory(get_by_id=AsyncMock(return_value=None))
    report_service = ReportService(report_repository=report_repository)

    # Act & Assert
    with pytest.raises(ResourceNotFoundException):
        await report_service.review_report(report_id=999, dismiss=True, comment="Dismissed")


@pytest.mark.asyncio
async def test_get_report_by_id(repository_factory, service_factory):
    # Arrange
    report = SimpleNamespace(id=1, reason="Reason 1")
    report_repository = repository_factory(get_by_id=AsyncMock(return_value=report))
    report_service = ReportService(report_repository=report_repository)

    # Act
    result = await report_service.get_report_by_id(report_id=1)

    # Assert
    assert result == report


@pytest.mark.asyncio
async def test_get_report_by_id_not_found(repository_factory, service_factory):
    # Arrange
    report_repository = repository_factory(get_by_id=AsyncMock(return_value=None))
    report_service = ReportService(report_repository=report_repository)

    # Act & Assert
    with pytest.raises(ResourceNotFoundException):
        await report_service.get_report_by_id(report_id=999)


@pytest.mark.asyncio
async def test_create_report(repository_factory, service_factory):
    # Arrange
    report = SimpleNamespace(id=1, user_id=1, reason="Inappropriate content")
    report_repository = repository_factory(save_report=AsyncMock(return_value=report))
    report_service = ReportService(report_repository=report_repository)

    # Act
    result = await report_service.create_report(user_id=1, reason="Inappropriate content")

    # Assert
    assert result == report
