from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import Departments, UserRole


if TYPE_CHECKING:
    from app.models.order import Order


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, index=True)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    department: Mapped[Departments] = mapped_column(Enum(Departments), nullable=False)
    register_number: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Maximum 3 active orders at a time for consumers, and 5 deliveries for delivery users
    active_orders_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    active_orders_for_delivery_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="consumer", foreign_keys="Order.consumer_id"
    )
    terms_version_accepted: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    about_me: Mapped[str | None] = mapped_column(String(500), nullable=True)
    upi_screenshot_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "active_orders_count >= 0 AND active_orders_count <= 3",
            name="check_active_orders_count_range",
        ),
        CheckConstraint(
            "active_orders_for_delivery_count >= 0 AND active_orders_for_delivery_count <= 5",
            name="check_active_orders_for_delivery_count_range",
        ),
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
