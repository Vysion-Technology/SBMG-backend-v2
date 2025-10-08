"""add_fcm_device_tokens

Revision ID: 13dc0a61a8bf
Revises: bc06aad033d7
Create Date: 2025-10-08 19:28:28.589262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13dc0a61a8bf'
down_revision: Union[str, Sequence[str], None] = 'bc06aad033d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_device_tokens table
    op.create_table(
        'user_device_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('fcm_token', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'device_id', name='uq_user_device')
    )
    
    # Create public_user_device_tokens table
    op.create_table(
        'public_user_device_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('public_user_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('fcm_token', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('platform', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['public_user_id'], ['public_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_user_id', 'device_id', name='uq_public_user_device')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('public_user_device_tokens')
    op.drop_table('user_device_tokens')
