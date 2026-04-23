from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int = Field(..., description="Unique identifier for the feedback")
    user_id: int = Field(..., description="ID of the user who submitted the feedback")
    feedback: str = Field(..., description="The feedback text provided by the user")
    created_at: datetime = Field(..., description="Timestamp when the feedback was created")


class ListFeedbacksRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    asc: bool = Field(default=True)


class ListFeedbackResponse(BaseModel):
    feedbacks: list[FeedbackRead] = Field(..., description="List of feedback entries")
    total: int = Field(..., description="Total number of feedback entries available")
