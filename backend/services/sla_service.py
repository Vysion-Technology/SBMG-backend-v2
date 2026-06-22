
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy import select, and_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.database.complaint import Complaint, ComplaintStatus, ComplaintComment

logger = logging.getLogger(__name__)

class SLAService:
    _should_stop = False
    CHECK_INTERVAL_SECONDS = 43200  # Check SLA breaches every 12 hours

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_monitoring(self):
        """
        Starts the periodic SLA breach monitoring loop.
        """
        SLAService._should_stop = False
        logger.info("Starting periodic SLA monitoring (every 12 hours)")
        
        while not SLAService._should_stop:
            try:
                await self.run_sla_check()
            except Exception as e:
                logger.error(f"Error in periodic SLA monitoring: {e}")
            
            await asyncio.sleep(SLAService.CHECK_INTERVAL_SECONDS)

    def stop_monitoring(self):
        """
        Stops the periodic SLA monitoring.
        """
        logger.info("Stopping periodic SLA monitoring")
        SLAService._should_stop = True

    async def run_sla_check(self):
        """
        Runs the SLA check for all unresolved complaints.
        """
        logger.info("Starting SLA check...")
        
        # Define 'unresolved' statuses. Usually anything that isn't VERIFIED or CLOSED.
        # Once it is VERIFIED, it is considered resolved by the system.
        resolved_statuses = ["VERIFIED", "CLOSED", "INVALID"]
        
        # Get status IDs for resolved statuses
        status_query = select(ComplaintStatus).where(ComplaintStatus.name.in_(resolved_statuses))
        status_result = await self.db.execute(status_query)
        resolved_status_ids = [s.id for s in status_result.scalars().all()]
        
        # Query all complaints that are not resolved
        complaints_query = (
            select(Complaint)
            .where(not_(Complaint.status_id.in_(resolved_status_ids)))
            .options(selectinload(Complaint.status))
        )
        
        result = await self.db.execute(complaints_query)
        complaints = result.scalars().all()
        
        now = datetime.now(tz=timezone.utc)
        breaches_count = 0
        
        for complaint in complaints:
            days_elapsed = (now - complaint.created_at).days
            
            # Determine the current breach level based on elapsed time
            current_breach_level = None
            if days_elapsed >= 30:
                current_breach_level = "DISTRICT"
            elif days_elapsed >= 15:
                current_breach_level = "BLOCK"
            elif days_elapsed >= 7:
                current_breach_level = "GP"
            
            # If a breach level is identified and it's different from the last recorded breach level
            if current_breach_level and complaint.last_sla_breach_level != current_breach_level:
                await self._generate_sla_remark(complaint, current_breach_level, days_elapsed)
                complaint.last_sla_breach_level = current_breach_level
                breaches_count += 1
        
        await self.db.commit()
        logger.info(f"SLA check completed. {breaches_count} new breaches identified.")

    async def _generate_sla_remark(self, complaint: Complaint, level: str, days: int):
        """
        Generates an automatic remark entry for a complaint.
        """
        message = (
            f"[SLA BREACH - {level} LEVEL] This complaint remains unresolved after {days} days. "
            f"Administrative escalation triggered."
        )
        
        remark = ComplaintComment(
            complaint_id=complaint.id,
            comment=message,
            is_system_generated=True,
            commented_at=datetime.now(tz=timezone.utc)
        )
        
        self.db.add(remark)
        logger.info(f"Generated {level} SLA remark for complaint ID {complaint.id}")
