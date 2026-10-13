"""add profile_updated_at to authority_users

Revision ID: 9a4f2c8d1e3b
Revises: fe16f348632b
Create Date: 2026-09-10 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a4f2c8d1e3b'
down_revision: Union[str, Sequence[str], None] = 'fe16f348632b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add profile_updated_at column as nullable
    op.add_column(
        'authority_users',
        sa.Column('profile_updated_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # 2. Backfill existing authority users to now() - 2 months so they are prompted to update
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("UPDATE authority_users SET profile_updated_at = now() - INTERVAL '2 months'")
    else:
        op.execute("UPDATE authority_users SET profile_updated_at = datetime('now', '-2 months')")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('authority_users', 'profile_updated_at')
