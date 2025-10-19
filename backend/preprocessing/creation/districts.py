"""Create district file from blocks file if it does not exist."""

import os
import pandas as pd


def create_district_file_if_not_exists(
    blocks_file: str,
    district_file_path: str,
) -> None:
    """Create a district file if it does not already exist."""

    if os.path.exists(district_file_path):
        print(f"District file already exists at {district_file_path}. Skipping creation.")
        # Just convert the cell values to capitals
        district_df = pd.read_csv(district_file_path)  # type: ignore
        district_df["New District"] = district_df["New District"].str.upper()
        district_df.to_csv(district_file_path, index=False)
        return

    blocks_df = pd.read_csv(blocks_file)  # type: ignore

    district_name_column = "New District"
    district_id_column = "District ID"

    # Assign a unique ID to each district
    unique_districts = blocks_df[district_name_column].drop_duplicates().reset_index(drop=True)
    district_ids = range(1, len(unique_districts) + 1)
    district_df = pd.DataFrame({
        district_id_column: district_ids,
        district_name_column: unique_districts,
    })
    # Save all the cells in capitals for column "New District"
    district_df[district_name_column] = district_df[district_name_column].str.upper()
    district_df.to_csv(district_file_path, index=False)
    print(f"District file created at {district_file_path} with {len(district_df)} unique districts.")
