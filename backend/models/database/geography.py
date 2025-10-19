"""Database models for geographical entities like Districts, Blocks, and Villages."""

from typing import List, Optional

from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Index,
    UniqueConstraint,
)

from database import Base  # type: ignore
from models.database.complaint import Complaint  # type: ignore


class District(Base):  # type: ignore
    """
    Describes a district entity
    """

    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    blocks = relationship("Block", back_populates="district")
    villages = relationship("GramPanchayat", back_populates="district")
    complaints = relationship("Complaint", back_populates="district")


class Block(Base):  # type: ignore
    """
    Describes a block entity within a district
    """

    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Unique constraint on name within district
    __table_args__ = (UniqueConstraint("name", "district_id", name="uq_block_name_district"),)

    # Relationships
    district: Mapped[District] = relationship("District", back_populates="blocks")
    villages: Mapped[List["GramPanchayat"]] = relationship("GramPanchayat", back_populates="block")
    complaints: Mapped[List[Complaint]] = relationship("Complaint", back_populates="block")


class GramPanchayat(Base):  # type: ignore
    """
    Describes a Gram Panchayat entity within a block
    """

    __tablename__ = "gram_panchayats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    block_id: Mapped[int] = mapped_column(Integer, ForeignKey("blocks.id"), nullable=False, index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Unique constraint on name within block
    __table_args__ = (UniqueConstraint("name", "block_id", name="uq_village_name_block"),)

    # Relationships
    block: Mapped[Block] = relationship("Block", back_populates="villages")
    district: Mapped[District] = relationship("District", back_populates="villages")
    complaints: Mapped[List[Complaint]] = relationship("Complaint", back_populates="village")

    # Table indexes
    __table_args__ = (
        Index("ix_gram_panchayat_name", "name"),
        Index("ix_gram_panchayat_block", "block_id"),
    )


class Village(Base):
    """
    Village within a Gram Panchayat.
    """

    __tablename__ = "villages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    gp_id: Mapped[int] = mapped_column(Integer, ForeignKey("gram_panchayats.id"), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Unique constraint on name within Gram Panchayat
    __table_args__ = (
        UniqueConstraint("name", "gp_id", name="uq_village_name_gp"),
        Index("ix_village_name_gp", "name", "gp_id"),
    )
