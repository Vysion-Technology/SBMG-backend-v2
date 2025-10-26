"""
Script to update complaint states using database service:
- Convert 70% of OPEN complaints to RESOLVED
- Convert 80% of those RESOLVED complaints to VERIFIED
- Convert 60% of those VERIFIED complaints to CLOSED

Usage: python update_complaint_states.py
"""

import asyncio
import random
from typing import List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from models.database.complaint import Complaint, ComplaintStatus


# Configuration
PERCENTAGE_TO_RESOLVE = 0.7  # 70% of OPEN complaints
PERCENTAGE_TO_VERIFY = 0.8   # 80% of RESOLVED complaints
PERCENTAGE_TO_CLOSE = 0.6    # 60% of VERIFIED complaints

# Timestamp configuration (in days)
RESOLVED_DAYS_AGO_MIN = 1
RESOLVED_DAYS_AGO_MAX = 30
VERIFIED_DAYS_AFTER_MIN = 1
VERIFIED_DAYS_AFTER_MAX = 7
CLOSED_DAYS_AFTER_MIN = 1
CLOSED_DAYS_AFTER_MAX = 5


async def get_or_create_status(db: AsyncSession, status_name: str, description: str) -> ComplaintStatus:
    """Get or create a complaint status"""
    result = await db.execute(
        select(ComplaintStatus).where(ComplaintStatus.name == status_name)
    )
    status = result.scalar_one_or_none()
    
    if not status:
        status = ComplaintStatus(name=status_name, description=description)
        db.add(status)
        await db.commit()
        await db.refresh(status)
    
    return status


async def update_to_resolved(
    db: AsyncSession,
    complaints: List[Complaint],
    resolved_status: ComplaintStatus,
    percentage: float
) -> List[Complaint]:
    """Update complaints to RESOLVED status"""
    num_to_resolve = int(len(complaints) * percentage)
    complaints_to_resolve = random.sample(complaints, num_to_resolve)
    
    for complaint in complaints_to_resolve:
        # Set resolved timestamp to sometime between created_at and now
        days_ago = random.randint(RESOLVED_DAYS_AGO_MIN, RESOLVED_DAYS_AGO_MAX)
        resolved_at = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
        
        complaint.status_id = resolved_status.id
        complaint.resolved_at = resolved_at
        complaint.updated_at = resolved_at
    
    await db.commit()
    return complaints_to_resolve


async def update_to_verified(
    db: AsyncSession,
    complaints: List[Complaint],
    verified_status: ComplaintStatus,
    percentage: float
) -> List[Complaint]:
    """Update complaints to VERIFIED status"""
    num_to_verify = int(len(complaints) * percentage)
    complaints_to_verify = random.sample(complaints, num_to_verify)
    
    for complaint in complaints_to_verify:
        # Set verified timestamp to sometime after resolved_at
        if complaint.resolved_at:
            days_after = random.randint(VERIFIED_DAYS_AFTER_MIN, VERIFIED_DAYS_AFTER_MAX)
            verified_at = complaint.resolved_at + timedelta(days=days_after)
        else:
            verified_at = datetime.now(tz=timezone.utc) - timedelta(days=random.randint(1, 20))
        
        complaint.status_id = verified_status.id
        complaint.verified_at = verified_at
        complaint.updated_at = verified_at
    
    await db.commit()
    return complaints_to_verify


async def update_to_closed(
    db: AsyncSession,
    complaints: List[Complaint],
    closed_status: ComplaintStatus,
    percentage: float
) -> List[Complaint]:
    """Update complaints to CLOSED status"""
    num_to_close = int(len(complaints) * percentage)
    complaints_to_close = random.sample(complaints, num_to_close)
    
    for complaint in complaints_to_close:
        # Set closed timestamp to sometime after verified_at
        if complaint.verified_at:
            days_after = random.randint(CLOSED_DAYS_AFTER_MIN, CLOSED_DAYS_AFTER_MAX)
            closed_at = complaint.verified_at + timedelta(days=days_after)
        else:
            closed_at = datetime.now(tz=timezone.utc) - timedelta(days=random.randint(1, 10))
        
        complaint.status_id = closed_status.id
        complaint.closed_at = closed_at
        complaint.updated_at = closed_at
    
    await db.commit()
    return complaints_to_close


