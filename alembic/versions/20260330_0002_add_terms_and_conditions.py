"""Add terms and conditions table.

Revision ID: 20260330_0002
Revises: 20260327_0001
Create Date: 2026-03-30 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC


# revision identifiers, used by Alembic.
revision = "20260330_0002"
down_revision = "20260327_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create terms_and_conditions table
    op.create_table(
        "terms_and_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), sa.Identity(always=False, start=1, increment=1), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )
    op.create_index("ix_terms_and_conditions_version", "terms_and_conditions", ["version"])
    op.create_index("ix_terms_and_conditions_is_active", "terms_and_conditions", ["is_active"])

    terms_table = sa.table(
        "terms_and_conditions",
        sa.column("version", sa.Integer),
        sa.column("content", sa.Text),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        terms_table,
        [
            {
                "version": 1,
                "content": (
                    "Welcome to Foodie Hub. By using our platform, you agree to comply with "
                    "these terms and conditions. Please read them carefully."
                ),
                "is_active": True,
                "created_at": datetime.now(UTC),
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_terms_and_conditions_is_active", "terms_and_conditions")
    op.drop_index("ix_terms_and_conditions_version", "terms_and_conditions")
    op.drop_table("terms_and_conditions")
