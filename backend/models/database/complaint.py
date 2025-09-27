from typing import Optional
from datetime import datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    String,
    Integer,
    ForeignKey,
    DateTime,
)

from database import Base


class ComplaintType(Base):
    """
    Describes a type of complaint
    """

    __tablename__ = "complaint_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    # Relationships
    geographical_eligibilities = relationship(
        "ComplaintTypeGeographicalEligibility", back_populates="complaint_type"
    )
    complaints = relationship("Complaint", back_populates="complaint_type")


class ComplaintTypeGeographicalEligibility(Base):
    """
    Describes the geographical eligibility of a complaint type
    """

    __tablename__ = "complaint_type_geographical_eligibilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    complaint_type_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("complaint_types.id"), nullable=False
    )
    district_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("districts.id"), nullable=True
    )  # type: ignore
    block_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("blocks.id"), nullable=True
    )  # type: ignore
    village_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("villages.id"), nullable=True
    )  # type: ignore
    active: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )  # type: ignore

    # Relationships
    complaint_type = relationship(
        "ComplaintType", back_populates="geographical_eligibilities"
    )
    district = relationship("District")
    block = relationship("Block")
    village = relationship("Village")


class ComplaintStatus(Base):
    """
    Describes the status of a complaint
    """

    __tablename__ = "complaint_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    # Relationships
    complaints = relationship("Complaint", back_populates="status")


class Complaint(Base):
    """
    Describes a complaint lodged by a user
    """

    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    complaint_type_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("complaint_types.id"), nullable=False
    )
    village_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("villages.id"), nullable=False
    )  # type: ignore
    block_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blocks.id"), nullable=False
    )  # type: ignore
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id"), nullable=False
    )  # type: ignore
    description: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    mobile_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    status_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("complaint_statuses.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(  # type: ignore
        DateTime,
        onupdate=datetime.utcnow,
        nullable=True,
    )

    # Relationships
    village = relationship("Village", back_populates="complaints")
    block = relationship("Block", back_populates="complaints")
    district = relationship("District", back_populates="complaints")
    complaint_type = relationship("ComplaintType", back_populates="complaints")
    status: Mapped[ComplaintStatus] = relationship("ComplaintStatus", back_populates="complaints")
    assignments = relationship("ComplaintAssignment", back_populates="complaint")
    media = relationship("ComplaintMedia", back_populates="complaint")
    comments = relationship("ComplaintComment", back_populates="complaint")


class ComplaintAssignment(Base):
    """
    Describes the assignment of a complaint to a user
    """

    __tablename__ = "complaint_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id"), nullable=False
    )  # type: ignore
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # type: ignore
    assigned_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime,
        default=datetime.utcnow,
    )

    # Relationships
    complaint = relationship("Complaint", back_populates="assignments")
    user = relationship("User", back_populates="complaint_assignments")


class ComplaintMedia(Base):
    """
    Describes media (images, videos, etc.) associated with a complaint
    """

    __tablename__ = "complaint_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id"), nullable=False
    )  # type: ignore
    media_url: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    uploaded_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime,
        default=datetime.utcnow,
    )
    uploaded_by_public_mobile: Mapped[Optional[str]] = mapped_column(  # type: ignore
        String, nullable=True
    )
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    complaint = relationship("Complaint", back_populates="media")

    # Constraint: Either uploaded_by_public_mobile or uploaded_by_user_id should be set, but not both, nor neither.
    __table_args__ = (
        CheckConstraint(
            (uploaded_by_public_mobile.isnot(None)) | (uploaded_by_user_id.isnot(None)),
            name="uploaded_by_constraint"
        ),
        CheckConstraint(
            (uploaded_by_public_mobile.is_(None)) | (uploaded_by_user_id.is_(None)),
            name="uploaded_by_exclusivity_constraint"
        )
    )


class ComplaintComment(Base):
    """
    Describes comments made on a complaint
    """

    __tablename__ = "complaint_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id"), nullable=False
    )  # type: ignore
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # type: ignore
    mobile_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    comment: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    commented_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime,
        default=datetime.utcnow,
    )

    # Relationships
    complaint = relationship("Complaint", back_populates="comments")
    user = relationship("User", back_populates="complaint_comments")
