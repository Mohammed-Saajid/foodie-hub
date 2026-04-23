from pydantic import BaseModel, Field

from app.models.enums import ReportStatus


class ReportCreateRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ReportUpdateRequest(BaseModel):
    id: int
    status: ReportStatus = Field(default=ReportStatus.OPEN)
    comment: str | None = Field(default=None, max_length=500)
    dismiss: bool = Field(default=False)


class ReportUpdateResponse(BaseModel):
    id: int
    status: ReportStatus
    comment: str | None = None
