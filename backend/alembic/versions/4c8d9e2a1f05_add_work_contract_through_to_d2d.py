"""add work_contract_through to d2d activities

Revision ID: 4c8d9e2a1f05
Revises: 1bca07e77b56
Create Date: 2026-10-13 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c8d9e2a1f05'
down_revision: Union[str, Sequence[str], None] = '1bca07e77b56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add work_contract_through column to survey_d2d_activities
    op.add_column(
        'survey_d2d_activities',
        sa.Column('work_contract_through', sa.String(length=50), nullable=True)
    )

    # Backfill existing rows based on which of the 5 fields was set
    op.execute("""
        UPDATE survey_d2d_activities
        SET work_contract_through = CASE
            WHEN (
                (CASE WHEN COALESCE(sanctioned_tender, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(sanctioned_self_gp, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(sanctioned_csr_ngo, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(sanctioned_shg, 0) > 0 THEN 1 ELSE 0 END) +
                (CASE WHEN COALESCE(sanctioned_mixed_model, 0) > 0 THEN 1 ELSE 0 END)
            ) > 1 THEN 'mixed_model'
            WHEN COALESCE(sanctioned_tender, 0) > 0 THEN 'tender'
            WHEN COALESCE(sanctioned_self_gp, 0) > 0 THEN 'self_gp'
            WHEN COALESCE(sanctioned_csr_ngo, 0) > 0 THEN 'csr_ngo'
            WHEN COALESCE(sanctioned_shg, 0) > 0 THEN 'shg'
            WHEN COALESCE(sanctioned_mixed_model, 0) > 0 THEN 'mixed_model'
            ELSE NULL
        END
        WHERE is_active = TRUE AND work_contract_through IS NULL
    """)

    # Ensure 0-1 mutual exclusivity for existing rows where contract mode is set
    op.execute("""
        UPDATE survey_d2d_activities
        SET 
            sanctioned_tender = CASE WHEN work_contract_through = 'tender' THEN 1 ELSE 0 END,
            sanctioned_self_gp = CASE WHEN work_contract_through = 'self_gp' THEN 1 ELSE 0 END,
            sanctioned_csr_ngo = CASE WHEN work_contract_through = 'csr_ngo' THEN 1 ELSE 0 END,
            sanctioned_shg = CASE WHEN work_contract_through = 'shg' THEN 1 ELSE 0 END,
            sanctioned_mixed_model = CASE WHEN work_contract_through = 'mixed_model' THEN 1 ELSE 0 END
        WHERE work_contract_through IS NOT NULL
    """)

    # Ensure clean state for inactive rows
    op.execute("""
        UPDATE survey_d2d_activities
        SET 
            work_contract_through = NULL,
            sanctioned_tender = 0,
            sanctioned_self_gp = 0,
            sanctioned_csr_ngo = 0,
            sanctioned_shg = 0,
            sanctioned_mixed_model = 0
        WHERE is_active = FALSE
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('survey_d2d_activities', 'work_contract_through')
