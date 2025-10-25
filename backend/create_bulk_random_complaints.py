import asyncio
import aiohttp
import random
from typing import List
import time

# Configuration
URL = "http://localhost:8000/api/v1/citizen/with-media"
HEADERS = {
    "accept": "application/json",
    "token": "6669084e-26b3-4db7-8737-7157ad00f880"
}
TOTAL_COMPLAINTS = 100000
CONCURRENT_REQUESTS = 100  # Number of concurrent requests
MIN_GP_ID = 1
MAX_GP_ID = 11207

# Sample data for generating varied complaints
COMPLAINT_TYPES = ["1", "2", "3", "4", "5"]
DESCRIPTIONS = [
    "Street light not working",
    "Garbage not collected",
    "Water supply issue",
    "Road repair needed",
    "Drainage problem",
    "Public toilet maintenance required",
    "Sewage overflow",
    "Broken infrastructure",
    "Waste management issue",
    "Sanitation problem"
]
LOCATIONS = [
    "Main Market Area",
    "Residential Colony",
    "Village Center",
    "Near School",
    "Hospital Road",
    "Government Office Area",
    "Bus Stand",
    "Railway Station Road",
    "Agricultural Area",
    "Community Center"
]


async def create_complaint(session: aiohttp.ClientSession, complaint_id: int) -> dict:
    """Create a single complaint asynchronously"""
    payload = {
        "complaint_type_id": random.choice(COMPLAINT_TYPES),
        "gp_id": str(random.randint(MIN_GP_ID, MAX_GP_ID)),
        "description": random.choice(DESCRIPTIONS),
        "lat": str(random.uniform(24.0, 30.5)),  # Rajasthan latitude range
        "long": str(random.uniform(69.5, 78.5)),  # Rajasthan longitude range
        "location": random.choice(LOCATIONS),
    }
    
    try:
        async with session.post(URL, headers=HEADERS, data=payload) as response:
            result = await response.text()
            status = response.status
            return {
                "id": complaint_id,
                "status": status,
                "success": status == 200,
                "response": result[:100] if len(result) > 100 else result
            }
    except Exception as e:
        return {
            "id": complaint_id,
            "status": 0,
            "success": False,
            "error": str(e)
        }


async def create_complaints_batch(start_id: int, batch_size: int) -> List[dict]:
    """Create a batch of complaints concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(start_id, start_id + batch_size):
            tasks.append(create_complaint(session, i))
        
        results = await asyncio.gather(*tasks)
        return results


async def main():
    """Main function to orchestrate bulk complaint creation"""
    print(f"Starting bulk complaint creation...")
    print(f"Total complaints to create: {TOTAL_COMPLAINTS}")
    print(f"Concurrent requests per batch: {CONCURRENT_REQUESTS}")
    print(f"GP ID range: {MIN_GP_ID} to {MAX_GP_ID}")
    print("-" * 60)
    
    start_time = time.time()
    total_success = 0
    total_failed = 0
    
    # Process in batches
    batches = (TOTAL_COMPLAINTS + CONCURRENT_REQUESTS - 1) // CONCURRENT_REQUESTS
    
    for batch_num in range(batches):
        batch_start = batch_num * CONCURRENT_REQUESTS
        batch_size = min(CONCURRENT_REQUESTS, TOTAL_COMPLAINTS - batch_start)
        
        print(f"\nProcessing batch {batch_num + 1}/{batches} (Complaints {batch_start + 1} to {batch_start + batch_size})...")
        
        batch_start_time = time.time()
        results = await create_complaints_batch(batch_start, batch_size)
        batch_end_time = time.time()
        
        # Count successes and failures
        batch_success = sum(1 for r in results if r.get("success", False))
        batch_failed = batch_size - batch_success
        
        total_success += batch_success
        total_failed += batch_failed
        
        # Progress update
        elapsed = batch_end_time - batch_start_time
        rate = batch_size / elapsed if elapsed > 0 else 0
        
        print(f"  Batch completed in {elapsed:.2f}s ({rate:.2f} complaints/sec)")
        print(f"  Success: {batch_success}, Failed: {batch_failed}")
        print(f"  Total progress: {batch_start + batch_size}/{TOTAL_COMPLAINTS} ({((batch_start + batch_size) / TOTAL_COMPLAINTS * 100):.1f}%)")
        
        # Small delay to avoid overwhelming the server
        if batch_num < batches - 1:
            await asyncio.sleep(0.5)
    
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total complaints created: {total_success}/{TOTAL_COMPLAINTS}")
    print(f"Total failed: {total_failed}")
    print(f"Total time: {total_elapsed:.2f} seconds")
    print(f"Average rate: {TOTAL_COMPLAINTS / total_elapsed:.2f} complaints/second")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
