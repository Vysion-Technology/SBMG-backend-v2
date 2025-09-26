"""complaint media constraint

Revision ID: 9b8edd20eb92
Revises: 3a2adc91e493
Create Date: 2025-09-26 16:58:12.796231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b8edd20eb92'
down_revision: Union[str, Sequence[str], None] = '3a2adc91e493'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### end Alembic commands ###
    op.add_column(
        "complaint_media",
        sa.Column("uploaded_by_public_mobile", sa.String(), nullable=True)
    )
    op.add_column(
        "complaint_media",
        sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True)
    )
    op.create_check_constraint(
        "uploaded_by_constraint",
        "complaint_media",
        "(uploaded_by_public_mobile IS NOT NULL) OR (uploaded_by_user_id IS NOT NULL)"
    )
    op.create_check_constraint(
        "uploaded_by_exclusivity_constraint",
        "complaint_media",
        "(uploaded_by_public_mobile IS NULL) OR (uploaded_by_user_id IS NULL)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # ### end Alembic commands ###
    op.drop_constraint("uploaded_by_exclusivity_constraint", "complaint_media", type_="check")
    op.drop_constraint("uploaded_by_constraint", "complaint_media", type_="check")
    op.drop_column("complaint_media", "uploaded_by_user_id")
    op.drop_column("complaint_media", "uploaded_by_public_mobile")