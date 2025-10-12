"""fix_district_batch_analytics_coverage

Revision ID: 5145124937a3
Revises: 7f808341d47f
Create Date: 2025-10-12 11:42:05.297311

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5145124937a3"
down_revision: Union[str, Sequence[str], None] = "7f808341d47f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix district batch analytics to calculate coverage based on villages, not blocks."""

    # Drop and recreate get_districts_inspection_analytics_batch with correct coverage
    op.execute(
        "DROP FUNCTION IF EXISTS get_districts_inspection_analytics_batch(INTEGER[], DATE, DATE);"
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION get_districts_inspection_analytics_batch(
        district_ids INTEGER[],
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        district_id INTEGER,
        total_blocks BIGINT,
        inspected_blocks BIGINT,
        total_gps BIGINT,
        inspected_gps BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            d.id as district_id,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) as inspected_blocks,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(AVG(COALESCE(block_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM unnest(district_ids) AS d(id)
        LEFT JOIN blocks b ON b.district_id = d.id
        LEFT JOIN villages gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                blocks.id as block_id,
                AVG(COALESCE(gp_scores.average_score, 0)) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks
            LEFT JOIN villages gp_inner ON blocks.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(COALESCE(village_scores.average_score, 0)) as average_score,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM villages v
                LEFT JOIN (
                    SELECT inspection_scores.village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                    GROUP BY inspection_scores.village_id
                ) village_scores ON v.id = village_scores.village_id
                GROUP BY v.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY blocks.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM villages v
            LEFT JOIN (
                SELECT inspection_scores.village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                GROUP BY inspection_scores.village_id
            ) village_scores ON v.id = village_scores.village_id
            GROUP BY v.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY d.id;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert district batch analytics to use block-based coverage."""

    # Drop and recreate with old coverage calculation
    op.execute(
        "DROP FUNCTION IF EXISTS get_districts_inspection_analytics_batch(INTEGER[], DATE, DATE);"
    )

    op.execute("""
    CREATE OR REPLACE FUNCTION get_districts_inspection_analytics_batch(
        district_ids INTEGER[],
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        district_id INTEGER,
        total_blocks BIGINT,
        inspected_blocks BIGINT,
        total_gps BIGINT,
        inspected_gps BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            d.id as district_id,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) as inspected_blocks,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(AVG(COALESCE(block_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) * 100.0) / NULLIF(COUNT(DISTINCT b.id), 0), 2) as coverage_percentage
        FROM unnest(district_ids) AS d(id)
        LEFT JOIN blocks b ON b.district_id = d.id
        LEFT JOIN villages gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                blocks.id as block_id,
                AVG(COALESCE(gp_scores.average_score, 0)) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks
            LEFT JOIN villages gp_inner ON blocks.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(COALESCE(village_scores.average_score, 0)) as average_score,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM villages v
                LEFT JOIN (
                    SELECT inspection_scores.village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                    GROUP BY inspection_scores.village_id
                ) village_scores ON v.id = village_scores.village_id
                GROUP BY v.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY blocks.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM villages v
            LEFT JOIN (
                SELECT inspection_scores.village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                GROUP BY inspection_scores.village_id
            ) village_scores ON v.id = village_scores.village_id
            GROUP BY v.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY d.id;
    END;
    $$ LANGUAGE plpgsql;
    """)
