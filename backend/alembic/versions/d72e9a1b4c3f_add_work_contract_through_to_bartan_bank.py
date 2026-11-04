"""add work_contract_through to bartan bank

Revision ID: d72e9a1b4c3f
Revises: f641b98a3e21
Create Date: 2026-11-04 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd72e9a1b4c3f'
down_revision: Union[str, Sequence[str], None] = 'f641b98a3e21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'survey_bartan_banks',
        sa.Column('work_contract_through', sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('survey_bartan_banks', 'work_contract_through')
