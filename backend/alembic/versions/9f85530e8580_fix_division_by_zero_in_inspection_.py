"""fix_division_by_zero_in_inspection_analytics

Revision ID: 9f85530e8580
Revises: bc351229b386
Create Date: 2025-10-11 16:42:37.981806

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f85530e8580"
down_revision: Union[str, Sequence[str], None] = "bc351229b386"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix division by zero errors in inspection analytics functions."""

    # Fix get_block_inspection_analytics - use NULLIF to prevent division by zero
    op.execute("""
    CREATE OR REPLACE FUNCTION get_block_inspection_analytics(
        block_id_param INTEGER,
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
            block_id_param,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) as inspected_gps,
            ROUND(AVG(COALESCE(gp_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
        FROM villages gp
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                AVG(COALESCE(village_scores.average_score, 0)) as average_score,
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
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        WHERE gp.block_id = block_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Fix get_district_inspection_analytics - use NULLIF to prevent division by zero
    op.execute("""
    CREATE OR REPLACE FUNCTION get_district_inspection_analytics(
        district_id_param INTEGER,
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        district_id INTEGER,
        total_blocks BIGINT,
        inspected_blocks BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            district_id_param,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) as inspected_blocks,
            ROUND(AVG(COALESCE(block_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) * 100.0) / NULLIF(COUNT(DISTINCT b.id), 0), 2) as coverage_percentage
        FROM blocks b
        LEFT JOIN (
            SELECT 
                b.id as block_id,
                AVG(COALESCE(gp_scores.average_score, 0)) as average_score,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks b
            LEFT JOIN villages gp ON b.id = gp.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(COALESCE(village_scores.average_score, 0)) as average_score,
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
            ) gp_scores ON gp.id = gp_scores.gp_id
            GROUP BY b.id
        ) block_inspected ON b.id = block_inspected.block_id
        WHERE b.district_id = district_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Fix get_state_inspection_analytics - use NULLIF to prevent division by zero
    op.execute("""
    CREATE OR REPLACE FUNCTION get_state_inspection_analytics(
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        total_districts BIGINT,
        inspected_districts BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            COUNT(DISTINCT d.id) as total_districts,
            COUNT(DISTINCT CASE WHEN district_inspected.has_inspections THEN d.id END) as inspected_districts,
            ROUND(AVG(COALESCE(district_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN district_inspected.has_inspections THEN d.id END) * 100.0) / NULLIF(COUNT(DISTINCT d.id), 0), 2) as coverage_percentage
        FROM districts d
        LEFT JOIN (
            SELECT 
                d.id as district_id,
                AVG(COALESCE(block_scores.average_score, 0)) as average_score,
                BOOL_OR(block_scores.has_inspections) as has_inspections
            FROM districts d
            LEFT JOIN blocks b ON d.id = b.district_id
            LEFT JOIN (
                SELECT 
                    b.id as block_id,
                    AVG(COALESCE(gp_scores.average_score, 0)) as average_score,
                    BOOL_OR(gp_scores.has_inspections) as has_inspections
                FROM blocks b
                LEFT JOIN villages gp ON b.id = gp.block_id
                LEFT JOIN (
                    SELECT 
                        v.id as gp_id,
                        AVG(COALESCE(village_scores.average_score, 0)) as average_score,
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
                ) gp_scores ON gp.id = gp_scores.gp_id
                GROUP BY b.id
            ) block_scores ON b.id = block_scores.block_id
            GROUP BY d.id
        ) district_inspected ON d.id = district_inspected.district_id;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to original functions (with division by zero issue)."""

    # Revert get_block_inspection_analytics
    op.execute("""
    CREATE OR REPLACE FUNCTION get_block_inspection_analytics(
        block_id_param INTEGER,
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
            block_id_param,
            COUNT(DISTINCT gp.id) as total_gps,
            COUNT(DISTINCT CASE WHEN gp_inspected.gp_id IS NOT NULL THEN gp.id END) as inspected_gps,
            ROUND(AVG(COALESCE(gp_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.gp_id IS NOT NULL THEN gp.id END) * 100.0) / COUNT(DISTINCT gp.id), 2) as coverage_percentage
        FROM villages gp
        LEFT JOIN (
            SELECT 
                v.id as gp_id,
                AVG(COALESCE(village_scores.average_score, 0)) as average_score
            FROM villages v
            LEFT JOIN (
                SELECT village_id, AVG(overall_score) as average_score
                FROM inspection_scores
                WHERE (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                GROUP BY village_id
            ) village_scores ON v.id = village_scores.village_id
            GROUP BY v.id
        ) gp_inspected ON gp.id = gp_inspected.gp_id
        WHERE gp.block_id = block_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Revert get_district_inspection_analytics
    op.execute("""
    CREATE OR REPLACE FUNCTION get_district_inspection_analytics(
        district_id_param INTEGER,
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        district_id INTEGER,
        total_blocks BIGINT,
        inspected_blocks BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            district_id_param,
            COUNT(DISTINCT b.id) as total_blocks,
            COUNT(DISTINCT CASE WHEN block_inspected.block_id IS NOT NULL THEN b.id END) as inspected_blocks,
            ROUND(AVG(COALESCE(block_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN block_inspected.block_id IS NOT NULL THEN b.id END) * 100.0) / COUNT(DISTINCT b.id), 2) as coverage_percentage
        FROM blocks b
        LEFT JOIN (
            SELECT 
                b.id as block_id,
                AVG(COALESCE(gp_scores.average_score, 0)) as average_score
            FROM blocks b
            LEFT JOIN villages gp ON b.id = gp.block_id
            LEFT JOIN (
                SELECT 
                    v.id as gp_id,
                    AVG(COALESCE(village_scores.average_score, 0)) as average_score
                FROM villages v
                LEFT JOIN (
                    SELECT village_id, AVG(overall_score) as average_score
                    FROM inspection_scores
                    WHERE (start_date_param IS NULL OR date >= start_date_param)
                    AND (end_date_param IS NULL OR date <= end_date_param)
                    GROUP BY village_id
                ) village_scores ON v.id = village_scores.village_id
                GROUP BY v.id
            ) gp_scores ON gp.id = gp_scores.gp_id
            GROUP BY b.id
        ) block_inspected ON b.id = block_inspected.block_id
        WHERE b.district_id = district_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Revert get_state_inspection_analytics
    op.execute("""
    CREATE OR REPLACE FUNCTION get_state_inspection_analytics(
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        total_districts BIGINT,
        inspected_districts BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            COUNT(DISTINCT d.id) as total_districts,
            COUNT(DISTINCT CASE WHEN district_inspected.district_id IS NOT NULL THEN d.id END) as inspected_districts,
            ROUND(AVG(COALESCE(district_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN district_inspected.district_id IS NOT NULL THEN d.id END) * 100.0) / COUNT(DISTINCT d.id), 2) as coverage_percentage
        FROM districts d
        LEFT JOIN (
            SELECT 
                d.id as district_id,
                AVG(COALESCE(block_scores.average_score, 0)) as average_score
            FROM districts d
            LEFT JOIN blocks b ON d.id = b.district_id
            LEFT JOIN (
                SELECT 
                    b.id as block_id,
                    AVG(COALESCE(gp_scores.average_score, 0)) as average_score
                FROM blocks b
                LEFT JOIN villages gp ON b.id = gp.block_id
                LEFT JOIN (
                    SELECT 
                        v.id as gp_id,
                        AVG(COALESCE(village_scores.average_score, 0)) as average_score
                    FROM villages v
                    LEFT JOIN (
                        SELECT village_id, AVG(overall_score) as average_score
                        FROM inspection_scores
                        WHERE (start_date_param IS NULL OR date >= start_date_param)
                        AND (end_date_param IS NULL OR date <= end_date_param)
                        GROUP BY village_id
                    ) village_scores ON v.id = village_scores.village_id
                    GROUP BY v.id
                ) gp_scores ON gp.id = gp_scores.gp_id
                GROUP BY b.id
            ) block_scores ON b.id = block_scores.block_id
            GROUP BY d.id
        ) district_inspected ON d.id = district_inspected.district_id;
    END;
    $$ LANGUAGE plpgsql;
    """)
