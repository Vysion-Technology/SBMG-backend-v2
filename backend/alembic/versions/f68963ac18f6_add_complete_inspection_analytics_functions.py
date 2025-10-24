"""add_complete_inspection_analytics_functions

Revision ID: f68963ac18f6
Revises: b9d6b23e259c
Create Date: 2025-10-24 22:50:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f68963ac18f6"
down_revision: Union[str, Sequence[str], None] = "b9d6b23e259c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add comprehensive inspection scoring and analytics functions."""

    # ========================================================================
    # SECTION 1: SCORING FUNCTIONS
    # ========================================================================

    # Function to calculate household waste score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_household_waste_score(
        waste_collection_frequency TEXT,
        dry_wet_vehicle_segregation BOOLEAN,
        covered_collection_in_vehicles BOOLEAN,
        waste_disposed_at_rrc BOOLEAN,
        waste_collection_vehicle_functional BOOLEAN
    ) RETURNS INTEGER AS $$
    DECLARE
        points INTEGER := 0;
    BEGIN
        -- Waste collection frequency (10 points max)
        CASE waste_collection_frequency
            WHEN 'DAILY' THEN points := points + 10;
            WHEN 'ONCE_IN_THREE_DAYS' THEN points := points + 7;
            WHEN 'WEEKLY' THEN points := points + 3;
            ELSE points := points + 0;
        END CASE;

        -- Dry/wet vehicle segregation (10 points)
        IF dry_wet_vehicle_segregation THEN
            points := points + 10;
        END IF;

        -- Covered collection in vehicles (10 points)
        IF covered_collection_in_vehicles THEN
            points := points + 10;
        END IF;

        -- Waste disposed at RRC (10 points)
        IF waste_disposed_at_rrc THEN
            points := points + 10;
        END IF;

        -- Waste collection vehicle functional (10 points)
        IF waste_collection_vehicle_functional THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Function to calculate road cleaning score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_road_cleaning_score(
        road_cleaning_frequency TEXT
    ) RETURNS INTEGER AS $$
    BEGIN
        CASE road_cleaning_frequency
            WHEN 'WEEKLY' THEN RETURN 10;
            WHEN 'FORTNIGHTLY' THEN RETURN 5;
            WHEN 'MONTHLY' THEN RETURN 2;
            ELSE RETURN 0;
        END CASE;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Function to calculate drain cleaning score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_drain_cleaning_score(
        drain_cleaning_frequency TEXT,
        disposal_of_sludge_from_drains BOOLEAN,
        drain_waste_colllected_on_roadside BOOLEAN
    ) RETURNS INTEGER AS $$
    DECLARE
        points INTEGER := 0;
    BEGIN
        -- Drain cleaning frequency (10 points max)
        CASE drain_cleaning_frequency
            WHEN 'WEEKLY' THEN points := points + 10;
            WHEN 'FORTNIGHTLY' THEN points := points + 5;
            WHEN 'MONTHLY' THEN points := points + 2;
            ELSE points := points + 0;
        END CASE;

        -- Disposal of sludge from drains (10 points)
        IF disposal_of_sludge_from_drains THEN
            points := points + 10;
        END IF;

        -- Drain waste NOT collected on roadside (10 points - inverted scoring)
        IF drain_waste_colllected_on_roadside IS FALSE THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Function to calculate community sanitation score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_community_sanitation_score(
        csc_cleaning_frequency TEXT,
        electricity_and_water BOOLEAN,
        csc_used_by_community BOOLEAN,
        pink_toilets_cleaning BOOLEAN
    ) RETURNS INTEGER AS $$
    DECLARE
        points INTEGER := 0;
    BEGIN
        -- CSC cleaning frequency (10 points max)
        CASE csc_cleaning_frequency
            WHEN 'DAILY' THEN points := points + 10;
            WHEN 'ONCE_IN_THREE_DAYS' THEN points := points + 7;
            WHEN 'WEEKLY' THEN points := points + 3;
            ELSE points := points + 0;
        END CASE;

        -- Electricity and water (10 points)
        IF electricity_and_water THEN
            points := points + 10;
        END IF;

        -- CSC used by community (10 points)
        IF csc_used_by_community THEN
            points := points + 10;
        END IF;

        -- Pink toilets cleaning (10 points)
        IF pink_toilets_cleaning THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Function to calculate other inspection score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_other_inspection_score(
        firm_paid_regularly BOOLEAN,
        cleaning_staff_paid_regularly BOOLEAN,
        firm_provided_safety_equipment BOOLEAN,
        village_visibly_clean BOOLEAN,
        rate_chart_displayed BOOLEAN
    ) RETURNS INTEGER AS $$
    DECLARE
        points INTEGER := 0;
    BEGIN
        -- Firm paid regularly (10 points)
        IF firm_paid_regularly THEN
            points := points + 10;
        END IF;

        -- Cleaning staff paid regularly (10 points)
        IF cleaning_staff_paid_regularly THEN
            points := points + 10;
        END IF;

        -- Firm provided safety equipment (10 points)
        IF firm_provided_safety_equipment THEN
            points := points + 10;
        END IF;

        -- Village visibly clean (10 points)
        IF village_visibly_clean THEN
            points := points + 10;
        END IF;

        -- Rate chart displayed (10 points)
        IF rate_chart_displayed THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Function to calculate complete inspection score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_inspection_score(inspection_id INTEGER)
    RETURNS TABLE(
        household_waste_score DECIMAL(5,2),
        road_cleaning_score DECIMAL(5,2),
        drain_cleaning_score DECIMAL(5,2),
        community_sanitation_score DECIMAL(5,2),
        other_score DECIMAL(5,2),
        overall_score DECIMAL(5,2),
        total_points INTEGER,
        max_points INTEGER
    ) AS $$
    DECLARE
        household_points INTEGER := 0;
        road_points INTEGER := 0;
        drain_points INTEGER := 0;
        community_points INTEGER := 0;
        other_points INTEGER := 0;
        total_max INTEGER := 180;
    BEGIN
        -- Get household waste points (50 points max)
        SELECT calculate_household_waste_score(
            hw.waste_collection_frequency::TEXT,
            hw.dry_wet_vehicle_segregation,
            hw.covered_collection_in_vehicles,
            hw.waste_disposed_at_rrc,
            hw.waste_collection_vehicle_functional
        ) INTO household_points
        FROM inspection_household_waste_collection_and_disposal_inspection_i hw
        WHERE hw.id = inspection_id;

        -- Get road cleaning points (10 points max)
        SELECT calculate_road_cleaning_score(rd.road_cleaning_frequency::TEXT) INTO road_points
        FROM inspection_road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get drain cleaning points (30 points max)
        SELECT calculate_drain_cleaning_score(
            rd.drain_cleaning_frequency::TEXT,
            rd.disposal_of_sludge_from_drains,
            rd.drain_waste_colllected_on_roadside
        ) INTO drain_points
        FROM inspection_road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get community sanitation points (40 points max)
        SELECT calculate_community_sanitation_score(
            cs.csc_cleaning_frequency::TEXT,
            cs.electricity_and_water,
            cs.csc_used_by_community,
            cs.pink_toilets_cleaning
        ) INTO community_points
        FROM inspection_community_sanitation_inspection_items cs
        WHERE cs.id = inspection_id;

        -- Get other inspection points (50 points max)
        SELECT calculate_other_inspection_score(
            ot.firm_paid_regularly,
            ot.cleaning_staff_paid_regularly,
            ot.firm_provided_safety_equipment,
            ot.village_visibly_clean,
            ot.rate_chart_displayed
        ) INTO other_points
        FROM inspection_other_inspection_items ot
        WHERE ot.id = inspection_id;

        -- Calculate total points
        total_points := COALESCE(household_points, 0) + COALESCE(road_points, 0) +
                       COALESCE(drain_points, 0) + COALESCE(community_points, 0) +
                       COALESCE(other_points, 0);

        -- Return section scores (as percentages) and overall
        RETURN QUERY SELECT
            ROUND((COALESCE(household_points, 0) / 50.0) * 100, 2),  -- Household waste score %
            ROUND((COALESCE(road_points, 0) / 10.0) * 100, 2),       -- Road cleaning score %
            ROUND((COALESCE(drain_points, 0) / 30.0) * 100, 2),      -- Drain cleaning score %
            ROUND((COALESCE(community_points, 0) / 40.0) * 100, 2),  -- Community sanitation score %
            ROUND((COALESCE(other_points, 0) / 50.0) * 100, 2),      -- Other score %
            ROUND((total_points / 180.0) * 100, 2),                  -- Overall score %
            total_points,
            total_max;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # ========================================================================
    # SECTION 2: INSPECTION SCORES VIEW
    # ========================================================================

    # Create view for inspections with scores
    op.execute("""
    CREATE OR REPLACE VIEW inspection_scores AS
    SELECT
        i.id,
        i.gp_id as village_id,
        i.date,
        i.start_time,
        i.remarks,
        COALESCE(scores.household_waste_score, 0) as household_waste_score,
        COALESCE(scores.road_cleaning_score, 0) as road_cleaning_score,
        COALESCE(scores.drain_cleaning_score, 0) as drain_cleaning_score,
        COALESCE(scores.community_sanitation_score, 0) as community_sanitation_score,
        COALESCE(scores.other_score, 0) as other_score,
        COALESCE(scores.overall_score, 0) as overall_score,
        COALESCE(scores.total_points, 0) as total_points,
        COALESCE(scores.max_points, 180) as max_points
    FROM inspections i
    LEFT JOIN LATERAL calculate_inspection_score(i.id) scores ON true;
    """)

    # ========================================================================
    # SECTION 3: SINGLE ENTITY ANALYTICS FUNCTIONS
    # ========================================================================

    # Function to get village inspection analytics
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
            COALESCE((
                SELECT overall_score 
                FROM inspection_scores 
                WHERE village_id = village_id_param
                AND (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                ORDER BY date DESC, start_time DESC 
                LIMIT 1
            ), 0) as latest_score,
            CASE 
                WHEN COUNT(*) > 0 THEN 100.0 
                ELSE 0.0 
            END as coverage_percentage
        FROM inspection_scores
        WHERE village_id = village_id_param
        AND (start_date_param IS NULL OR date >= start_date_param)
        AND (end_date_param IS NULL OR date <= end_date_param);
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)

    # Function to get district inspection analytics
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

    # Function to get state inspection analytics
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

    # ========================================================================
    # SECTION 4: BATCH ANALYTICS FUNCTIONS (OPTIMIZED FOR PERFORMANCE)
    # ========================================================================

    # Batch function for villages - gets analytics for multiple villages in one query
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
                SELECT overall_score 
                FROM inspection_scores 
                WHERE village_id = v.id
                AND (start_date_param IS NULL OR date >= start_date_param)
                AND (end_date_param IS NULL OR date <= end_date_param)
                ORDER BY date DESC, start_time DESC 
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

    # Batch function for blocks - gets analytics for multiple blocks in one query
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

    # Batch function for districts - gets analytics for multiple districts in one query
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


