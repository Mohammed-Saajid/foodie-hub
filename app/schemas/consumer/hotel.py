from pydantic import BaseModel, Field


class HotelRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int = Field(..., description="Unique identifier for the hotel")
    name: str = Field(..., description="Name of the hotel")
    is_open: bool = Field(..., description="Whether the hotel is currently open")
    description: str = Field(default="", description="Description of the hotel")


class HotelListResponse(BaseModel):
    model_config = {"from_attributes": True}
    hotels: list[HotelRead] = Field(..., description="List of hotels")
    total: int = Field(..., description="Total number of hotels matching the criteria")


class MenuItemRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    hotel_id: int
    name: str
    description: str
    price: float
    is_available: bool


class HotelMenuRead(HotelRead):
    model_config = {"from_attributes": True}
    menu_items: list[MenuItemRead] = Field(
        ..., description="List of menu items available at the hotel"
    )
