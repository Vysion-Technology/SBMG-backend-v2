"""contractor freq and order amount

Revision ID: b1d34efc3126
Revises: bookmark_001
Create Date: 2026-01-26 12:56:10.546966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1d34efc3126'
down_revision: Union[str, Sequence[str], None] = 'bookmark_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first in PostgreSQL
    contractor_frequency_enum = postgresql.ENUM(
        'DAILY', 'ONCE_IN_THREE_DAYS', 'WEEKLY', 'MONTHLY',
        name='contractorfrequency',
        create_type=False
    )
    contractor_frequency_enum.create(op.get_bind(), checkfirst=True)
    
    # Add the columns
    op.add_column('contractors', sa.Column(
        'contract_frequency',
        sa.Enum('DAILY', 'ONCE_IN_THREE_DAYS', 'WEEKLY', 'MONTHLY', name='contractorfrequency'),
        server_default='DAILY',
        nullable=False
    ))
    op.add_column('contractors', sa.Column('contract_amount', sa.Float(), server_default='0.0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the columns
    op.drop_column('contractors', 'contract_amount')
    op.drop_column('contractors', 'contract_frequency')
    
    # Drop the enum type
    contractor_frequency_enum = postgresql.ENUM(name='contractorfrequency')
    contractor_frequency_enum.drop(op.get_bind(), checkfirst=True)

