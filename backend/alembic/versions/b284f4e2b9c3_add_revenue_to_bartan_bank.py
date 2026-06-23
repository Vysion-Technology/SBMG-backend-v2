"""add_revenue_to_bartan_bank

Revision ID: b284f4e2b9c3
Revises: c283f3e1a8a2
Create Date: 2026-06-23 20:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b284f4e2b9c3'
down_revision: Union[str, Sequence[str], None] = 'c283f3e1a8a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('survey_bartan_banks', sa.Column('revenue', sa.Numeric(precision=15, scale=2), server_default='0.0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('survey_bartan_banks', 'revenue')
