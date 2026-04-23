from pydantic import BaseModel, Field

from app.schemas.auth.auth import UserRead


class UserProfileUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    email: str | None = Field(None, min_length=5, max_length=100)
    phone_number: str | None = Field(None, min_length=7, max_length=20)
    about_me: str | None = Field(None, max_length=500)
    profile_picture_url: str | None = Field(None, max_length=255)
    upi_screenshot_url: str | None = Field(None, max_length=255)


class FullUserRead(UserRead):
    model_config = {
        "from_attributes": True,
    }

    about_me: str | None = Field(None, description="A brief description about the user")
    profile_picture_url: str | None = Field(None, description="URL to the user's profile picture")
    upi_screenshot_url: str | None = Field(
        None, description="URL to the user's UPI screenshot for payments"
    )
