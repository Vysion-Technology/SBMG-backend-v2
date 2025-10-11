"""add_inspection_performance_indexes

Revision ID: d540cfe830f2
Revises: 098641a9fe51
Create Date: 2025-10-11 17:48:52.388669

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d540cfe830f2"
down_revision: Union[str, Sequence[str], None] = "098641a9fe51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for inspection analytics queries."""

    # Composite index on (village_id, date) for faster date-range queries
    op.create_index(
        "ix_inspections_village_id_date",
        "inspections",
        ["village_id", "date"],
        unique=False,
    )

    # Index on date alone for queries that aggregate across all villages
    op.create_index("ix_inspections_date", "inspections", ["date"], unique=False)


def downgrade() -> None:
    """Remove performance indexes."""

    op.drop_index("ix_inspections_village_id_date", table_name="inspections")
    op.drop_index("ix_inspections_date", table_name="inspections")
