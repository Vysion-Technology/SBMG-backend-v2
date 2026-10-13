"""add surveyor details and work order end date

Revision ID: 1bca07e77b56
Revises: 9a4f2c8d1e3b
Create Date: 2026-09-29 13:18:16.316571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1bca07e77b56'
down_revision: Union[str, Sequence[str], None] = '9a4f2c8d1e3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add surveyor details to annual_surveys
    op.add_column('annual_surveys', sa.Column('surveyor_name', sa.String(length=255), nullable=True))
    op.add_column('annual_surveys', sa.Column('surveyor_post', sa.String(length=255), nullable=True))
    op.add_column('annual_surveys', sa.Column('surveyor_contact', sa.String(length=20), nullable=True))

    # Add work_order_end_date to survey_work_order_details
    op.add_column('survey_work_order_details', sa.Column('work_order_end_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('survey_work_order_details', 'work_order_end_date')
    op.drop_column('annual_surveys', 'surveyor_contact')
    op.drop_column('annual_surveys', 'surveyor_post')
    op.drop_column('annual_surveys', 'surveyor_name')
