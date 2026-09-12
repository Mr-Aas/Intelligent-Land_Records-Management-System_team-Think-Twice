/**
 * Core TypeScript types for the Urban Land Record GIS Management System.
 */

export interface OfficialProfile {
  official_id: string;
  username: string;
  name: string;
  role: string;
  tehsil: string;
  district: string;
}

export interface StructureProperties {
  structure_id: string;
  class: string;
  status: 'ai_extracted' | 'unregistered' | 'verified' | 'audit_pending' | 'disputed' | 'locked_disputed';
  verification_method?: string;
  confidence?: number;
  parcel_id?: string;
  primary_parcel_id?: string;
  related_parcel_ids?: string[];
  overflow_measure?: number;
  configured_threshold?: number;
  reason?: string;
  stage2_reason?: string;
  municipal_building_id?: string;
  human_verification?: {
    action: string;
    official_id: string;
    official_name: string;
    official_role: string;
    tehsil: string;
    previous_status: string;
    new_status: string;
    timestamp: string;
    notes: string;
  };
  cadastral_record?: {
    parcel_id: string;
    khasra_no: string;
    khata_no: string;
    land_use: string;
    record_area_sqm: number;
    tehsil: string;
    district: string;
  };
}

export interface GeoJSONGeometry {
  type: string;
  coordinates: any;
}



export interface GeoJSONFeature<P = any> {
  type: 'Feature';
  geometry: GeoJSONGeometry;
  properties: P;
}

export interface GeoJSONFeatureCollection<P = any> {
  type: 'FeatureCollection';
  name?: string;
  features: Array<GeoJSONFeature<P>>;
}

export interface ConflictDetail {
  resolved_value: any;
  conflict_detected: boolean;
  claims_by_department: Record<string, any>;
  explanation: string;
  delta_sqm?: number;
}

export interface ConsolidatedParcel {
  parcel_id: string;
  khasra_no: string;
  khata_no: string;
  tehsil: string;
  district: string;
  resolved_owner: string;
  resolved_land_use: string;
  resolved_area_sqm: number;
  verified_structures_count: number;
  verified_structures: Array<{
    structure_id: string;
    class: string;
    status: string;
    verification_method: string;
    confidence?: number;
    municipal_building_id?: string;
    human_verification?: any;
  }>;
  conflict_summary: {
    has_conflicts: boolean;
    conflicting_fields: string[];
    ownership: ConflictDetail;
    land_use: ConflictDetail;
    area: ConflictDetail;
  };
  source_provenance: Record<string, any>;
  resolver_metadata: {
    resolver_name: string;
    is_production_ai: boolean;
    version: string;
    consolidated_at: string;
  };
}

export interface AuditLogEntry {
  event_id: string;
  action: string;
  structure_id: string;
  official_id: string;
  official_name: string;
  tehsil: string;
  previous_status: string;
  new_status: string;
  timestamp: string;
  notes: string;
}
