import re
from datetime import datetime

import phonenumbers
from better_profanity import profanity  # type: ignore[import-untyped]
from phonenumbers import NumberParseException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, field_validator

from app.models.enums import Departments, UserRole


profanity.load_censor_words()


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username, alphanumeric only",
        title="Username",
    )
    full_name: str = Field(
        min_length=2, max_length=120, description="User's full name", title="Full Name"
    )
    role: UserRole = Field(description="User role", title="Role")
    mobile_number: str = Field(
        min_length=8,
        max_length=20,
        description="Mobile number in E.164 format",
        title="Mobile Number",
    )
    department: Departments = Field(description="User's department", title="Department")
    register_number: str = Field(
        min_length=2, max_length=60, description="User's register number", title="Register Number"
    )
    email: EmailStr = Field(description="User's email address", title="Email")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password with at least 8 characters",
        title="Password",
    )

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        if not v:
            raise ValueError("Mobile number is required")
        try:
            parsed = phonenumbers.parse(v, "IN")
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid mobile number format")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException as err:
            raise ValueError("Invalid mobile number format") from err

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        if profanity.contains_profanity(v):
            raise ValueError("Username contains inappropriate language")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.replace(" ", "").isalpha():
            raise ValueError("Full name must contain only alphabetic characters and spaces")
        if profanity.contains_profanity(v):
            raise ValueError("Full name contains inappropriate language")
        return v

    @field_validator("register_number")
    @classmethod
    def validate_register_number(cls, v: str) -> str:
        if not v:
            raise ValueError("Register number is required")
        register_number_pattern = (
            r"^21222[2-6](?:0[1-9]|1[0-9]|2[0-5])(?:000[1-9]|00[1-9][0-9]|01[0-9]{2}|0200)$"
        )
        if not re.match(register_number_pattern, v):
            raise ValueError("Invalid register number format")
        return v


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="Username", title="Username")
    password: str = Field(min_length=8, max_length=128, description="Password", title="Password")


class ForgotPasswordRequest(BaseModel):
    username_or_email: str = Field(
        min_length=3,
        max_length=255,
        description="Username or email address",
        title="Username or Email",
    )

    @field_validator("username_or_email")
    @classmethod
    def validate_username_or_email(cls, v: str) -> str:
        if "@" in v:
            # Validate as email
            try:
                TypeAdapter(EmailStr).validate_python(v)
            except ValueError as err:
                raise ValueError("Invalid email address format") from err
        else:
            # Validate as username
            if not v.isalnum():
                raise ValueError("Username must be alphanumeric")
            if profanity.contains_profanity(v):
                raise ValueError("Username contains inappropriate language")
        return v


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TermsRead(BaseModel):
    version: str = Field(description="Terms version", title="Version")
    content: str = Field(description="Terms content", title="Content")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode

    id: int
    username: str
    full_name: str
    role: UserRole
    mobile_number: str
    department: Departments
    register_number: str
    email: EmailStr
    terms_accepted: bool
    terms_accepted_at: datetime | None = None


class AuthResponse(BaseModel):
    access_token: str = Field(description="JWT access token", title="Access Token")
    token_type: str = Field("bearer", description="Type of the token", title="Token Type")
    first_login_terms_required: bool = Field(
        description="Whether terms are required for first login", title="First Login Terms Required"
    )
    user: UserRead = Field(description="Authenticated user details", title="User")


class MessageResponse(BaseModel):
    message: str = Field(description="Response message", title="Message")


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode
    id: int = Field(description="User ID", title="ID")
    full_name: str = Field(description="Full name of the user", title="Full Name")
    role: UserRole = Field(description="User role", title="Role")
    is_active: bool = Field(description="Whether the user is active", title="Is Active")
    is_banned: bool = Field(description="Whether the user is banned", title="Is Banned")
    terms_accepted: bool = Field(
        description="Whether the user has accepted terms", title="Terms Accepted"
    )
