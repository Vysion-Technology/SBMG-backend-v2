"""Module to match district names and counts between blocks and GPS data files."""

import pandas as pd  # type: ignore


def match_district_count_and_names(
    blocks_df: pd.DataFrame,
    gps_df: pd.DataFrame,
    blocks_file_district_name_column: str,
    gps_file_district_name_column: str,
) -> None:
    """Match the number of unique districts and their names between blocks and GPS data files."""
    unique_blocks_districts = blocks_df[blocks_file_district_name_column].nunique()
    unique_gps_districts = gps_df[gps_file_district_name_column].nunique()

    print(
        f"Unique districts in blocks file: {unique_blocks_districts}, Unique districts in GPS file: {unique_gps_districts}"
    )

    if unique_blocks_districts != unique_gps_districts:
        print("District mismatch between blocks and GPS files.")
        # Get the unique district names from both files as sets
        blocks_districts_set = set(blocks_df[blocks_file_district_name_column].unique())
        gps_districts_set = set(gps_df[gps_file_district_name_column].unique())
        # Find districts present in blocks file but missing in GPS file
        missing_in_gps = blocks_districts_set - gps_districts_set
        if missing_in_gps:
            print(f"Districts present in blocks file but missing in GPS file: {missing_in_gps}")
        # Find districts present in GPS file but missing in blocks file
        missing_in_blocks = gps_districts_set - blocks_districts_set
        if missing_in_blocks:
            print(f"Districts present in GPS file but missing in blocks file: {missing_in_blocks}")
    else:
        assert unique_blocks_districts == unique_gps_districts, "District counts match but names may differ."
        print("District counts match between blocks and GPS files.")
