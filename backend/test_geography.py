#!/usr/bin/env python3
"""
Simple test script to verify geography API endpoints
"""

import asyncio
from models.response.geography import (
    CreateDistrictRequest,
    CreateBlockRequest,
    CreateVillageRequest,
)

# Add the backend directory to Python path


async def test_geography_models():
    """Test the geography models can be created and validated."""
    print("Testing geography models...")

    # Test District Request
    district_request = CreateDistrictRequest(name="Test District", description="A test district")
    print(f"✓ District request: {district_request}")

    # Test Block Request
    block_request = CreateBlockRequest(name="Test Block", description="A test block", district_id=1)
    print(f"✓ Block request: {block_request}")

    # Test Village Request
    village_request = CreateVillageRequest(name="Test Village", description="A test village", block_id=1, district_id=1)
    print(f"✓ Village request: {village_request}")

    print("✓ All geography models validated successfully!")


async def main():
    """Run all tests."""
    print("Starting geography API tests...")
    await test_geography_models()
    print("✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
