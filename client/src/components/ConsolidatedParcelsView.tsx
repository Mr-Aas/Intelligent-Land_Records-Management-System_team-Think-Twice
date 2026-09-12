import React, { useState } from 'react';
import {
  Layers,
  Search,
  AlertTriangle,
  CheckCircle,
  FileText,
  Building,
  User,
  Maximize2,
  RefreshCw,
} from 'lucide-react';
import type { ConsolidatedParcel } from '../types';

interface ConsolidatedParcelsViewProps {
  parcels: ConsolidatedParcel[];
  selectedParcelId: string | null;
  onSelectParcel: (parcelId: string) => void;
  onTriggerStage4: () => void;
  isStage4Running: boolean;
}

export const ConsolidatedParcelsView: React.FC<ConsolidatedParcelsViewProps> = ({
  parcels,
  selectedParcelId,
  onSelectParcel,
  onTriggerStage4,
  isStage4Running,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterConflictOnly, setFilterConflictOnly] = useState(false);

  const filteredParcels = parcels.filter((p) => {
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
    <div className="flex-1 flex h-full bg-slate-950 overflow-hidden text-white">
      {/* Left Column: Parcel Registry List */}
      <div className="w-84 border-r border-slate-800 bg-slate-900 flex flex-col h-full shrink-0">
        <div className="p-3 border-b border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold flex items-center gap-1.5 text-slate-100">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Single Source of Truth</span>
            </h2>
            <button
              onClick={onTriggerStage4}
              disabled={isStage4Running}
              className="text-[11px] bg-indigo-600/80 hover:bg-indigo-600 px-2 py-0.5 rounded text-white font-medium flex items-center gap-1 transition"
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
              className="w-full bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Conflict Toggle */}
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400 hover:text-slate-200">
            <input
              type="checkbox"
              checked={filterConflictOnly}
              onChange={(e) => setFilterConflictOnly(e.target.checked)}
              className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
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
                className={`p-2.5 rounded-lg border transition cursor-pointer ${
                  isSelected
                    ? 'bg-slate-800 border-indigo-500 shadow ring-1 ring-indigo-500/40'
                    : 'bg-slate-950/60 hover:bg-slate-800/40 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-100">
                      {parcel.parcel_id}
                    </span>
                    <span className="text-[11px] text-slate-400 ml-1.5">
                      (Khasra {parcel.khasra_no})
                    </span>
                  </div>
                  {hasConflict ? (
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-1.5 py-0.2 rounded border border-amber-500/30 flex items-center gap-0.5">
                      <AlertTriangle className="w-2.5 h-2.5" />
                      <span>Conflict</span>
                    </span>
                  ) : (
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/30 flex items-center gap-0.5">
                      <CheckCircle className="w-2.5 h-2.5" />
                      <span>Consistent</span>
                    </span>
                  )}
                </div>

                <div className="text-[11px] text-slate-300 mt-1 flex items-center justify-between">
                  <span className="truncate max-w-[140px] text-slate-200">
                    {parcel.resolved_owner}
                  </span>
                  <span className="text-slate-400 capitalize">
                    {parcel.resolved_land_use}
                  </span>
                </div>

                <div className="text-[10px] text-slate-500 mt-1 flex items-center justify-between">
                  <span>{parcel.tehsil}</span>
                  <span className="font-mono text-slate-400">
                    {Number(parcel.resolved_area_sqm).toLocaleString()} sqm
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column: Parcel Master Record Inspector */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-950">
        {activeParcel ? (
          <div className="max-w-4xl mx-auto space-y-5">
            {/* Header Title */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-extrabold text-white">
                    Parcel {activeParcel.parcel_id}
                  </h1>
                  <span className="bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs font-semibold px-2.5 py-0.5 rounded-full">
                    Single Source of Truth
                  </span>
                  {activeParcel.conflict_summary?.has_conflicts && (
                    <span className="bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Conflicts Resolved</span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                  <span>Khasra No: <strong className="text-slate-200">{activeParcel.khasra_no}</strong></span>
                  <span>Khata No: <strong className="text-slate-200">{activeParcel.khata_no}</strong></span>
                  <span>Tehsil: <strong className="text-amber-400">{activeParcel.tehsil}</strong></span>
                  <span>District: <strong className="text-slate-200">{activeParcel.district}</strong></span>
                </p>
              </div>

              <div className="text-right text-[11px] text-slate-400">
                <span>Resolver: </span>
                <span className="text-indigo-300 font-mono">
                  {activeParcel.resolver_metadata?.resolver_name || 'SmartRuleConflictResolver'}
                </span>
                <div className="text-[10px] text-slate-500">
                  Consolidated: {new Date(activeParcel.resolver_metadata?.consolidated_at || Date.now()).toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Resolved Attribute Highlight Cards */}
            <div className="grid grid-cols-3 gap-4">
              {/* Resolved Owner Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-300">
                    <User className="w-4 h-4 text-indigo-400" />
                    <span>Consolidated Owner</span>
                  </span>
                  {activeParcel.conflict_summary?.ownership?.conflict_detected && (
                    <span className="text-[10px] text-amber-400 font-semibold bg-amber-400/10 px-1.5 py-0.5 rounded">
                      Discrepancy
                    </span>
                  )}
                </div>
                <div className="text-base font-bold text-white mt-1">
                  {activeParcel.resolved_owner}
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  {activeParcel.conflict_summary?.ownership?.explanation ||
                    'Consistent owner name reported across all department registers.'}
                </p>
              </div>

              {/* Resolved Land-Use Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-300">
                    <Building className="w-4 h-4 text-emerald-400" />
                    <span>Approved Land Use</span>
                  </span>
                  {activeParcel.conflict_summary?.land_use?.conflict_detected && (
                    <span className="text-[10px] text-amber-400 font-semibold bg-amber-400/10 px-1.5 py-0.5 rounded">
                      Discrepancy
                    </span>
                  )}
                </div>
                <div className="text-base font-bold text-white capitalize mt-1">
                  {activeParcel.resolved_land_use}
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  {activeParcel.conflict_summary?.land_use?.explanation ||
                    'Consistent land-use classification across contributing departments.'}
                </p>
              </div>

              {/* Resolved Area Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span className="flex items-center gap-1.5 font-semibold text-slate-300">
                    <Maximize2 className="w-4 h-4 text-sky-400" />
                    <span>Cadastral Spatial Area</span>
                  </span>
                  {activeParcel.conflict_summary?.area?.conflict_detected && (
                    <span className="text-[10px] text-amber-400 font-semibold bg-amber-400/10 px-1.5 py-0.5 rounded">
                      Variance {activeParcel.conflict_summary.area.delta_sqm}m²
                    </span>
                  )}
                </div>
                <div className="text-base font-bold text-white font-mono mt-1">
                  {Number(activeParcel.resolved_area_sqm).toLocaleString()} sqm
                </div>
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  {activeParcel.conflict_summary?.area?.explanation ||
                    'Consistent area records across cadastral survey and deeds.'}
                </p>
              </div>
            </div>

            {/* Departmental Comparison Matrix (The 5 Department Truth Table) */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="p-3.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span>5-Department Source Records Comparison Table</span>
                </h3>
                <span className="text-[11px] text-slate-400">
                  Preserved source values without information loss (§10, §18)
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-4 font-semibold">Government Department</th>
                      <th className="py-2.5 px-4 font-semibold">Recorded Owner</th>
                      <th className="py-2.5 px-4 font-semibold">Reported Land Use</th>
                      <th className="py-2.5 px-4 font-semibold">Record Area (sqm)</th>
                      <th className="py-2.5 px-4 font-semibold">Registration Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-medium">
                    {/* 1. Registration & Stamps */}
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                        <span>Registration & Stamps</span>
                      </td>
                      <td className="py-2.5 px-4 text-white">
                        {activeParcel.source_provenance?.registration_stamps?.owner_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 capitalize">
                        {activeParcel.source_provenance?.registration_stamps?.purpose_of_use || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        {activeParcel.source_provenance?.registration_stamps?.land_area_sqm || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-emerald-400 text-[11px]">
                        {activeParcel.source_provenance?.registration_stamps?.registration_status || 'registered'}
                      </td>
                    </tr>

                    {/* 2. Revenue Department */}
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                        <span>Revenue Department</span>
                      </td>
                      <td className="py-2.5 px-4 text-white">
                        {activeParcel.source_provenance?.revenue_department?.owner_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 capitalize">
                        {activeParcel.source_provenance?.revenue_department?.purpose_of_use || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        {activeParcel.source_provenance?.revenue_department?.land_area_sqm || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 text-[11px]">active</td>
                    </tr>

                    {/* 3. Urban Local Body (ULB) */}
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                        <span>Urban Local Body (ULB)</span>
                      </td>
                      <td className="py-2.5 px-4 text-white">
                        {activeParcel.source_provenance?.urban_local_body?.owner_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 capitalize">
                        {activeParcel.source_provenance?.urban_local_body?.purpose_of_use || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        {activeParcel.source_provenance?.urban_local_body?.land_area_sqm || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 text-[11px]">tax registered</td>
                    </tr>

                    {/* 4. Urban Development Authority (UDA) */}
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                        <span>Urban Development Authority</span>
                      </td>
                      <td className="py-2.5 px-4 text-white">
                        {activeParcel.source_provenance?.urban_development_authority?.owner_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-white font-semibold capitalize">
                        {activeParcel.source_provenance?.urban_development_authority?.purpose_of_use || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        {activeParcel.source_provenance?.urban_development_authority?.land_area_sqm || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 text-[11px]">approved</td>
                    </tr>

                    {/* 5. Directorate of Land Records (DLR) */}
                    <tr className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 text-slate-300 font-semibold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        <span>Directorate of Land Records</span>
                      </td>
                      <td className="py-2.5 px-4 text-white">
                        {activeParcel.source_provenance?.directorate_land_records?.owner_name || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-300 capitalize">
                        {activeParcel.source_provenance?.directorate_land_records?.purpose_of_use || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-300">
                        {activeParcel.source_provenance?.directorate_land_records?.land_area_sqm || 'N/A'}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 text-[11px]">cadastral record</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Verified Physical Structures on this Parcel */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2 flex items-center gap-2">
                <Building className="w-4 h-4 text-indigo-400" />
                <span>Verified Structures on Parcel ({activeParcel.verified_structures?.length || 0})</span>
              </h3>

              {activeParcel.verified_structures && activeParcel.verified_structures.length > 0 ? (
                <div className="grid grid-cols-2 gap-3 mt-2">
                  {activeParcel.verified_structures.map((s) => (
                    <div
                      key={s.structure_id}
                      className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-100">{s.structure_id}</span>
                        <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded border border-emerald-500/30">
                          {s.status}
                        </span>
                      </div>
                      <div className="text-slate-400 text-[11px] mt-1 capitalize">
                        Class: <span className="text-slate-200">{s.class.replace('_', ' ')}</span>
                      </div>
                      <div className="text-slate-500 text-[10px] mt-0.5">
                        Method:{' '}
                        <span className="text-indigo-300">
                          {s.verification_method || 'geoai'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic mt-1">
                  No verified building structures currently mapped on this parcel.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="py-20 text-center text-slate-400 text-sm">
            Select a parcel from the left to inspect its Single Source of Truth record.
          </div>
        )}
      </div>
    </div>
  );
};
