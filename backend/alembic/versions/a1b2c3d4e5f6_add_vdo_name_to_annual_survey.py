"""Add vdo_name to AnnualSurvey

Revision ID: a1b2c3d4e5f6
Revises: 890c658e3b42
Create Date: 2026-02-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '890c658e3b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('annual_surveys', sa.Column('vdo_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('annual_surveys', 'vdo_name')
