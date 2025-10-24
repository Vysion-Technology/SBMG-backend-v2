"""fix_inspection_item_table_names

Revision ID: a9b3c4d5e6f7
Revises: 81a1114ba1a4
Create Date: 2025-10-24 17:37:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b3c4d5e6f7'
down_revision: Union[str, None] = '81a1114ba1a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix calculate_inspection_score function with correct table names
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
            ROUND((COALESCE(other_points, 0) / 50.0) * 100, 2),      -- Other inspection score %
            ROUND((total_points / total_max::DECIMAL) * 100, 2),     -- Overall score %
            total_points,
            total_max;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)


def downgrade() -> None:
    # Revert to previous version with incorrect table names
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
        FROM community_sanitation_inspection_items cs
        WHERE cs.id = inspection_id;

        -- Get other inspection points (50 points max)
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

        -- Return section scores (as percentages) and overall
        RETURN QUERY SELECT
            ROUND((COALESCE(household_points, 0) / 50.0) * 100, 2),  -- Household waste score %
            ROUND((COALESCE(road_points, 0) / 10.0) * 100, 2),       -- Road cleaning score %
            ROUND((COALESCE(drain_points, 0) / 30.0) * 100, 2),      -- Drain cleaning score %
            ROUND((COALESCE(community_points, 0) / 40.0) * 100, 2),  -- Community sanitation score %
            ROUND((COALESCE(other_points, 0) / 50.0) * 100, 2),      -- Other inspection score %
            ROUND((total_points / total_max::DECIMAL) * 100, 2),     -- Overall score %
            total_points,
            total_max;
    END;
    $$ LANGUAGE plpgsql STABLE;
    """)
