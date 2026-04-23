from pydantic import BaseModel, Field


class HotelCreateRequest(BaseModel):
    model_config = {"from_attributes": True}
    name: str = Field(description="Name of the hotel")
    description: str | None = Field(default="", description="Hotel description")


class HotelRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    manager_id: int
    description: str
    is_open: bool
