"""
Stage 4 Swappable Conflict Resolution Component (§9, §10, §24).

Implements an isolated, swappable interface for resolving departmental
discrepancies (ownership, land-use, area, structures) into a consolidated
Single Source of Truth per land parcel.

NOTE: As mandated by §9 and §23 of CODING_AGENT_MASTER_PROMPT.md:
"Build a clearly isolated smart-AI conflict-resolution component...
For the synthetic prototype, deterministic rules or a mock AI resolver may be used...
Do NOT pretend a mock resolver is production AI.
The interface must later allow a real smart AI system to replace the mock resolver."
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ConflictResolver(ABC):
    """Abstract interface for parcel attribute conflict resolution."""

    @abstractmethod
    def resolve_parcel(
        self,
        parcel_id: str,
        cadastral_feature: Optional[Dict[str, Any]],
        department_records: Dict[str, Dict[str, Any]],
        verified_structures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Consolidate departmental data and verified structures for a single parcel,
        resolving attribute conflicts while preserving full provenance and source values.
        """
        pass


class SmartRuleConflictResolver(ConflictResolver):
    """
    Prototype Rule-Based Conflict Resolver.

    LABELED AS NON-PRODUCTION AI PROTOTYPE.
    This component implements deterministic government hierarchy rules to resolve
    departmental conflicts while retaining complete source provenance:
      1. Ownership: Registration & Stamps (legal deed/title registry) takes precedence,
         retaining Revenue and ULB owner variants.
      2. Land-use: Urban Development Authority (master plan / zoning authority) takes
         precedence, preserving municipal and revenue classifications.
      3. Land area: Official Cadastral Survey (Bhu-Naksha / DLR) serves as the primary
         geospatial measurement, tracking area discrepancies across records.
      4. Structures: Associates prefinal verified structures on this parcel.
    """

    RESOLVER_NAME: str = "SmartRuleConflictResolver"
    IS_PRODUCTION_AI: bool = False
    VERSION: str = "1.0.0-prototype"

    def resolve_parcel(
        self,
        parcel_id: str,
        cadastral_feature: Optional[Dict[str, Any]],
        department_records: Dict[str, Dict[str, Any]],
        verified_structures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Consolidate a parcel's departmental records into a Single Source of Truth."""
        cad_props = cadastral_feature.get("properties", {}) if cadastral_feature else {}

        # 1. Resolve Ownership
        ownership_resolution = self._resolve_ownership(department_records)

        # 2. Resolve Land-Use
        land_use_resolution = self._resolve_land_use(department_records)

        # 3. Resolve Land Area
        area_resolution = self._resolve_land_area(cad_props, department_records)

        # 4. Compile Verified Structures
        structures_summary = self._compile_structures(verified_structures)

        # 5. Extract Khasra / Khata / Administrative hierarchy
        khasra_no = (
            cad_props.get("khasra_no")
            or department_records.get("directorate_land_records", {}).get("khasra_no")
            or department_records.get("revenue_department", {}).get("khasra_no")
            or "N/A"
        )
        khata_no = (
            cad_props.get("khata_no")
            or department_records.get("directorate_land_records", {}).get("khata_no")
            or "N/A"
        )
        tehsil = (
            cad_props.get("tehsil")
            or next(
                (r.get("tehsil") for r in department_records.values() if r.get("tehsil")),
                "N/A",
            )
        )
        district = cad_props.get("district", "Synthetic-District")

        # Compile conflicting fields
        conflicting_fields: List[str] = []
        if ownership_resolution["conflict_detected"]:
            conflicting_fields.append("owner_name")
        if land_use_resolution["conflict_detected"]:
            conflicting_fields.append("purpose_of_use")
        if area_resolution["conflict_detected"]:
            conflicting_fields.append("land_area_sqm")

        consolidated_record: Dict[str, Any] = {
            "parcel_id": parcel_id,
            "khasra_no": khasra_no,
            "khata_no": khata_no,
            "tehsil": tehsil,
            "district": district,
            # Single Source of Truth resolved attributes
            "resolved_owner": ownership_resolution["resolved_value"],
            "resolved_land_use": land_use_resolution["resolved_value"],
            "resolved_area_sqm": area_resolution["resolved_value"],
            "verified_structures_count": len(verified_structures),
            "verified_structures": structures_summary,
            # Conflict Analysis & Lineage
            "conflict_summary": {
                "has_conflicts": len(conflicting_fields) > 0,
                "conflicting_fields": conflicting_fields,
                "ownership": ownership_resolution,
                "land_use": land_use_resolution,
                "area": area_resolution,
            },
            # Full provenance: untouched source values preserved without destruction (§10, §18)
            "source_provenance": {
                dept_name: record
                for dept_name, record in department_records.items()
            },
            "department_records": {
                dept_name: record
                for dept_name, record in department_records.items()
            },
            # Resolver Metadata (§9, §23)
            "resolver_metadata": {
                "resolver_name": self.RESOLVER_NAME,
                "is_production_ai": self.IS_PRODUCTION_AI,
                "version": self.VERSION,
                "consolidated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        return consolidated_record

    def _resolve_ownership(
        self,
        dept_records: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate reported owner names across departments.
        Registration & Stamps is treated as the primary legal title registry.
        """
        claims: Dict[str, str] = {}
        for dept_name, rec in dept_records.items():
            owner = rec.get("owner_name") or rec.get("cadastral_owner") or rec.get("revenue_owner")
            if owner and str(owner).strip():
                claims[dept_name] = str(owner).strip()

        unique_owners = set(claims.values())
        conflict_detected = len(unique_owners) > 1

        # Resolution priority:
        # 1. Registration & Stamps (deed of title)
        # 2. Revenue Department
        # 3. Directorate of Land Records
        # 4. Urban Local Body
        # 5. Urban Development Authority
        resolved_value = (
            claims.get("registration_stamps")
            or claims.get("revenue_department")
            or claims.get("directorate_land_records")
            or claims.get("urban_local_body")
            or claims.get("urban_development_authority")
            or "Unknown"
        )

        if conflict_detected:
            explanation = (
                f"Discrepancy detected across {len(claims)} departments: {claims}. "
                f"Resolved to '{resolved_value}' following Registration & Stamps statutory legal title priority. "
                "All source department claims preserved."
            )
        else:
            explanation = "Consistent owner name reported across contributing departments."

        return {
            "resolved_value": resolved_value,
            "conflict_detected": conflict_detected,
            "claims_by_department": claims,
            "explanation": explanation,
        }

    def _resolve_land_use(
        self,
        dept_records: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate reported land-use/purpose across departments.
        Urban Development Authority master plan / zoning takes statutory planning priority.
        """
        claims: Dict[str, str] = {}
        for dept_name, rec in dept_records.items():
            use = rec.get("purpose_of_use") or rec.get("revenue_land_use")
            if use and str(use).strip():
                claims[dept_name] = str(use).strip()

        unique_uses = set(claims.values())
        conflict_detected = len(unique_uses) > 1

        # Resolution priority:
        # 1. Urban Development Authority (statutory master plan / zoning)
        # 2. Urban Local Body (municipal current use)
        # 3. Revenue Department
        # 4. Directorate of Land Records
        # 5. Registration & Stamps
        resolved_value = (
            claims.get("urban_development_authority")
            or claims.get("urban_local_body")
            or claims.get("revenue_department")
            or claims.get("directorate_land_records")
            or claims.get("registration_stamps")
            or "unspecified"
        )

        if conflict_detected:
            explanation = (
                f"Discrepancy detected across {len(claims)} departments: {claims}. "
                f"Resolved to '{resolved_value}' following Urban Development Authority master plan authority. "
                "All source department classifications preserved."
            )
        else:
            explanation = "Consistent land-use classification across contributing departments."

        return {
            "resolved_value": resolved_value,
            "conflict_detected": conflict_detected,
            "claims_by_department": claims,
            "explanation": explanation,
        }

    def _resolve_land_area(
        self,
        cad_props: Dict[str, Any],
        dept_records: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate land area measurements across departments.
        Cadastral spatial survey (Bhu-Naksha / DLR) serves as the primary ground truth measurement.
        """
        claims: Dict[str, float] = {}

        # Cadastral parcel feature area
        cad_area = cad_props.get("record_area_sqm")
        if cad_area is not None:
            try:
                claims["cadastral_survey"] = float(cad_area)
            except (ValueError, TypeError):
                pass

        for dept_name, rec in dept_records.items():
            area_val = rec.get("land_area_sqm")
            if area_val is not None and str(area_val).strip():
                try:
                    claims[dept_name] = float(area_val)
                except (ValueError, TypeError):
                    pass

        areas = list(claims.values())
        if areas:
            min_area = min(areas)
            max_area = max(areas)
            delta = max_area - min_area
            # Consider conflict if delta > 1.0 sqm
            conflict_detected = delta > 1.0
        else:
            min_area = max_area = delta = 0.0
            conflict_detected = False

        # Cadastral survey is primary, fallback to DLR, Registration, Revenue
        resolved_value = (
            claims.get("cadastral_survey")
            or claims.get("directorate_land_records")
            or claims.get("registration_stamps")
            or claims.get("revenue_department")
            or (areas[0] if areas else 0.0)
        )

        if conflict_detected:
            explanation = (
                f"Area variance of {delta:.2f} sqm detected across departmental records "
                f"(min: {min_area:.2f}, max: {max_area:.2f}). "
                f"Resolved to primary cadastral survey value of {resolved_value:.2f} sqm."
            )
        else:
            explanation = "Consistent area records across reporting systems."

        return {
            "resolved_value": resolved_value,
            "conflict_detected": conflict_detected,
            "delta_sqm": round(delta, 2),
            "claims_by_department": claims,
            "explanation": explanation,
        }

    def _compile_structures(
        self,
        verified_structures: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Summarize verified structures located on this parcel."""
        summary = []
        for feat in verified_structures:
            props = feat.get("properties", {})
            summary.append({
                "structure_id": props.get("structure_id"),
                "class": props.get("class"),
                "status": props.get("status"),
                "verification_method": props.get("verification_method"),
                "confidence": props.get("confidence"),
                "municipal_building_id": props.get("municipal_building_id"),
                "human_verification": props.get("human_verification"),
            })
        return summary
