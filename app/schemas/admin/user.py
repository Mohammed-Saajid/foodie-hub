from pydantic import BaseModel, EmailStr, Field

from app.models.enums import Departments, UserRole
from app.schemas.auth.auth import UserRead


class ListUsersRequest(BaseModel):
    limit: int = Field(10, description="Number of users to return")
    offset: int = Field(0, description="Number of users to skip")
    username: str | None = Field(None, description="Filter by username (partial match)")
    full_name: str | None = Field(None, description="Filter by full name (partial match)")
    role: UserRole | None = Field(None, description="Filter by user role")
    mobile_number: str | None = Field(None, description="Filter by mobile number (partial match)")
    department: Departments | None = Field(None, description="Filter by department")
    register_number: str | None = Field(
        None, description="Filter by register number (partial match)"
    )
    email: EmailStr | None = Field(None, description="Filter by email (partial match)")
    is_active: bool | None = Field(None, description="Filter by active status")
    is_banned: bool | None = Field(None, description="Filter by banned status")
    terms_accepted: bool | None = Field(None, description="Filter by terms acceptance")


class ListUsersResponse(BaseModel):
    users: list[UserRead] = Field(..., description="List of users matching the criteria")
    total: int
