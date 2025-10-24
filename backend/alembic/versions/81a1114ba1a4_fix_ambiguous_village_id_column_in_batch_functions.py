"""fix_ambiguous_village_id_column_in_batch_functions

Revision ID: 81a1114ba1a4
Revises: 66e6f908f13e
Create Date: 2025-10-24 23:10:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "81a1114ba1a4"
down_revision: Union[str, Sequence[str], None] = "66e6f908f13e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix ambiguous column reference by qualifying all column references in batch functions."""

    # Fix get_villages_inspection_analytics_batch to properly qualify column references
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
            COALESCE((
                SELECT i2.overall_score 
                FROM inspection_scores i2
                WHERE i2.village_id = v.id
                AND (start_date_param IS NULL OR i2.date >= start_date_param)
                AND (end_date_param IS NULL OR i2.date <= end_date_param)
                ORDER BY i2.date DESC, i2.start_time DESC 
                LIMIT 1
            ), 0) as latest_score,
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
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_blocks_inspection_analytics_batch to properly qualify column references
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
            ROUND(COALESCE(AVG(CASE WHEN gp_inspected.has_inspections THEN gp_inspected.average_score END), 0), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM unnest(block_ids) AS b(id)
        LEFT JOIN gram_panchayats gp ON gp.block_id = b.id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                AVG(scores_inner.average_score) as average_score,
                BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT i_scores.village_id, AVG(i_scores.overall_score) as average_score
                FROM inspection_scores i_scores
                WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                GROUP BY i_scores.village_id
            ) scores_inner ON gp_inner.id = scores_inner.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY b.id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_districts_inspection_analytics_batch to properly qualify column references
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
            ROUND(COALESCE(AVG(CASE WHEN block_inspected.has_inspections THEN block_inspected.average_score END), 0), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM unnest(district_ids) AS d(id)
        LEFT JOIN blocks b ON b.district_id = d.id
        LEFT JOIN gram_panchayats gp ON gp.block_id = b.id
        LEFT JOIN (
            SELECT 
                blocks_inner.id as block_id,
                AVG(gp_scores.average_score) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks blocks_inner
            LEFT JOIN gram_panchayats gp_inner ON blocks_inner.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    gp_inner2.id as gp_id,
                    AVG(scores_inner.average_score) as average_score,
                    BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT i_scores.village_id, AVG(i_scores.overall_score) as average_score
                    FROM inspection_scores i_scores
                    WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                    GROUP BY i_scores.village_id
                ) scores_inner ON gp_inner2.id = scores_inner.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY blocks_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT i_scores.village_id
                FROM inspection_scores i_scores
                WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                GROUP BY i_scores.village_id
            ) scores_inner ON gp_inner.id = scores_inner.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY d.id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_district_inspection_analytics to properly qualify column references
    op.execute("""
    CREATE OR REPLACE FUNCTION get_district_inspection_analytics(
        district_id_param INTEGER,
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
            district_id_param,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) as inspected_blocks,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(COALESCE(AVG(CASE WHEN block_inspected.has_inspections THEN block_inspected.average_score END), 0), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM blocks b
        LEFT JOIN gram_panchayats gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                b_inner.id as block_id,
                AVG(gp_scores.average_score) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks b_inner
            LEFT JOIN gram_panchayats gp_inner ON b_inner.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    gp_inner2.id as gp_id,
                    AVG(scores_inner.average_score) as average_score,
                    BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT i_scores.village_id, AVG(i_scores.overall_score) as average_score
                    FROM inspection_scores i_scores
                    WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                    GROUP BY i_scores.village_id
                ) scores_inner ON gp_inner2.id = scores_inner.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            WHERE b_inner.district_id = district_id_param
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT i_scores.village_id
                FROM inspection_scores i_scores
                WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                GROUP BY i_scores.village_id
            ) scores_inner ON gp_inner.id = scores_inner.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        WHERE b.district_id = district_id_param;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_state_inspection_analytics to properly qualify column references
    op.execute("""
    CREATE OR REPLACE FUNCTION get_state_inspection_analytics(
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        total_districts BIGINT,
        inspected_districts BIGINT,
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
            COUNT(DISTINCT d.id) as total_districts,
            COUNT(DISTINCT CASE WHEN district_inspected.has_inspections THEN d.id END) as inspected_districts,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) as inspected_blocks,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(COALESCE(AVG(CASE WHEN district_inspected.has_inspections THEN district_inspected.average_score END), 0), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM districts d
        LEFT JOIN blocks b ON d.id = b.district_id
        LEFT JOIN gram_panchayats gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                d_inner.id as district_id,
                AVG(block_scores.average_score) as average_score,
                BOOL_OR(block_scores.has_inspections) as has_inspections
            FROM districts d_inner
            LEFT JOIN blocks b_inner ON d_inner.id = b_inner.district_id
            LEFT JOIN (
                SELECT 
                    b_inner2.id as block_id,
                    AVG(gp_scores.average_score) as average_score,
                    BOOL_OR(gp_scores.has_inspections) as has_inspections
                FROM blocks b_inner2
                LEFT JOIN gram_panchayats gp_inner ON b_inner2.id = gp_inner.block_id
                LEFT JOIN (
                    SELECT 
                        gp_inner2.id as gp_id,
                        AVG(scores_inner.average_score) as average_score,
                        BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
                    FROM gram_panchayats gp_inner2
                    LEFT JOIN (
                        SELECT i_scores.village_id, AVG(i_scores.overall_score) as average_score
                        FROM inspection_scores i_scores
                        WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                        AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                        GROUP BY i_scores.village_id
                    ) scores_inner ON gp_inner2.id = scores_inner.village_id
                    GROUP BY gp_inner2.id
                ) gp_scores ON gp_inner.id = gp_scores.gp_id
                GROUP BY b_inner2.id
            ) block_scores ON b_inner.id = block_scores.block_id
            GROUP BY d_inner.id
        ) district_inspected ON d.id = district_inspected.district_id
        LEFT JOIN (
            SELECT 
                b_inner.id as block_id,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks b_inner
            LEFT JOIN gram_panchayats gp_inner ON b_inner.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    gp_inner2.id as gp_id,
                    BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT i_scores.village_id
                    FROM inspection_scores i_scores
                    WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                    GROUP BY i_scores.village_id
                ) scores_inner ON gp_inner2.id = scores_inner.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(scores_inner.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT i_scores.village_id
                FROM inspection_scores i_scores
                WHERE (start_date_param IS NULL OR i_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR i_scores.date <= end_date_param)
                GROUP BY i_scores.village_id
            ) scores_inner ON gp_inner.id = scores_inner.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)


def downgrade() -> None:
    """Revert to the previous version with ambiguous column references."""
    # Not implementing downgrade as it would restore broken code
    pass
