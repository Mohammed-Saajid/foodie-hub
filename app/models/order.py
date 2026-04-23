from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import BidStatus, OrderStatus
from app.models.hotel import Hotel, MenuItem
from app.models.user import User


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consumer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    consumer: Mapped["User"] = relationship(
        "User", back_populates="orders", foreign_keys=[consumer_id]
    )
    hotel_id: Mapped[int | None] = mapped_column(ForeignKey("hotels.id"), nullable=True, index=True)
    hotel: Mapped["Hotel"] = relationship("Hotel", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.BIDDING,
        nullable=False,
        index=True,
    )
    delivery_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    delivery_user: Mapped["User"] = relationship("User", foreign_keys=[delivery_user_id])
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    delivery_otp: Mapped[str | None] = mapped_column(String(12), nullable=True)
    text_order: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_text_based: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    bids: Mapped[list["OrderBid"]] = relationship(
        "OrderBid",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem")


class OrderBid(Base):
    __tablename__ = "order_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", name="fk_order_bids_order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped["Order"] = relationship("Order", back_populates="bids", passive_deletes=True)
    delivery_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    delivery_user: Mapped["User"] = relationship("User", foreign_keys=[delivery_user_id])
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    upi_screenshot_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[BidStatus] = mapped_column(
        Enum(BidStatus), default=BidStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
