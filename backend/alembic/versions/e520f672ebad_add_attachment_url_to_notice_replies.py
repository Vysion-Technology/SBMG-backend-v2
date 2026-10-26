"""add attachment_url to notice_replies

Revision ID: e520f672ebad
Revises: a4b3c0d17c7f
Create Date: 2026-10-26 12:00:03.564594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e520f672ebad'
down_revision: Union[str, Sequence[str], None] = 'a4b3c0d17c7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('notice_replies', sa.Column('attachment_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notice_replies', 'attachment_url')
