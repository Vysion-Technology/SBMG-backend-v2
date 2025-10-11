"""add_batch_inspection_analytics_functions

Revision ID: 098641a9fe51
Revises: 121fca98e2d6
Create Date: 2025-10-11 17:46:17.224711

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "098641a9fe51"
down_revision: Union[str, Sequence[str], None] = "121fca98e2d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add batch analytics functions for better performance."""

    # Batch function for villages - gets analytics for all villages in one query
    op.execute("""
    CREATE OR REPLACE FUNCTION get_villages_inspection_analytics_batch(
        village_ids INTEGER[],
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
            v.id as village_id,
            COALESCE(COUNT(i_scores.id), 0) as total_inspections,
            ROUND(COALESCE(AVG(i_scores.overall_score), 0), 2) as average_score,
            COALESCE(MAX(i_scores.overall_score), 0) as latest_score,
            CASE 
                WHEN COUNT(i_scores.id) > 0 THEN 100.0 
                ELSE 0.0 
            END as coverage_percentage
        FROM unnest(village_ids) AS v(id)
        LEFT JOIN inspection_scores i_scores ON i_scores.village_id = v.id
            AND (start_date_param IS NULL OR i_scores.date >= start_date_param)
            AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
        GROUP BY v.id;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Batch function for blocks - gets analytics for all blocks in one query
    op.execute("""
    CREATE OR REPLACE FUNCTION get_blocks_inspection_analytics_batch(
        block_ids INTEGER[],
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        block_id INTEGER,
        total_gps BIGINT,
        inspected_gps BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            b.id as block_id,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(AVG(COALESCE(gp_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM unnest(block_ids) AS b(id)
        LEFT JOIN villages gp ON gp.block_id = b.id
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
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY b.id;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Batch function for districts - gets analytics for all districts in one query
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


def downgrade() -> None:
    """Remove batch analytics functions."""

    op.execute(
        "DROP FUNCTION IF EXISTS get_villages_inspection_analytics_batch(INTEGER[], DATE, DATE);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS get_blocks_inspection_analytics_batch(INTEGER[], DATE, DATE);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS get_districts_inspection_analytics_batch(INTEGER[], DATE, DATE);"
    )
