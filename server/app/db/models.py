"""
SQLAlchemy PostGIS Data Models (§12 of Master Prompt).

Provides ORM schemas for spatial layers, verification workflow states,
human audit logs, official credentials, and Single Source of Truth consolidated parcels.
"""

from __future__ import annotations

from datetime import datetime
from app.db.session import Base
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB


class CadastralParcelDB(Base):
    """Synthetic Bhu-Naksha Cadastral Parcel spatial table."""

    __tablename__ = "cadastral_parcels"

    parcel_id = Column(String(64), primary_key=True, index=True)
    khasra_no = Column(String(64), nullable=False, index=True)
    khata_no = Column(String(64), nullable=True)
    tehsil = Column(String(128), nullable=False, index=True)
    district = Column(String(128), nullable=False, default="Meerut District")
    land_use = Column(String(128), nullable=True)
    record_area_sqm = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    properties = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_cadastral_parcels_geom", "geom", postgresql_using="gist"),
    )


class MunicipalBuildingDB(Base):
    """Synthetic Municipal Corporation / ULB Building spatial table."""

    __tablename__ = "municipal_buildings"

    municipal_building_id = Column(String(64), primary_key=True, index=True)
    tehsil = Column(String(128), nullable=True, index=True)
    building_status = Column(String(64), nullable=False, default="registered")
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    properties = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_municipal_buildings_geom", "geom", postgresql_using="gist"),
    )


class AIExtractedStructureDB(Base):
    """GeoAI Stage 1 extracted physical structures table."""

    __tablename__ = "ai_extracted_structures"

    structure_id = Column(String(64), primary_key=True, index=True)
    class_name = Column(String(64), nullable=False, default="building")
    confidence = Column(Float, nullable=True)
    source_tile = Column(String(128), nullable=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    properties = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_ai_extracted_structures_geom", "geom", postgresql_using="gist"),
    )


class StructureVerificationDB(Base):
    """Stage 2/3 validation workflow state & spatial table."""

    __tablename__ = "structure_verifications"

    structure_id = Column(String(64), primary_key=True, index=True)
    status = Column(String(64), nullable=False, index=True)  # verified, audit_pending, disputed, locked_disputed
    verification_method = Column(String(32), nullable=False, default="geoai")
    parcel_id = Column(String(64), nullable=True, index=True)
    overflow_measure = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    tehsil = Column(String(128), nullable=True, index=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    properties = Column(JSONB, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_structure_verifications_geom", "geom", postgresql_using="gist"),
    )


class HumanAuditLogDB(Base):
    """Append-only government decision audit log table (§8, §18)."""

    __tablename__ = "human_audit_log"

    event_id = Column(String(64), primary_key=True, index=True)
    structure_id = Column(String(64), nullable=False, index=True)
    official_id = Column(String(64), nullable=False, index=True)
    official_name = Column(String(128), nullable=False)
    tehsil = Column(String(128), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # mark_verified, lock_disputed
    previous_status = Column(String(64), nullable=False)
    new_status = Column(String(64), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class OfficialDB(Base):
    """Synthetic Lekhpal/Patwari official credentials table (§8)."""

    __tablename__ = "officials"

    official_id = Column(String(64), primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False, default="Lekhpal")
    tehsil = Column(String(128), nullable=False, index=True)
    district = Column(String(128), nullable=False, default="Kumaon District")


class ConsolidatedParcelDB(Base):
    """Stage 4 Single Source of Truth consolidated parcel table (§10)."""

    __tablename__ = "consolidated_parcels"

    parcel_id = Column(String(64), primary_key=True, index=True)
    khasra_no = Column(String(64), nullable=False, index=True)
    khata_no = Column(String(64), nullable=True)
    tehsil = Column(String(128), nullable=False, index=True)
    district = Column(String(128), nullable=False, default="Kumaon District")
    resolved_owner = Column(String(256), nullable=False)
    resolved_land_use = Column(String(128), nullable=False)
    resolved_area_sqm = Column(Float, nullable=False)
    conflict_summary = Column(JSONB, nullable=True)
    source_provenance = Column(JSONB, nullable=True)
    department_records = Column(JSONB, nullable=True)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_consolidated_parcels_geom", "geom", postgresql_using="gist"),
    )
