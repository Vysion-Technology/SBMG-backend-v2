"""Module to create bulk attendance records."""

import asyncio
from datetime import date, timedelta
import random
from typing import List
from sqlalchemy import insert, select

from database import get_db

from models.database.attendance import DailyAttendance as Attendance
from models.database.contractor import Contractor


async def get_all_contractors() -> List[Contractor]:
    """Fetch all contractor attendance records from the database."""
    async for db in get_db():
        result = await db.execute(select(Contractor))
        return list(result.scalars().all())
    return []


start_date = date(2025, 4, 1)
end_date = date(2025, 10, 31)

all_dates = [
    start_date + timedelta(days=x)
    for x in range((end_date - start_date).days + 1)
    if (start_date + timedelta(days=x)).weekday() < 6  # Exclude Sundays
]


async def create_contractor_attendance(contractor: Contractor) -> None:
    """Create attendance record for a given contractor."""
    if contractor.id <= 9104:
        return
    async for db in get_db():
        print(f"Creating attendance for contractor: {contractor.id}")
        # Generate a random number between 30 and 99
        attendance_percentage = 30 + hash(contractor.id) % 70
        attendance_count = (attendance_percentage * len(all_dates)) // 100

        # Create attendance records for the selected dates
        selected_dates = random.sample(all_dates, attendance_count)
        attendances: list[Attendance] = []
        for attendance_date in selected_dates:
            attendance = Attendance(
                contractor_id=contractor.id,
                date=attendance_date,
                start_lat="26.9124",
                start_long="75.7873",
            )
            attendances.append(attendance)
        # Insert in batches of 1000
        batch_size = 1000
        for i in range(0, len(attendances), batch_size):
            batch = attendances[i : i + batch_size]
            await db.execute(
                insert(Attendance).values([
                    {
                        "contractor_id": att.contractor_id,
                        "date": att.date,
                        "start_lat": att.start_lat,
                        "start_long": att.start_long,
                    }
                    for att in batch
                ])
            )
        await db.commit()
        print(f"Created {len(attendances)} attendance records for contractor {contractor.id}.")


async def create_bulk_attendances() -> None:
    """Create bulk attendance records in the database."""
    print("Creating bulk attendance records...")
    contractors = await get_all_contractors()
    print(f"Found {len(contractors)} contractors.")
    await asyncio.gather(*[create_contractor_attendance(contractor) for contractor in contractors])
    print("Attendance records created successfully!")


async def main():
    """Main function to create bulk attendance records."""
    await create_bulk_attendances()


if __name__ == "__main__":
    asyncio.run(main())
