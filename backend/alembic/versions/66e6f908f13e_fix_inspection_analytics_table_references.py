"""fix_inspection_analytics_table_references

Revision ID: 66e6f908f13e
Revises: f68963ac18f6
Create Date: 2025-10-24 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "66e6f908f13e"
down_revision: Union[str, Sequence[str], None] = "f68963ac18f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix table references in inspection analytics functions - use gram_panchayats instead of villages."""

    # Fix get_blocks_inspection_analytics_batch - use gram_panchayats table
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
                AVG(village_scores.average_score) as average_score,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT inspection_scores.village_id, AVG(overall_score) as average_score
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                GROUP BY inspection_scores.village_id
            ) village_scores ON gp_inner.id = village_scores.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY b.id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_districts_inspection_analytics_batch - use gram_panchayats table
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
                blocks.id as block_id,
                AVG(gp_scores.average_score) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks
            LEFT JOIN gram_panchayats gp_inner ON blocks.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    gp_inner2.id as gp_id,
                    AVG(village_scores.average_score) as average_score,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT inspection_scores.village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                    AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                    GROUP BY inspection_scores.village_id
                ) village_scores ON gp_inner2.id = village_scores.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY blocks.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT inspection_scores.village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR inspection_scores.date >= start_date_param)
                AND (end_date_param IS NULL OR inspection_scores.date <= end_date_param)
                GROUP BY inspection_scores.village_id
            ) village_scores ON gp_inner.id = village_scores.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        GROUP BY d.id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_district_inspection_analytics - use gram_panchayats table
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
                    AVG(village_scores.average_score) as average_score,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR date >= start_date_param)
                    AND (end_date_param IS NULL OR date <= end_date_param)
                    GROUP BY village_id
                ) village_scores ON gp_inner2.id = village_scores.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            WHERE b_inner.district_id = district_id_param
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                GROUP BY village_id
            ) village_scores ON gp_inner.id = village_scores.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        WHERE b.district_id = district_id_param;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Fix get_state_inspection_analytics - use gram_panchayats table
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
                        AVG(village_scores.average_score) as average_score,
                        BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                    FROM gram_panchayats gp_inner2
                    LEFT JOIN (
                        SELECT village_id, AVG(overall_score) as average_score
                        FROM inspection_scores
                        WHERE (start_date_param IS NULL OR date >= start_date_param)
                        AND (end_date_param IS NULL OR date <= end_date_param)
                        GROUP BY village_id
                    ) village_scores ON gp_inner2.id = village_scores.village_id
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
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM gram_panchayats gp_inner2
                LEFT JOIN (
                    SELECT village_id
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR date >= start_date_param)
                    AND (end_date_param IS NULL OR date <= end_date_param)
                    GROUP BY village_id
                ) village_scores ON gp_inner2.id = village_scores.village_id
                GROUP BY gp_inner2.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                gp_inner.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM gram_panchayats gp_inner
            LEFT JOIN (
                SELECT village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                GROUP BY village_id
            ) village_scores ON gp_inner.id = village_scores.village_id
            GROUP BY gp_inner.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)


def downgrade() -> None:
    """Revert to the previous (broken) version with villages table references."""
    
    # Restore the broken version of get_blocks_inspection_analytics_batch
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
        LEFT JOIN villages gp ON gp.block_id = b.id
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                AVG(village_scores.average_score) as average_score,
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
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Restore the broken version of get_districts_inspection_analytics_batch
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
        LEFT JOIN villages gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                blocks.id as block_id,
                AVG(gp_scores.average_score) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks
            LEFT JOIN villages gp_inner ON blocks.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(village_scores.average_score) as average_score,
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
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Restore broken get_district_inspection_analytics
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
        LEFT JOIN villages gp ON b.id = gp.block_id
        LEFT JOIN (
            SELECT 
                b_inner.id as block_id,
                AVG(gp_scores.average_score) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks b_inner
            LEFT JOIN villages gp_inner ON b_inner.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(village_scores.average_score) as average_score,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM villages v
                LEFT JOIN (
                    SELECT village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR date >= start_date_param)
                    AND (end_date_param IS NULL OR date <= end_date_param)
                    GROUP BY village_id
                ) village_scores ON v.id = village_scores.village_id
                GROUP BY v.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            WHERE b_inner.district_id = district_id_param
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM villages v
            LEFT JOIN (
                SELECT village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                GROUP BY village_id
            ) village_scores ON v.id = village_scores.village_id
            GROUP BY v.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        WHERE b.district_id = district_id_param;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Restore broken get_state_inspection_analytics
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
        LEFT JOIN villages gp ON b.id = gp.block_id
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
                LEFT JOIN villages gp_inner ON b_inner2.id = gp_inner.block_id
                LEFT JOIN (
                    SELECT 
                        v.id as gp_id,
                        AVG(village_scores.average_score) as average_score,
                        BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                    FROM villages v
                    LEFT JOIN (
                        SELECT village_id, AVG(overall_score) as average_score
                        FROM inspection_scores
                        WHERE (start_date_param IS NULL OR date >= start_date_param)
                        AND (end_date_param IS NULL OR date <= end_date_param)
                        GROUP BY village_id
                    ) village_scores ON v.id = village_scores.village_id
                    GROUP BY v.id
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
            LEFT JOIN villages gp_inner ON b_inner.id = gp_inner.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
                FROM villages v
                LEFT JOIN (
                    SELECT village_id
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR date >= start_date_param)
                    AND (end_date_param IS NULL OR date <= end_date_param)
                    GROUP BY village_id
                ) village_scores ON v.id = village_scores.village_id
                GROUP BY v.id
            ) gp_scores ON gp_inner.id = gp_scores.gp_id
            GROUP BY b_inner.id
        ) block_inspected ON b.id = block_inspected.block_id
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                BOOL_OR(village_scores.village_id IS NOT NULL) as has_inspections
            FROM villages v
            LEFT JOIN (
                SELECT village_id
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                GROUP BY village_id
            ) village_scores ON v.id = village_scores.village_id
            GROUP BY v.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
