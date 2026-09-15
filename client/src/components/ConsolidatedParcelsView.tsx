import React, { useState } from 'react';
import {
  Layers,
  Search,
  Building,
  RefreshCw,
} from 'lucide-react';
import type { ConsolidatedParcel,OfficialProfile } from '../types';

interface ConsolidatedParcelsViewProps {
  currentOfficial:OfficialProfile;
  parcels: ConsolidatedParcel[];
  selectedParcelId: string | null;
  onSelectParcel: (parcelId: string) => void;
  onTriggerStage4: () => void;
  isStage4Running: boolean;
}

export const ConsolidatedParcelsView: React.FC<ConsolidatedParcelsViewProps> = ({
  currentOfficial,
  parcels,
  selectedParcelId,
  onSelectParcel,
  onTriggerStage4,
  isStage4Running,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterConflictOnly, setFilterConflictOnly] = useState(false);
 


  const official_related_parcels = parcels.filter((p) => p.tehsil == currentOfficial.tehsil);
  console.log(currentOfficial)
  console.log(parcels[8])

  const filteredParcels = official_related_parcels.filter((p) => {
    const matchesSearch =
      p.parcel_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.khasra_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.resolved_owner.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.tehsil.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesConflict = filterConflictOnly
      ? p.conflict_summary?.has_conflicts
      : true;

    return matchesSearch && matchesConflict;
  });
  

  const activeParcel =
    parcels.find((p) => p.parcel_id === selectedParcelId) || parcels[0] || null;

  return (
    <div className="flex-1 bg-red-100 flex h-full  overflow-hidden text-slate-800">
      {/* Left Column: Parcel Registry List */}
      <div className="w-84 border-r border-[#d2d2c8] bg-[#fafaf7] flex flex-col h-full shrink-0 shadow-sm">
        <div className="p-3.5 border-b border-[#d2d2c8] bg-[#efefea] space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black flex items-center gap-1.5 text-slate-900">
              <Layers className="w-4 h-4 text-[#29cc39]" />
              <span>Single Source of Truth</span>
            </h2>
            <button
              onClick={onTriggerStage4}
              disabled={isStage4Running}
              className="text-[11px] bg-[#29cc39] hover:bg-[#22a229] px-2.5 py-1 rounded-lg text-white font-bold flex items-center gap-1 transition shadow-sm cursor-pointer"
            >
              <RefreshCw className={`w-3 h-3 ${isStage4Running ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search parcel, khasra, owner..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-[#d2d2c8] rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#29cc39]"
            />
          </div>

          {/* Conflict Toggle */}
          <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-600 hover:text-slate-900">
            <input
              type="checkbox"
              checked={filterConflictOnly}
              onChange={(e) => setFilterConflictOnly(e.target.checked)}
              className="rounded border-[#d2d2c8] bg-white text-[#29cc39] focus:ring-0 cursor-pointer"
            />
            <span>Show Conflicted Parcels Only</span>
          </label>
        </div>

        {/* Parcels List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {filteredParcels.map((parcel) => {
            const isSelected = activeParcel?.parcel_id === parcel.parcel_id;
            const hasConflict = parcel.conflict_summary?.has_conflicts;

            return (
              <div
                key={parcel.parcel_id}
                onClick={() => onSelectParcel(parcel.parcel_id)}
                className={`p-3 rounded-xl border text-xs transition cursor-pointer ${
                  isSelected
                    ? 'bg-white border-[#29cc39] ring-2 ring-[#29cc39]/30 shadow-md'
                    : 'bg-[#f4f4ef] hover:bg-white border-[#d2d2c8]'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-slate-900">{parcel.parcel_id}</span>
                  {hasConflict ? (
                    <span className="text-[10px] bg-red-100 border border-red-300 text-red-700 font-bold px-1.5 py-0.2 rounded">
                      Conflict
                    </span>
                  ) : (
                    <span className="text-[10px] bg-[#29cc39]/15 border border-[#29cc39]/30 text-[#1b7a21] font-bold px-1.5 py-0.2 rounded">
                      Unified
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-600 flex justify-between">
                  <span>Khasra: <strong>{parcel.khasra_no}</strong></span>
                  <span className="text-amber-700 font-semibold">{parcel.tehsil}</span>
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-0.5">
                  Owner: <span className="text-slate-800 font-medium">{parcel.resolved_owner}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Main Column: Consolidated SSOT Inspector */}
      {activeParcel ? (
        <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6">
          {/* Header Bar */}
          <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-5 shadow-sm flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-xl font-black text-slate-900">
                  Parcel Master: {activeParcel.parcel_id}
                </h1>
                <span className="text-xs bg-amber-100 border border-amber-300 text-amber-800 font-bold px-2.5 py-0.5 rounded-lg">
                  Khasra #{activeParcel.khasra_no}
                </span>
                <span className="text-xs bg-[#29cc39]/15 border border-[#29cc39]/30 text-[#1b7a21] font-bold px-2.5 py-0.5 rounded-lg">
                  {activeParcel.tehsil}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Consolidated Single Source of Truth record across 5 land management departments.
              </p>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-4 shadow-sm">
              <span className="text-slate-400 text-[11px] block font-semibold">Resolved Owner (SSOT)</span>
              <span className="text-sm font-black text-slate-900 mt-1 block">{activeParcel.resolved_owner}</span>
            </div>

            <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-4 shadow-sm">
              <span className="text-slate-400 text-[11px] block font-semibold">Total Area (sqm)</span>
              <span className="text-sm font-black text-[#29cc39] mt-1 block">{activeParcel.resolved_area_sqm} sqm</span>
            </div>

            <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-4 shadow-sm">
              <span className="text-slate-400 text-[11px] block font-semibold">Land Use Classification</span>
              <span className="text-sm font-black text-indigo-700 mt-1 block capitalize">{activeParcel.resolved_land_use}</span>
            </div>

            <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-4 shadow-sm">
              <span className="text-slate-400 text-[11px] block font-semibold">Conflict Resolution Status</span>
              <span className="text-sm font-black text-slate-900 mt-1 block">
                {activeParcel.conflict_summary?.has_conflicts ? 'conflicted' : 'No Conflicts'}
              </span>
            </div>
          </div>

          {/* Department Breakdown Table */}
          <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
              <Building className="w-4 h-4 text-[#29cc39]" />
              <span>Multi-Department Records Alignment (5 Data Sources)</span>
            </h3>

            <div className="overflow-x-auto rounded-xl border border-[#e0e0d6]">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-[#efefea] text-slate-900 font-bold border-b border-[#e0e0d6]">
                  <tr>
                    <th className="p-3">Department Source</th>
                    <th className="p-3">Recorded Owner</th>
                    <th className="p-3">Recorded Area</th>
                    <th className="p-3">Land Category</th>
                    <th className="p-3">Discrepancy Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#e0e0d6]">
                  {Object.entries(activeParcel.department_records || activeParcel.source_provenance || {}).map(([dept, rec]: [string, any]) => (
                    <tr key={dept} className="hover:bg-white transition">
                      <td className="p-3 font-bold uppercase text-slate-800">{dept.replace(/_/g, ' ')}</td>
                      <td className="p-3 font-semibold">{rec?.owner_name || rec?.cadastral_owner || rec?.revenue_owner || rec?.owner || 'N/A'}</td>
                      <td className="p-3 font-semibold">{rec?.land_area_sqm || rec?.registered_area_sqm || rec?.record_area_sqm || 'N/A'} {rec?.area_sqm || rec?.registered_area_sqm || rec?.record_area_sqm ? 'sqm' : ''}</td>
                      <td className="p-3 capitalize">{rec?.land_use || rec?.purpose_of_use || rec?.category || 'N/A'}</td>
                      <td className="p-3">
                        <span className="text-[10px] bg-[#29cc39]/15 text-[#1b7a21] font-bold px-2 py-0.5 rounded">
                          Aligned
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-xs font-semibold">
          Select a parcel to inspect single source of truth records.
        </div>
      )}
    </div>
  );
};