def downgrade() -> None:
    """Downgrade schema: Remove all inspection scoring and analytics functions."""

    # Drop batch analytics functions
    op.execute("DROP FUNCTION IF EXISTS get_districts_inspection_analytics_batch(INTEGER[], DATE, DATE);")
    op.execute("DROP FUNCTION IF EXISTS get_blocks_inspection_analytics_batch(INTEGER[], DATE, DATE);")
    op.execute("DROP FUNCTION IF EXISTS get_villages_inspection_analytics_batch(INTEGER[], DATE, DATE);")

    # Drop single entity analytics functions
    op.execute("DROP FUNCTION IF EXISTS get_state_inspection_analytics(DATE, DATE);")
    op.execute("DROP FUNCTION IF EXISTS get_district_inspection_analytics(INTEGER, DATE, DATE);")
    op.execute("DROP FUNCTION IF EXISTS get_village_inspection_analytics(INTEGER, DATE, DATE);")

    # Drop inspection scores view
    op.execute("DROP VIEW IF EXISTS inspection_scores;")

    # Drop scoring functions
    op.execute("DROP FUNCTION IF EXISTS calculate_inspection_score(INTEGER);")
    op.execute("DROP FUNCTION IF EXISTS calculate_other_inspection_score(BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN);")
    op.execute("DROP FUNCTION IF EXISTS calculate_community_sanitation_score(TEXT, BOOLEAN, BOOLEAN, BOOLEAN);")
    op.execute("DROP FUNCTION IF EXISTS calculate_drain_cleaning_score(TEXT, BOOLEAN, BOOLEAN);")
    op.execute("DROP FUNCTION IF EXISTS calculate_road_cleaning_score(TEXT);")
    op.execute("DROP FUNCTION IF EXISTS calculate_household_waste_score(TEXT, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN);")
