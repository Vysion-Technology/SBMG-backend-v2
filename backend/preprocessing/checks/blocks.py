"""Module to process block data files."""

import pandas as pd  # type: ignore


def match_district_blocks_pair(
    blocks_df: pd.DataFrame,
    gps_df: pd.DataFrame,
    blocks_file_district_name_column: str,
    gps_file_district_name_column: str,
    blocks_file_block_name_column: str,
    gps_file_block_name_column: str,
) -> None:
    """Match the number of unique districts and block pairs between blocks and GPS data files."""
    # Create district-block pairs from both dataframes
    blocks_pairs = blocks_df[[blocks_file_district_name_column, blocks_file_block_name_column]].drop_duplicates()

    gps_pairs = gps_df[[gps_file_district_name_column, gps_file_block_name_column]].drop_duplicates()

    # Create a tuple column for easier comparison (convert to uppercase for case-insensitive matching)
    blocks_pairs["pair"] = blocks_pairs.apply(
        lambda x: (  # type: ignore
            str(x[blocks_file_district_name_column]).strip().upper(),  # type: ignore
            str(x[blocks_file_block_name_column]).strip().upper(),  # type: ignore
        ),
        axis=1,
    )
    gps_pairs["pair"] = gps_pairs.apply(
        lambda x: (  # type: ignore
            str(x[gps_file_district_name_column]).strip().upper(),  # type: ignore
            str(x[gps_file_block_name_column]).strip().upper(),  # type: ignore
        ),
        axis=1,
    )

    # Get unique pairs as sets
    blocks_set = set(blocks_pairs["pair"])
    gps_set = set(gps_pairs["pair"])

    # Calculate statistics
    print("\n" + "=" * 80)
    print("DISTRICT-BLOCK PAIR MATCHING REPORT")
    print("=" * 80)

    print(f"\nTotal unique district-block pairs in blocks file: {len(blocks_set)}")
    print(f"Total unique district-block pairs in GPS file: {len(gps_set)}")

    # Find common pairs
    common_pairs = blocks_set.intersection(gps_set)
    print(f"\nCommon pairs (present in both files): {len(common_pairs)}")

    # Find pairs only in blocks file
    only_in_blocks = blocks_set - gps_set
    if only_in_blocks:
        print(f"\nPairs only in blocks file ({len(only_in_blocks)}):")
        for district, block in sorted(only_in_blocks):
            print(f"  - {district} / {block}")
    else:
        print("\nAll pairs from blocks file are present in GPS file ✓")

    # Find pairs only in GPS file
    only_in_gps = gps_set - blocks_set
    if only_in_gps:
        print(f"\nPairs only in GPS file ({len(only_in_gps)}):")
        for district, block in sorted(only_in_gps):
            print(f"  - {district} / {block}")
    else:
        print("\nAll pairs from GPS file are present in blocks file ✓")

    # Calculate match percentage
    if len(blocks_set) > 0:
        match_percentage = (len(common_pairs) / len(blocks_set)) * 100
        print(f"\nMatch percentage (blocks file as reference): {match_percentage:.2f}%")

    if len(gps_set) > 0:
        match_percentage_gps = (len(common_pairs) / len(gps_set)) * 100
        print(f"Match percentage (GPS file as reference): {match_percentage_gps:.2f}%")

    # Summary
    print("\n" + "=" * 80)
    if blocks_set == gps_set:
        print("✓ PERFECT MATCH: Both files have identical district-block pairs")
    else:
        print("⚠ MISMATCH DETECTED: Files have different district-block pairs")
        print(f"Difference: ", blocks_set.symmetric_difference(gps_set))
        assert False, "Mismatch detected between blocks and GPS files. Please check the data files."
    print("=" * 80 + "\n")
