"""fix_district_coverage_calculation_properly

Revision ID: 7f808341d47f
Revises: f5f09f0cb2c6
Create Date: 2025-10-12 11:34:23.554699

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7f808341d47f"
down_revision: Union[str, Sequence[str], None] = "f5f09f0cb2c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Properly fix district coverage percentage calculation with correct aggregation."""

    # Drop and recreate get_district_inspection_analytics with proper aggregation
    op.execute(
        "DROP FUNCTION IF EXISTS get_district_inspection_analytics(INTEGER, DATE, DATE);"
    )

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
    DECLARE
        v_total_blocks BIGINT;
        v_inspected_blocks BIGINT;
        v_total_gps BIGINT;
        v_inspected_gps BIGINT;
        v_average_score DECIMAL(5,2);
        v_coverage_percentage DECIMAL(5,2);
    BEGIN
        -- Count total blocks in the district
        SELECT COUNT(DISTINCT b.id) INTO v_total_blocks
        FROM blocks b
        WHERE b.district_id = district_id_param;
        
        -- Count inspected blocks (blocks that have at least one inspected village)
        SELECT COUNT(DISTINCT b.id) INTO v_inspected_blocks
        FROM blocks b
        INNER JOIN villages v ON b.id = v.block_id
        INNER JOIN inspection_scores ins ON v.id = ins.village_id
        WHERE b.district_id = district_id_param
        AND (start_date_param IS NULL OR ins.date >= start_date_param)
        AND (end_date_param IS NULL OR ins.date <= end_date_param);
        
        -- Count total villages in the district
        SELECT COUNT(DISTINCT v.id) INTO v_total_gps
        FROM villages v
        INNER JOIN blocks b ON v.block_id = b.id
        WHERE b.district_id = district_id_param;
        
        -- Count inspected villages
        SELECT COUNT(DISTINCT v.id) INTO v_inspected_gps
        FROM villages v
        INNER JOIN blocks b ON v.block_id = b.id
        INNER JOIN inspection_scores ins ON v.id = ins.village_id
        WHERE b.district_id = district_id_param
        AND (start_date_param IS NULL OR ins.date >= start_date_param)
        AND (end_date_param IS NULL OR ins.date <= end_date_param);
        
        -- Calculate average score
        SELECT COALESCE(ROUND(AVG(ins.overall_score), 2), 0) INTO v_average_score
        FROM inspection_scores ins
        INNER JOIN villages v ON ins.village_id = v.id
        INNER JOIN blocks b ON v.block_id = b.id
        WHERE b.district_id = district_id_param
        AND (start_date_param IS NULL OR ins.date >= start_date_param)
        AND (end_date_param IS NULL OR ins.date <= end_date_param);
        
        -- Calculate coverage percentage based on villages
        v_coverage_percentage := ROUND((v_inspected_gps * 100.0) / NULLIF(v_total_gps, 0), 2);
        
        -- Return the results
        RETURN QUERY
        SELECT 
            district_id_param,
            v_total_blocks,
            v_inspected_blocks,
            v_total_gps,
            v_inspected_gps,
            v_average_score,
            v_coverage_percentage;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Revert to previous version with aggregation issues."""

    # Drop and recreate get_district_inspection_analytics with old version
    op.execute(
        "DROP FUNCTION IF EXISTS get_district_inspection_analytics(INTEGER, DATE, DATE);"
    )

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
            ROUND((COUNT(DISTINCT CASE WHEN gp_inspected.has_inspections THEN gp.id END) * 100.0) / NULLIF(COUNT(DISTINCT gp.id), 0), 2) as coverage_percentage
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
