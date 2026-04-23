"""Add text-based order support.

Revision ID: 20260330_0003
Revises: 20260330_0002
Create Date: 2026-03-30 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260330_0003"
down_revision = "20260330_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hotel_id nullable to support text-based orders
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "hotel_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
    
    # Add new columns for text-based orders
    op.add_column("orders", sa.Column("text_order", sa.String(1000), nullable=True))
    op.add_column(
        "orders",
        sa.Column("is_text_based", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    # Remove text-based order columns
    op.drop_column("orders", "is_text_based")
    op.drop_column("orders", "text_order")
    
    # Make hotel_id non-nullable again
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "hotel_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
