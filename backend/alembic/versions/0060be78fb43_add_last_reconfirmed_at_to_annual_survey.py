"""add last_reconfirmed_at to annual_survey

Revision ID: 0060be78fb43
Revises: 7d066c6ff805
Create Date: 2026-06-15 22:00:50.040259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0060be78fb43'
down_revision: Union[str, Sequence[str], None] = '7d066c6ff805'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add the column as nullable first
    op.add_column('annual_surveys', sa.Column('last_reconfirmed_at', sa.DateTime(timezone=True), nullable=True))
    
    # 2. Backfill data from updated_at
    op.execute("UPDATE annual_surveys SET last_reconfirmed_at = updated_at")
    
    # 3. For any records where updated_at might be null (though unlikely), use now()
    op.execute("UPDATE annual_surveys SET last_reconfirmed_at = now() WHERE last_reconfirmed_at IS NULL")
    
    # 4. Set the column to non-nullable
    op.alter_column('annual_surveys', 'last_reconfirmed_at', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('annual_surveys', 'last_reconfirmed_at')
