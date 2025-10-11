"""fix_ambiguous_column_reference_in_village_analytics

Revision ID: 121fca98e2d6
Revises: 7ed5dd5c6744
Create Date: 2025-10-11 17:07:08.704391

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "121fca98e2d6"
down_revision: Union[str, Sequence[str], None] = "7ed5dd5c6744"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix ambiguous column reference in get_village_inspection_analytics."""

    # Drop and recreate the function with explicit table qualification
    op.execute(
        "DROP FUNCTION IF EXISTS get_village_inspection_analytics(INTEGER, DATE, DATE);"
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION get_village_inspection_analytics(
        village_id_param INTEGER,
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        village_id INTEGER,
        total_inspections BIGINT,
        average_score DECIMAL(5,2),
        latest_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            village_id_param,
            COUNT(*) as total_inspections,
            ROUND(AVG(overall_score), 2) as average_score,
            MAX(overall_score) as latest_score,
            100.0 as coverage_percentage
        FROM inspection_scores
        WHERE inspection_scores.village_id = village_id_param
        AND (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
        AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param);
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to previous version with ambiguous reference."""

    op.execute(
        "DROP FUNCTION IF EXISTS get_village_inspection_analytics(INTEGER, DATE, DATE);"
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION get_village_inspection_analytics(
        village_id_param INTEGER,
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        village_id INTEGER,
        total_inspections BIGINT,
        average_score DECIMAL(5,2),
        latest_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            village_id_param,
            COUNT(*) as total_inspections,
            ROUND(AVG(overall_score), 2) as average_score,
            MAX(overall_score) as latest_score,
            100.0 as coverage_percentage
        FROM inspection_scores
        WHERE village_id = village_id_param
        AND (start_date_param IS NULL OR date >= start_date_param)
        AND (end_date_param IS NULL OR date <= end_date_param);
    END;
    $$ LANGUAGE plpgsql;
    """)
