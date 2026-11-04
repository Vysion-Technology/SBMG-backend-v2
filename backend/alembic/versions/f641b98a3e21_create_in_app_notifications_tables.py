"""create in_app_notifications tables

Revision ID: f641b98a3e21
Revises: e520f672ebad
Create Date: 2026-11-04 22:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f641b98a3e21'
down_revision: Union[str, Sequence[str], None] = 'e520f672ebad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'in_app_notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('public_user_id', sa.Integer(), nullable=True),
        sa.Column('is_broadcast', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('target_audience', sa.String(length=50), server_default='ALL', nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('action_url', sa.String(length=255), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['public_user_id'], ['public_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['authority_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_in_app_notifications_category'), 'in_app_notifications', ['category'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_created_at'), 'in_app_notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_is_broadcast'), 'in_app_notifications', ['is_broadcast'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_is_read'), 'in_app_notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_public_user_id'), 'in_app_notifications', ['public_user_id'], unique=False)
    op.create_index(op.f('ix_in_app_notifications_user_id'), 'in_app_notifications', ['user_id'], unique=False)

    op.create_table(
        'in_app_notification_reads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('public_user_id', sa.Integer(), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['in_app_notifications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['public_user_id'], ['public_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['authority_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notification_id', 'public_user_id', name='uq_notif_read_public_user'),
        sa.UniqueConstraint('notification_id', 'user_id', name='uq_notif_read_user')
    )
    op.create_index(op.f('ix_in_app_notification_reads_notification_id'), 'in_app_notification_reads', ['notification_id'], unique=False)
    op.create_index(op.f('ix_in_app_notification_reads_public_user_id'), 'in_app_notification_reads', ['public_user_id'], unique=False)
    op.create_index(op.f('ix_in_app_notification_reads_user_id'), 'in_app_notification_reads', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_in_app_notification_reads_user_id'), table_name='in_app_notification_reads')
    op.drop_index(op.f('ix_in_app_notification_reads_public_user_id'), table_name='in_app_notification_reads')
    op.drop_index(op.f('ix_in_app_notification_reads_notification_id'), table_name='in_app_notification_reads')
    op.drop_table('in_app_notification_reads')
    op.drop_index(op.f('ix_in_app_notifications_user_id'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_public_user_id'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_is_read'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_is_broadcast'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_created_at'), table_name='in_app_notifications')
    op.drop_index(op.f('ix_in_app_notifications_category'), table_name='in_app_notifications')
    op.drop_table('in_app_notifications')
