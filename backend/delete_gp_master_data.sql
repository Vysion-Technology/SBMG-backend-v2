BEGIN;

-- Delete child tables of VillageData first
DELETE FROM survey_village_sbmg_assets;
DELETE FROM survey_village_gwm_assets;

-- Delete VillageData
DELETE FROM survey_village_data;

-- Delete 1:1 related tables of AnnualSurvey
DELETE FROM survey_work_order_details;
DELETE FROM survey_fund_sanctioned;
DELETE FROM survey_door_to_door_collection;
DELETE FROM survey_road_sweeping;
DELETE FROM survey_drain_cleaning;
DELETE FROM survey_csc_details;
DELETE FROM survey_swm_assets;
DELETE FROM survey_sbmg_year_targets;

-- Delete AnnualSurvey
DELETE FROM annual_surveys;

COMMIT;