async def update_complaint_states():
    """Main function to update complaint states"""
    async with AsyncSessionLocal() as db:
        try:
            print("=" * 80)
            print("COMPLAINT STATE UPDATE SCRIPT")
            print("=" * 80)
            print("Configuration:")
            print(f"  - {int(PERCENTAGE_TO_RESOLVE * 100)}% of OPEN → RESOLVED")
            print(f"  - {int(PERCENTAGE_TO_VERIFY * 100)}% of RESOLVED → VERIFIED")
            print(f"  - {int(PERCENTAGE_TO_CLOSE * 100)}% of VERIFIED → CLOSED")
            print("=" * 80)
            
            # Get or create all statuses
            print("\n[1/5] Fetching/Creating complaint statuses...")
            open_status = await get_or_create_status(db, "OPEN", "Complaint is open and pending")
            resolved_status = await get_or_create_status(db, "RESOLVED", "Complaint has been resolved")
            verified_status = await get_or_create_status(db, "VERIFIED", "Complaint resolution has been verified")
            closed_status = await get_or_create_status(db, "CLOSED", "Complaint is closed")
            
            print(f"   ✓ OPEN status ID: {open_status.id}")
            print(f"   ✓ RESOLVED status ID: {resolved_status.id}")
            print(f"   ✓ VERIFIED status ID: {verified_status.id}")
            print(f"   ✓ CLOSED status ID: {closed_status.id}")
            
            # Step 1: Get all OPEN complaints
            print("\n[2/5] Fetching OPEN complaints...")
            result = await db.execute(
                select(Complaint).where(Complaint.status_id == open_status.id)
            )
            open_complaints: List[Complaint] = list(result.scalars().all())
            total_open = len(open_complaints)
            print(f"   ✓ Found {total_open} OPEN complaints")
            
            if total_open == 0:
                print("\n⚠️  No OPEN complaints found. Exiting...")
                return
            
            # Step 2: Convert to RESOLVED
            print(f"\n[3/5] Converting {int(PERCENTAGE_TO_RESOLVE * 100)}% of OPEN complaints to RESOLVED...")
            complaints_resolved = await update_to_resolved(
                db, open_complaints, resolved_status, PERCENTAGE_TO_RESOLVE
            )
            print(f"   ✓ Updated {len(complaints_resolved)} complaints to RESOLVED")
            
            # Step 3: Convert to VERIFIED
            print(f"\n[4/5] Converting {int(PERCENTAGE_TO_VERIFY * 100)}% of RESOLVED complaints to VERIFIED...")
            complaints_verified = await update_to_verified(
                db, complaints_resolved, verified_status, PERCENTAGE_TO_VERIFY
            )
            print(f"   ✓ Updated {len(complaints_verified)} complaints to VERIFIED")
            
            # Step 4: Convert to CLOSED
            print(f"\n[5/5] Converting {int(PERCENTAGE_TO_CLOSE * 100)}% of VERIFIED complaints to CLOSED...")
            complaints_closed = await update_to_closed(
                db, complaints_verified, closed_status, PERCENTAGE_TO_CLOSE
            )
            print(f"   ✓ Updated {len(complaints_closed)} complaints to CLOSED")
            
            # Print summary
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(f"Total OPEN complaints:              {total_open}")
            print(f"Converted to RESOLVED (70%):        {len(complaints_resolved)}")
            print(f"Converted to VERIFIED (80% of R):   {len(complaints_verified)}")
            print(f"Converted to CLOSED (60% of V):     {len(complaints_closed)}")
            print(f"\nRemaining OPEN:                     {total_open - len(complaints_resolved)}")
            print(f"Remaining RESOLVED:                 {len(complaints_resolved) - len(complaints_verified)}")
            print(f"Remaining VERIFIED:                 {len(complaints_verified) - len(complaints_closed)}")
            print(f"Final CLOSED:                       {len(complaints_closed)}")
            print("=" * 80)
            print("✅ Script completed successfully!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Error occurred: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_complaint_states())
