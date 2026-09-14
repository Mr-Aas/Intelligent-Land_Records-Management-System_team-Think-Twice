/**
 * API service for Urban Land Record Management System.
 */

import type {
  AuditLogEntry,
  ConsolidatedParcel,
  GeoJSONFeatureCollection,
  OfficialProfile,
  StructureProperties,
} from '../types';

const API_BASE = '/api';

export async function login(
  username: string,
  password: string
): Promise<{ status: string; user: OfficialProfile }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function fetchVerificationQueue(
  officialId: string,
  includeDecided = false
): Promise<{
  status: string;
  official_id: string;
  tehsil: string;
  count: number;
  features: Array<{
    type: 'Feature';
    geometry: any;
    properties: StructureProperties;
  }>;
}> {
  const res = await fetch(
    `${API_BASE}/human-verification/queue?official_id=${encodeURIComponent(
      officialId
    )}&include_decided=${includeDecided}`
  );
  if (!res.ok) {
    throw new Error('Failed to fetch verification queue');
  }
  return res.json();
}

export async function submitHumanAction(
  structureId: string,
  officialId: string,
  action: 'mark_verified' | 'lock_disputed' | 'forward_to_revenue' | 'forward_to_tehsildar' | 'tehsildar_commit',
  notes = ''
): Promise<{
  status: string;
  action: string;
  structure_id: string;
  feature: any;
}> {
  const res = await fetch(`${API_BASE}/human-verification/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      structure_id: structureId,
      official_id: officialId,
      action,
      notes,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Action failed' }));
    throw new Error(err.detail || 'Action failed');
  }
  return res.json();
}

export async function fetchAuditLog(officialId?: string): Promise<{
  status: string;
  count: number;
  entries: AuditLogEntry[];
}> {
  const query = officialId ? `?official_id=${encodeURIComponent(officialId)}` : '';
  const res = await fetch(`${API_BASE}/human-verification/audit-log${query}`);
  if (!res.ok) {
    throw new Error('Failed to fetch audit log');
  }
  return res.json();
}

export async function triggerStage4(): Promise<{
  status: string;
  total_parcels_consolidated: number;
  total_eligible_verified_structures: number;
  conflicted_parcels_count: number;
}> {
  const res = await fetch(`${API_BASE}/stage4/run`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to run Stage 4 consolidation');
  }
  return res.json();
}

export async function fetchConsolidatedParcels(
  tehsil?: string
): Promise<{
  status: string;
  count: number;
  parcels: ConsolidatedParcel[];
}> {
  const query = tehsil ? `?tehsil=${encodeURIComponent(tehsil)}` : '';
  const res = await fetch(`${API_BASE}/stage4/parcels${query}`);
  if (!res.ok) {
    throw new Error('Failed to fetch consolidated parcels');
  }
  return res.json();
}

export async function fetchParcelById(
  parcelId: string
): Promise<{ status: string; parcel: ConsolidatedParcel }> {
  const res = await fetch(`${API_BASE}/stage4/parcels/${encodeURIComponent(parcelId)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch parcel ${parcelId}`);
  }
  return res.json();
}

export async function fetchLayer(
  layerName: 'cadastral' | 'municipal' | 'ai-extracted' | 'review-structures'
): Promise<GeoJSONFeatureCollection> {
  const res = await fetch(`${API_BASE}/layers/${layerName}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch layer ${layerName}`);
  }
  return res.json();
}
