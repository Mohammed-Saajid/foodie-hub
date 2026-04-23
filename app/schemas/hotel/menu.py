from pydantic import BaseModel, Field


class MenuItemCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)
    price: float = Field(gt=0)
    is_available: bool = True


class MenuItemUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, gt=0)
    is_available: bool | None = None


class MenuItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    hotel_id: int
    name: str
    description: str
    price: float
    is_available: bool
