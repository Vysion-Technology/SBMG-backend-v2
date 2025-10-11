"""add_granular_inspection_analytics

Revision ID: 7ed5dd5c6744
Revises: 9f85530e8580
Create Date: 2025-10-11 17:00:40.969983

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7ed5dd5c6744"
down_revision: Union[str, Sequence[str], None] = "9f85530e8580"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add granular inspection analytics to state and district functions."""

    # Drop existing functions to allow changing return types
    op.execute(
        "DROP FUNCTION IF EXISTS get_district_inspection_analytics(INTEGER, DATE, DATE);"
    )
    op.execute("DROP FUNCTION IF EXISTS get_state_inspection_analytics(DATE, DATE);")

    # Update get_district_inspection_analytics to include total and inspected GPs
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
            ROUND(AVG(COALESCE(block_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN block_inspected.has_inspections THEN b.id END) * 100.0) / NULLIF(COUNT(DISTINCT b.id), 0), 2) as coverage_percentage
        FROM blocks b
        LEFT JOIN villages gp ON b.id = gp.block_id
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
    $$ LANGUAGE plpgsql;
    """)

    # Update get_state_inspection_analytics to include total and inspected blocks and GPs
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
            ROUND(AVG(COALESCE(district_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN district_inspected.has_inspections THEN d.id END) * 100.0) / NULLIF(COUNT(DISTINCT d.id), 0), 2) as coverage_percentage
        FROM districts d
        LEFT JOIN blocks b ON d.id = b.district_id
        LEFT JOIN villages gp ON b.id = gp.block_id
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
        ) district_inspected ON d.id = district_inspected.district_id
        LEFT JOIN (
            SELECT 
                b.id as block_id,
                BOOL_OR(gp_scores.has_inspections) as has_inspections
            FROM blocks b
            LEFT JOIN villages gp ON b.id = gp.block_id
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
            ) gp_scores ON gp.id = gp_scores.gp_id
            GROUP BY b.id
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
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to previous version of analytics functions."""

    # Revert get_district_inspection_analytics to previous version
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

    # Revert get_state_inspection_analytics to previous version
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
