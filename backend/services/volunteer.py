from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from models.database.volunteer import VolunteerRegistration
from models.database.auth import PublicUser
from models.requests.volunteer import VolunteerRegistrationRequest
from services.s3_service import s3_service


class VolunteerService:
    """Service layer for volunteer operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_volunteer(
        self,
        public_user: PublicUser,
        request: VolunteerRegistrationRequest,
        photo: Optional[UploadFile] = None
    ) -> VolunteerRegistration:
        """Register a new volunteer."""
        
        photo_url = None
        if photo:
            s3_key = await s3_service.upload_file(photo, folder="volunteers/photos")
            photo_url = s3_service.get_file_url(s3_key)

        volunteer = VolunteerRegistration(
            public_user_id=public_user.id,
            full_name=request.full_name,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            aadhar_number=request.aadhar_number,
            mobile_number=public_user.mobile_number,
            alternate_mobile=request.alternate_mobile,
            email=request.email,
            photo_url=photo_url,
            district_id=request.district_id,
            block_id=request.block_id,
            gp_id=request.gp_id,
            village_name=request.village_name,
            ward_number=request.ward_number,
            full_address=request.full_address,
            pin_code=request.pin_code,
            highest_qualification=request.highest_qualification,
            current_occupation=request.current_occupation,
            organization_name=request.organization_name,
            service_types=request.service_types,
            preferred_days=request.preferred_days,
            hours_per_week=request.hours_per_week,
            commitment_duration=request.commitment_duration,
            fitness_level=request.fitness_level,
            relevant_skills=request.relevant_skills,
            willing_to_work_other_villages=request.willing_to_work_other_villages,
            can_bring_more_volunteers=request.can_bring_more_volunteers,
            additional_volunteers_count=request.additional_volunteers_count,
            category=request.category,
            declaration_accepted=request.declaration_accepted
        )

        self.db.add(volunteer)
        await self.db.commit()
        await self.db.refresh(volunteer)
        return volunteer

    async def get_volunteer_by_public_user_id(self, public_user_id: int) -> Optional[VolunteerRegistration]:
        """Get volunteer registration by public user ID."""
        result = await self.db.execute(
            select(VolunteerRegistration)
            .options(
                selectinload(VolunteerRegistration.district),
                selectinload(VolunteerRegistration.block),
                selectinload(VolunteerRegistration.gp)
            )
            .where(VolunteerRegistration.public_user_id == public_user_id)
        )
        return result.scalar_one_or_none()

    async def get_volunteers_list(
        self,
        district_id: Optional[int] = None,
        block_id: Optional[int] = None,
        gp_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[VolunteerRegistration]:
        """List volunteers with optional geographical filtering."""
        query = select(VolunteerRegistration).options(
            selectinload(VolunteerRegistration.district),
            selectinload(VolunteerRegistration.block),
            selectinload(VolunteerRegistration.gp)
        )

        filters = []
        if district_id:
            filters.append(VolunteerRegistration.district_id == district_id)
        if block_id:
            filters.append(VolunteerRegistration.block_id == block_id)
        if gp_id:
            filters.append(VolunteerRegistration.gp_id == gp_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_volunteer_by_id(self, volunteer_id: int) -> Optional[VolunteerRegistration]:
        """Get volunteer registration by its ID."""
        result = await self.db.execute(
            select(VolunteerRegistration)
            .options(
                selectinload(VolunteerRegistration.district),
                selectinload(VolunteerRegistration.block),
                selectinload(VolunteerRegistration.gp)
            )
            .where(VolunteerRegistration.id == volunteer_id)
        )
        return result.scalar_one_or_none()
