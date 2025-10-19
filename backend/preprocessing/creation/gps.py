"""Refine the Gram Panchayat CSV file by merging it with district data to include district and block IDs."""

import pandas as pd  # type: ignore

BLOCK_ID_COLUMN = "ID"
DISTRICT_ID_COLUMN = "District ID"
DISTRICT_NAME_COLUMN = "New District"
BLOCK_NAME_COLUMN = "Block Name"
GP_ID_COLUMN = "GP ID"


def refine_gram_panchayat_file(
    blocks_file: str,
    gps_file: str,
    gp_id_column_name: str,
) -> None:
    """Refine the Gram Panchayat file by adding district and block IDs.

    This function reads the blocks file which already contains District ID and Block ID,
    and maps them to the GP file based on matching District Name and Block Name.
    """
    # Load the blocks and GPS data
    blocks_df = pd.read_csv(blocks_file)
    gps_df = pd.read_csv(gps_file)
    # Drop the District ID and Block ID column if it exists to avoid conflicts
    # Temporarily keep both District and Block name values in capitals
    gps_df[DISTRICT_NAME_COLUMN] = gps_df[DISTRICT_NAME_COLUMN].str.upper()
    gps_df[BLOCK_NAME_COLUMN] = gps_df[BLOCK_NAME_COLUMN].str.upper()
    gps_df = gps_df.drop(
        columns=[
            DISTRICT_ID_COLUMN,
            BLOCK_ID_COLUMN,
            gp_id_column_name,
        ],
        errors="ignore",
    )
    # Lookup the district ID from blocks_df with case insensitivity and insert the values in gps_df
    gps_df = gps_df.merge(
        blocks_df[[DISTRICT_NAME_COLUMN, DISTRICT_ID_COLUMN]],
        on=[DISTRICT_NAME_COLUMN],
    )
    # Save the refined GPS file
    gps_df.to_csv(gps_file, index=False)
    # Lookup the block ID from blocks_df with case insensitivity and insert the values in gps_df
    gps_df = gps_df.merge(
        blocks_df[[DISTRICT_NAME_COLUMN, BLOCK_NAME_COLUMN, BLOCK_ID_COLUMN]],
        on=[DISTRICT_NAME_COLUMN, BLOCK_NAME_COLUMN],
    )
    input("Have you reviewed?")
    # Save the refined GPS file
    # Save the file with an index starting from 1
    gps_df = gps_df.drop_duplicates()
    # Reset index from 1
    gps_df.index = range(1, len(gps_df) + 1)
    gps_df.to_csv(gps_file, index=True)
    print(f"Refined GPS file saved to {gps_file}")
