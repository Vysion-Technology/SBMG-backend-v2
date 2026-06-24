"""change_work_frequency_none_to_daily

Revision ID: c283f3e1a8a2
Revises: a6828fa9b4f1
Create Date: 2026-06-23 20:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c283f3e1a8a2'
down_revision: Union[str, Sequence[str], None] = 'a6828fa9b4f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Rename enum value 'none' to 'daily' in postgres type
    op.execute("ALTER TYPE work_frequency RENAME VALUE 'none' TO 'daily'")
    
    # 2. Make work_frequency column nullable and drop its default value
    op.alter_column('survey_d2d_activities', 'work_frequency',
               existing_type=sa.Enum('daily', 'weekly', '15 days', 'monthly', name='work_frequency'),
               nullable=True,
               server_default=None)
               
    # 3. Update existing inactive D2D activities to have NULL frequency
    op.execute("UPDATE survey_d2d_activities SET work_frequency = NULL WHERE is_active = false")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Re-populate any NULL work_frequency values to 'daily' so they can be set to NOT NULL
    op.execute("UPDATE survey_d2d_activities SET work_frequency = 'daily' WHERE work_frequency IS NULL")
    
    # 2. Rename enum value 'daily' back to 'none'
    op.execute("ALTER TYPE work_frequency RENAME VALUE 'daily' TO 'none'")
    
    # 3. Re-add DEFAULT 'none' and NOT NULL constraint to work_frequency
    op.alter_column('survey_d2d_activities', 'work_frequency',
               existing_type=sa.Enum('none', 'weekly', '15 days', 'monthly', name='work_frequency'),
               nullable=False,
               server_default='none')
