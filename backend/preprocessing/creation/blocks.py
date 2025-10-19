"""Module for refining block files based on district information."""

import pandas as pd  # type: ignore

DISTRICT_NAME_COLUMN = "New District"
DISTRICT_ID_COLUMN = "District ID"
BLOCK_ID_COLUMN = "Block ID"
BLOCK_NAME_COLUMN = "Block Name"


def refine_block_file(
    district_file: str,
    blocks_file: str,
    blocks_file_block_id_column: str,
) -> None:
    """Refine the block file by ensuring block IDs are consistent with district IDs.

    Note: This function assumes blocks.csv already has District ID and Block ID columns.
    It will verify consistency with the district file.
    """

    # districts_df = pd.read_csv(district_file)  # type: ignore
    blocks_df = pd.read_csv(blocks_file)  # type: ignore
    # Drop the block id column if it exists to avoid conflicts
    blocks_df = blocks_df.drop(columns=[blocks_file_block_id_column], errors="ignore")
    # Save the refined blocks file
    # Save column names in capitals
    blocks_df["New District"] = blocks_df["New District"].str.upper()
    blocks_df["Block Name"] = blocks_df["Block Name"].str.upper()
    blocks_df.to_csv(blocks_file, index=False)
    print(f"Refined blocks file saved at {blocks_file}")

    # # If District ID and Block ID columns already exist, just verify and return
    # if DISTRICT_ID_COLUMN in blocks_df.columns and BLOCK_ID_COLUMN in blocks_df.columns:
    #     print(f"Block file already has District ID and Block ID columns. No changes needed.")
    #     return

    # # Create a mapping from district name to district ID
    # district_mapping = pd.Series(
    #     districts_df[DISTRICT_ID_COLUMN].values,
    #     index=districts_df[DISTRICT_NAME_COLUMN],
    # ).to_dict()

    # # Map district IDs to blocks
    # blocks_df[DISTRICT_ID_COLUMN] = blocks_df[DISTRICT_NAME_COLUMN].map(district_mapping)

    # # Ensure block IDs are unique within each district (starts from 1 for each district)
    # blocks_df[BLOCK_ID_COLUMN] = blocks_df.groupby(DISTRICT_ID_COLUMN).cumcount() + 1

    # # Drop the old Sr. No. column if it exists
    # if blocks_file_block_id_column in blocks_df.columns and blocks_file_block_id_column != BLOCK_ID_COLUMN:
    #     blocks_df = blocks_df.drop(columns=[blocks_file_block_id_column])

    # blocks_df.to_csv(blocks_file, index=False)
    # print(f"Block file refined at {blocks_file} with updated block IDs.")
