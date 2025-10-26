"""Models for authentication and user management."""

from uuid import uuid4
from typing import List, Optional
from datetime import date, datetime

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import String, Integer, Boolean, ForeignKey, Date, UniqueConstraint

from models.database.geography import District, Block, GramPanchayat
from database import Base  # type: ignore


class Role(Base):  # type: ignore
    """
    Describes a generic role
    Can be: WORKER/VDO/BDO/CEO/ADMIN
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore


class User(Base):  # type: ignore
    """
    Describes a user in the system
    """

    __tablename__ = "authority_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)  # type: ignore
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)  # type: ignore
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # type: ignore
    gp_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("gram_panchayats.id"),
        nullable=True,
        index=True,
    )
    block_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("blocks.id"),
        nullable=True,
        index=True,
    )
    district_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("districts.id"),
        nullable=True,
        index=True,
    )

    # Relationships
    positions: Mapped[List["PositionHolder"]] = relationship("PositionHolder", back_populates="user")
    complaint_assignments = relationship("ComplaintAssignment", back_populates="user")
    complaint_comments = relationship("ComplaintComment", back_populates="user")
    district: Mapped[Optional[District]] = relationship("District")
    block: Mapped[Optional[Block]] = relationship("Block")
    gp: Mapped[Optional[GramPanchayat]] = relationship("GramPanchayat")

    __table_args__ = (
        # Ensures no two position holders have the same role in the same geographical area
        # i.e., only one VDO per village, one BDO per block, etc.
        # Note: This does not prevent a user from holding multiple roles or positions in different areas
        # but prevents role duplication in the same area.
        UniqueConstraint("gp_id", "block_id", "district_id", "username", name="uix_user_geo"),
    )

    @property
    def role(self) -> Optional[str]:
        """Returns the primary role of the user based on their position holders."""
        if (not self.district_id) and (not self.block_id) and (not self.gp_id):
            return "ADMIN"
        if self.district_id and (not self.block_id) and (not self.gp_id):
            return "CEO"
        if self.block_id and (not self.gp_id):
            return "BDO"
        if self.gp_id:
            return "VDO"
        return "WORKER"

    @property
    def geo_entity(self) -> str:
        """Returns the geographical entity of the user."""
        geo_entities: List[str] = []
        if self.district:
            geo_entities.append(self.district.name)
        if self.block:
            geo_entities.append(self.block.name)
        if self.gp:
            geo_entities.append(self.gp.name)
        return ", ".join(geo_entities)

    @property
    def name(self) -> str:
        """Returns the name of the user."""
        name: str = f"{self.role}"
        if self.geo_entity:
            name += f" - {self.geo_entity}"
        return name


def generate_employee_id() -> str:
    """Generates a unique employee ID."""
    # This is a placeholder implementation. In a real system, this would generate
    # a unique ID based on specific business rules.

    return str(uuid4())[:8].upper()


class Employee(Base):  # type: ignore
    """
    Describes an employee entity
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    employee_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=generate_employee_id)  # type: ignore
    first_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    middle_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    last_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)  # type: ignore
    mobile_number: Mapped[Optional[str]] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )


class PositionHolder(Base):  # type: ignore
    """
    Describes a user holding a position (like VDO/BDO/CEO) with geographical assignment.
    """

    __tablename__ = "authority_holder_persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    role_id: Mapped[int] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("roles.id"),
        nullable=False,
    )
    village_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("gram_panchayats.id"),
        nullable=True,
    )
    block_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("blocks.id"),
        nullable=True,
    )
    district_id: Mapped[Optional[int]] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("districts.id"),
        nullable=True,
    )
    user_id: Mapped[int] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("authority_users.id"),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    middle_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore
    last_name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    date_of_joining: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # type: ignore - Format: YYYY-MM-DD
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # type: ignore - Format: YYYY-MM-DD
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # type: ignore - Format: YYYY-MM-DD

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="positions")
    role: Mapped[Role] = relationship("Role")
    gp: Mapped["GramPanchayat"] = relationship("GramPanchayat")
    block: Mapped[Block] = relationship("Block")
    district: Mapped[District] = relationship("District")

    @property
    def full_name(self) -> str:
        """Returns the full name of the position holder."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class PublicUser(Base):  # type: ignore
    """
    Describes a public user (like a complainant)
    """

    __tablename__ = "public_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, nullable=True)  # type: ignore
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)  # type: ignore
    mobile_number: Mapped[Optional[str]] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )


class PublicUserOTP(Base):  # type: ignore
    """
    Describes an OTP sent to a public user for verification
    """

    __tablename__ = "public_user_otps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    public_user_id: Mapped[int] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("public_users.id"),
        nullable=False,
        index=True,
    )
    otp: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # type: ignore
    expires_at: Mapped[datetime] = mapped_column(Date, nullable=False)  # type: ignore - Format: YYYY-MM-DD

    # Relationships
    public_user = relationship("PublicUser")


class PublicUserToken(Base):  # type: ignore
    """
    Describes a token issued to a public user after OTP verification
    """

    __tablename__ = "public_user_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    public_user_id: Mapped[int] = mapped_column(  # type: ignore
        Integer,
        ForeignKey("public_users.id"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    created_at: Mapped[datetime] = mapped_column(Date, nullable=False)  # type: ignore - Format: YYYY-MM-DD
    expires_at: Mapped[datetime] = mapped_column(Date, nullable=False)  # type: ignore - Format: YYYY-MM-DD

    # Relationships
    public_user = relationship("PublicUser")
