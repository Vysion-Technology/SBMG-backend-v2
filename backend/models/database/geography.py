from typing import List, Optional

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    UniqueConstraint,
)

from database import Base  # type: ignore
from models.database.complaint import Complaint  # type: ignore


class District(Base):  # type: ignore
    """
    Describes a district entity
    """

    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    # Relationships
    blocks = relationship("Block", back_populates="district")
    villages = relationship("GramPanchayat", back_populates="district")
    complaints = relationship("Complaint", back_populates="district")


class Block(Base):  # type: ignore
    """
    Describes a block entity within a district
    """

    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    district_id: Mapped[int] = mapped_column(  # type: ignore
        Integer, ForeignKey("districts.id"), nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    # Unique constraint on name within district
    __table_args__ = (
        UniqueConstraint("name", "district_id", name="uq_block_name_district"),
    )

    # Relationships
    district: Mapped[District] = relationship("District", back_populates="blocks")
    villages: Mapped[List["GramPanchayat"]] = relationship(
        "GramPanchayat", back_populates="block"
    )
    complaints: Mapped[List[Complaint]] = relationship(
        "Complaint", back_populates="block"
    )


class GramPanchayat(Base):  # type: ignore
    """
    Describes a village entity within a block
    """

    __tablename__ = "villages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # type: ignore
    name: Mapped[str] = mapped_column(String, nullable=False)  # type: ignore
    block_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blocks.id"), nullable=False, index=True
    )  # type: ignore
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id"), nullable=False
    )  # type: ignore
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # type: ignore

    # Unique constraint on name within block
    __table_args__ = (
        UniqueConstraint("name", "block_id", name="uq_village_name_block"),
    )

    # Relationships
    block: Mapped[Block] = relationship("Block", back_populates="villages")
    district: Mapped[District] = relationship("District", back_populates="villages")
    complaints: Mapped[List[Complaint]] = relationship(
        "Complaint", back_populates="village"
    )
