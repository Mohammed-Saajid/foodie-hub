from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import ReportStatus


class ListReportsRequest(BaseModel):
    limit: int = Field(100, gt=0, le=1000, description="Number of reports to return (max 1000)")
    offset: int = Field(0, ge=0, description="Number of reports to skip for pagination")
    asc: bool = Field(
        True, description="Whether to sort reports in ascending order of creation time"
    )


class ReportRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    reporter_id: int
    reason: str
    status: ReportStatus
    comment: str | None
    created_at: date


class ListReportsResponse(BaseModel):
    model_config = {"from_attributes": True}
    reports: list[ReportRead] = Field(..., description="List of reports with details")
    total: int = Field(..., description="Total number of reports available")


class ReviewReportRequest(BaseModel):
    dismiss: bool = Field(..., description="Whether to dismiss the report")
    comment: str | None = Field(
        None, description="Optional comment from the admin regarding the review"
    )
