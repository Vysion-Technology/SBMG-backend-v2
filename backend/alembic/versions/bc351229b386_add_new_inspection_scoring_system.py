"""add_new_inspection_scoring_system

Revision ID: bc351229b386
Revises: 7ee5f81bdbbb
Create Date: 2025-10-11 16:21:40.648307

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bc351229b386"
down_revision: Union[str, Sequence[str], None] = "7ee5f81bdbbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add new inspection scoring functions and views."""

    # Create function to calculate household waste score (50 points max)
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
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate road cleaning score (10 points max)
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
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate drain cleaning score (30 points max)
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

        -- Drain waste collected on roadside (inverted scoring, 10 points)
        IF drain_waste_colllected_on_roadside IS FALSE THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate community sanitation score (40 points max)
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
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate other inspection score (50 points max)
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
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate complete inspection score
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
        -- Get household waste points
        SELECT calculate_household_waste_score(
            hw.waste_collection_frequency::TEXT,
            hw.dry_wet_vehicle_segregation,
            hw.covered_collection_in_vehicles,
            hw.waste_disposed_at_rrc,
            hw.waste_collection_vehicle_functional
        ) INTO household_points
        FROM inspection_household_waste_collection_and_disposal_inspection_items hw
        WHERE hw.id = inspection_id;

        -- Get road cleaning points
        SELECT calculate_road_cleaning_score(rd.road_cleaning_frequency::TEXT) INTO road_points
        FROM inspection_road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get drain cleaning points
        SELECT calculate_drain_cleaning_score(
            rd.drain_cleaning_frequency::TEXT,
            rd.disposal_of_sludge_from_drains,
            rd.drain_waste_colllected_on_roadside
        ) INTO drain_points
        FROM inspection_road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get community sanitation points
        SELECT calculate_community_sanitation_score(
            cs.csc_cleaning_frequency::TEXT,
            cs.electricity_and_water,
            cs.csc_used_by_community,
            cs.pink_toilets_cleaning
        ) INTO community_points
        FROM inspection_community_sanitation_inspection_items cs
        WHERE cs.id = inspection_id;

        -- Get other inspection points
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

        -- Return section scores and overall
        RETURN QUERY SELECT
            ROUND((COALESCE(household_points, 0) / 50.0) * 100, 2),
            ROUND((COALESCE(road_points, 0) / 10.0) * 100, 2),
            ROUND((COALESCE(drain_points, 0) / 30.0) * 100, 2),
            ROUND((COALESCE(community_points, 0) / 40.0) * 100, 2),
            ROUND((COALESCE(other_points, 0) / 50.0) * 100, 2),
            ROUND((total_points / 180.0) * 100, 2),
            total_points,
            total_max;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create view for inspections with scores
    op.execute("""
    CREATE OR REPLACE VIEW inspection_scores AS
    SELECT
        i.id,
        i.village_id,
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

    # Create function to get village inspection analytics
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

    # Create function to get GP (village group) inspection analytics
    op.execute("""
    CREATE OR REPLACE FUNCTION get_gp_inspection_analytics(
        gp_id_param INTEGER,
        start_date_param DATE DEFAULT NULL,
        end_date_param DATE DEFAULT NULL
    ) RETURNS TABLE(
        gp_id INTEGER,
        total_villages BIGINT,
        inspected_villages BIGINT,
        average_score DECIMAL(5,2),
        coverage_percentage DECIMAL(5,2)
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            gp_id_param,
            COUNT(DISTINCT v.id) as total_villages,
            COUNT(DISTINCT CASE WHEN is_inspected.village_id IS NOT NULL THEN v.id END) as inspected_villages,
            ROUND(AVG(COALESCE(is_inspected.average_score, 0)), 2) as average_score,
            ROUND((COUNT(DISTINCT CASE WHEN is_inspected.village_id IS NOT NULL THEN v.id END) * 100.0) / COUNT(DISTINCT v.id), 2) as coverage_percentage
        FROM villages v
        LEFT JOIN (
            SELECT village_id, AVG(overall_score) as average_score
            FROM inspection_scores
            WHERE (start_date_param IS NULL OR date >= start_date_param)
            AND (end_date_param IS NULL OR date <= end_date_param)
            GROUP BY village_id
        ) is_inspected ON v.id = is_inspected.village_id
        WHERE v.id = gp_id_param;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function to get block inspection analytics
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

    # Create function to get district inspection analytics
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

    # Create function to get state inspection analytics
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


def downgrade() -> None:
    """Downgrade schema: Remove new inspection scoring functions and views."""

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS get_state_inspection_analytics(DATE, DATE);")
    op.execute(
        "DROP FUNCTION IF EXISTS get_district_inspection_analytics(INTEGER, DATE, DATE);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS get_block_inspection_analytics(INTEGER, DATE, DATE);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS get_gp_inspection_analytics(INTEGER, DATE, DATE);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS get_village_inspection_analytics(INTEGER, DATE, DATE);"
    )
    op.execute("DROP FUNCTION IF EXISTS calculate_inspection_score(INTEGER);")
    op.execute(
        "DROP FUNCTION IF EXISTS calculate_other_inspection_score(BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS calculate_community_sanitation_score(TEXT, BOOLEAN, BOOLEAN, BOOLEAN);"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS calculate_drain_cleaning_score(TEXT, BOOLEAN, BOOLEAN);"
    )
    op.execute("DROP FUNCTION IF EXISTS calculate_road_cleaning_score(TEXT);")
    op.execute(
        "DROP FUNCTION IF EXISTS calculate_household_waste_score(TEXT, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN);"
    )

    # Drop view
    op.execute("DROP VIEW IF EXISTS inspection_scores;")
