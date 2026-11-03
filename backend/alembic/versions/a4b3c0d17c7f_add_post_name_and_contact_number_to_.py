"""add post, name and contact_number to inspections

Revision ID: a4b3c0d17c7f
Revises: 4c8d9e2a1f05
Create Date: 2026-10-22 12:54:45.010579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b3c0d17c7f'
down_revision: Union[str, Sequence[str], None] = '4c8d9e2a1f05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('inspections', sa.Column('post', sa.String(length=100), nullable=True))
    op.add_column('inspections', sa.Column('name', sa.String(length=100), nullable=True))
    op.add_column('inspections', sa.Column('contact_number', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('inspections', 'contact_number')
    op.drop_column('inspections', 'name')
    op.drop_column('inspections', 'post')
