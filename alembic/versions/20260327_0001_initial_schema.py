"""initial schema

Revision ID: 20260327_0001
Revises: 
Create Date: 2026-03-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260327_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum("CONSUMER", "DELIVERY", "HOTEL_MANAGER", "ADMIN", name="userrole", native_enum=False)
order_status_enum = sa.Enum(
    "CREATED",
    "BIDDING",
    "BID_ACCEPTED",
    "PREPARING",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "CANCELED",
    name="orderstatus",
    native_enum=False,
)
bid_status_enum = sa.Enum("PENDING", "ACCEPTED", "REJECTED", name="bidstatus", native_enum=False)
report_status_enum = sa.Enum("OPEN", "REVIEWED", "DISMISSED", name="reportstatus", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("mobile_number", sa.String(length=20), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("register_number", sa.String(length=60), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terms_version_accepted", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"])

    op.create_table(
        "hotels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_hotels_manager_id", "hotels", ["manager_id"])

    op.create_table(
        "menu_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hotel_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_menu_items_hotel_id", "menu_items", ["hotel_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consumer_id", sa.Integer(), nullable=False),
        sa.Column("hotel_id", sa.Integer(), nullable=False),
        sa.Column("status", order_status_enum, nullable=False),
        sa.Column("selected_bid_id", sa.Integer(), nullable=True),
        sa.Column("delivery_user_id", sa.Integer(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("delivery_otp", sa.String(length=12), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["consumer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"]),
        sa.ForeignKeyConstraint(["delivery_user_id"], ["users.id"]),
    )
    op.create_index("ix_orders_consumer_id", "orders", ["consumer_id"])
    op.create_index("ix_orders_hotel_id", "orders", ["hotel_id"])
    op.create_index("ix_orders_delivery_user_id", "orders", ["delivery_user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "order_bids",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("delivery_user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("upi_screenshot_url", sa.String(length=500), nullable=False),
        sa.Column("status", bid_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["delivery_user_id"], ["users.id"]),
    )
    op.create_index("ix_order_bids_order_id", "order_bids", ["order_id"])
    op.create_index("ix_order_bids_delivery_user_id", "order_bids", ["delivery_user_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("menu_item_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"]),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "discussion_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("channel_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_discussion_messages_user_id", "discussion_messages", ["user_id"])
    op.create_index("ix_discussion_messages_channel_date", "discussion_messages", ["channel_date"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", report_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["discussion_messages.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_message_id", "reports", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_message_id", table_name="reports")
    op.drop_index("ix_reports_reporter_id", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_discussion_messages_channel_date", table_name="discussion_messages")
    op.drop_index("ix_discussion_messages_user_id", table_name="discussion_messages")
    op.drop_table("discussion_messages")

    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_table("order_items")

    op.drop_index("ix_order_bids_delivery_user_id", table_name="order_bids")
    op.drop_index("ix_order_bids_order_id", table_name="order_bids")
    op.drop_table("order_bids")

    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_delivery_user_id", table_name="orders")
    op.drop_index("ix_orders_hotel_id", table_name="orders")
    op.drop_index("ix_orders_consumer_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_menu_items_hotel_id", table_name="menu_items")
    op.drop_table("menu_items")

    op.drop_index("ix_hotels_manager_id", table_name="hotels")
    op.drop_table("hotels")

    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
