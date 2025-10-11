"""Remove inspection scoring functions

Revision ID: 7ee5f81bdbba
Revises: bfc3f9538ef6
Create Date: 2025-10-11 12:40:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7ee5f81bdbbb"
down_revision: Union[str, Sequence[str], None] = "1f40e69ca42e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Downgrade schema: Remove inspection scoring functions and views."""

    # Drop view
    op.execute("DROP VIEW IF EXISTS inspection_scores;")

    # Drop functions
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


def downgrade() -> None:
    """Upgrade schema: Add inspection scoring functions and views."""

    # Create function to calculate household waste score
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
        -- Waste collection frequency
        CASE waste_collection_frequency
            WHEN 'DAILY' THEN points := points + 10;
            WHEN 'ONCE_IN_THREE_DAYS' THEN points := points + 7;
            WHEN 'WEEKLY' THEN points := points + 3;
            ELSE points := points + 0;
        END CASE;

        -- Dry/wet vehicle segregation
        IF dry_wet_vehicle_segregation THEN
            points := points + 10;
        END IF;

        -- Covered collection in vehicles
        IF covered_collection_in_vehicles THEN
            points := points + 10;
        END IF;

        -- Waste disposed at RRC
        IF waste_disposed_at_rrc THEN
            points := points + 10;
        END IF;

        -- Waste collection vehicle functional
        IF waste_collection_vehicle_functional THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate road cleaning score
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

    # Create function to calculate drain cleaning score
    op.execute("""
    CREATE OR REPLACE FUNCTION calculate_drain_cleaning_score(
        drain_cleaning_frequency TEXT,
        disposal_of_sludge_from_drains BOOLEAN,
        drain_waste_colllected_on_roadside BOOLEAN
    ) RETURNS INTEGER AS $$
    DECLARE
        points INTEGER := 0;
    BEGIN
        -- Drain cleaning frequency
        CASE drain_cleaning_frequency
            WHEN 'WEEKLY' THEN points := points + 10;
            WHEN 'FORTNIGHTLY' THEN points := points + 5;
            WHEN 'MONTHLY' THEN points := points + 2;
            ELSE points := points + 0;
        END CASE;

        -- Disposal of sludge from drains
        IF disposal_of_sludge_from_drains THEN
            points := points + 10;
        END IF;

        -- Drain waste collected on roadside (inverted scoring)
        IF drain_waste_colllected_on_roadside IS FALSE THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate community sanitation score
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
        -- CSC cleaning frequency
        CASE csc_cleaning_frequency
            WHEN 'DAILY' THEN points := points + 10;
            WHEN 'ONCE_IN_THREE_DAYS' THEN points := points + 7;
            WHEN 'WEEKLY' THEN points := points + 3;
            ELSE points := points + 0;
        END CASE;

        -- Electricity and water
        IF electricity_and_water THEN
            points := points + 10;
        END IF;

        -- CSC used by community
        IF csc_used_by_community THEN
            points := points + 10;
        END IF;

        -- Pink toilets cleaning
        IF pink_toilets_cleaning THEN
            points := points + 10;
        END IF;

        RETURN points;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Create function to calculate other inspection score
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
        -- Firm paid regularly
        IF firm_paid_regularly THEN
            points := points + 10;
        END IF;

        -- Cleaning staff paid regularly
        IF cleaning_staff_paid_regularly THEN
            points := points + 10;
        END IF;

        -- Firm provided safety equipment
        IF firm_provided_safety_equipment THEN
            points := points + 10;
        END IF;

        -- Village visibly clean
        IF village_visibly_clean THEN
            points := points + 10;
        END IF;

        -- Rate chart displayed
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
        FROM household_waste_collection_and_disposal_inspection_items hw
        WHERE hw.id = inspection_id;

        -- Get road cleaning points
        SELECT calculate_road_cleaning_score(rd.road_cleaning_frequency::TEXT) INTO road_points
        FROM road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get drain cleaning points
        SELECT calculate_drain_cleaning_score(
            rd.drain_cleaning_frequency::TEXT,
            rd.disposal_of_sludge_from_drains,
            rd.drain_waste_colllected_on_roadside
        ) INTO drain_points
        FROM road_cleaning_inspection_items rd
        WHERE rd.id = inspection_id;

        -- Get community sanitation points
        SELECT calculate_community_sanitation_score(
            cs.csc_cleaning_frequency::TEXT,
            cs.electricity_and_water,
            cs.csc_used_by_community,
            cs.pink_toilets_cleaning
        ) INTO community_points
        FROM community_sanitation_inspection_items cs
        WHERE cs.id = inspection_id;

        -- Get other inspection points
        SELECT calculate_other_inspection_score(
            ot.firm_paid_regularly,
            ot.cleaning_staff_paid_regularly,
            ot.firm_provided_safety_equipment,
            ot.village_visibly_clean,
            ot.rate_chart_displayed
        ) INTO other_points
        FROM other_inspection_items ot
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
