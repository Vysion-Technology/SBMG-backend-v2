"""Script to analyze unique districts in blocks and GPS data files."""

import os

import pandas as pd

from preprocessing.checks.blocks import match_district_blocks_pair
from preprocessing.checks.districts import match_district_count_and_names

from preprocessing.creation.districts import create_district_file_if_not_exists
from preprocessing.creation.blocks import refine_block_file
from preprocessing.creation.gps import refine_gram_panchayat_file

BASE_DIR = "preprocessing"

BLOCKS_FILE = os.path.join(BASE_DIR, "data", "blocks.csv")
GPS_FILE = os.path.join(BASE_DIR, "data", "gps.csv")


# Get the number of unique districts in each file

BLOCKS_DF = pd.read_csv(BLOCKS_FILE)  # type: ignore
GPS_DF = pd.read_csv(GPS_FILE)  # type: ignore

BLOCKS_FILE_DISTRICT_NAME_COLUMN = "New District"
GPS_FILE_DISTRICT_NAME_COLUMN = "New District"
BLOCKS_FILE_BLOCK_NAME_COLUMN = "Block Name"
GPS_FILE_BLOCK_NAME_COLUMN = "Block Name"
GP_ID_COLUMN_NAME = "GP ID"
BLOCK_ID_COLUMN_NAME = "Block ID"


match_district_count_and_names(
    BLOCKS_DF,
    GPS_DF,
    BLOCKS_FILE_DISTRICT_NAME_COLUMN,
    GPS_FILE_DISTRICT_NAME_COLUMN,
)


match_district_blocks_pair(
    BLOCKS_DF,
    GPS_DF,
    BLOCKS_FILE_DISTRICT_NAME_COLUMN,
    GPS_FILE_DISTRICT_NAME_COLUMN,
    BLOCKS_FILE_BLOCK_NAME_COLUMN,
    GPS_FILE_BLOCK_NAME_COLUMN,
)

create_district_file_if_not_exists(BLOCKS_FILE, os.path.join(BASE_DIR, "data", "districts.csv"))


DISTRICT_FILE = os.path.join(BASE_DIR, "data", "districts.csv")

refine_block_file(
    DISTRICT_FILE,
    BLOCKS_FILE,
    BLOCK_ID_COLUMN_NAME,
)

refine_gram_panchayat_file(
    BLOCKS_FILE,
    GPS_FILE,
    GP_ID_COLUMN_NAME,
)
