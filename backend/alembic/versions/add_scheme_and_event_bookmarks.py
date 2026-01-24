"""Add scheme and event bookmarks

Revision ID: bookmark_001
Revises: 3cb1dee2532a
Create Date: 2026-01-24 10:52:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bookmark_001"
down_revision: Union[str, Sequence[str], None] = "3cb1dee2532a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create scheme_bookmarks table
    op.create_table(
        "scheme_bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheme_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["scheme_id"], ["schemes.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["authority_users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scheme_id", "user_id", name="uix_scheme_user_bookmark"),
    )
    op.create_index(op.f("ix_scheme_bookmarks_id"), "scheme_bookmarks", ["id"], unique=False)
    op.create_index(op.f("ix_scheme_bookmarks_scheme_id"), "scheme_bookmarks", ["scheme_id"], unique=False)
    op.create_index(op.f("ix_scheme_bookmarks_user_id"), "scheme_bookmarks", ["user_id"], unique=False)

    # Create event_bookmarks table
    op.create_table(
        "event_bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["authority_users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uix_event_user_bookmark"),
    )
    op.create_index(op.f("ix_event_bookmarks_id"), "event_bookmarks", ["id"], unique=False)
    op.create_index(op.f("ix_event_bookmarks_event_id"), "event_bookmarks", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_bookmarks_user_id"), "event_bookmarks", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop event_bookmarks table
    op.drop_index(op.f("ix_event_bookmarks_user_id"), table_name="event_bookmarks")
    op.drop_index(op.f("ix_event_bookmarks_event_id"), table_name="event_bookmarks")
    op.drop_index(op.f("ix_event_bookmarks_id"), table_name="event_bookmarks")
    op.drop_table("event_bookmarks")

    # Drop scheme_bookmarks table
    op.drop_index(op.f("ix_scheme_bookmarks_user_id"), table_name="scheme_bookmarks")
    op.drop_index(op.f("ix_scheme_bookmarks_scheme_id"), table_name="scheme_bookmarks")
    op.drop_index(op.f("ix_scheme_bookmarks_id"), table_name="scheme_bookmarks")
    op.drop_table("scheme_bookmarks")
