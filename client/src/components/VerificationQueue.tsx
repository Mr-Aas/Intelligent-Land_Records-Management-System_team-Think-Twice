import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Lock,
  Building,
  Clock,
  Search,
  Filter,
} from 'lucide-react';
import type { GeoJSONFeature, StructureProperties } from '../types';

interface VerificationQueueProps {
  queue: Array<GeoJSONFeature<StructureProperties>>;
  selectedStructureId: string | null;
  onSelectStructure: (feature: GeoJSONFeature<StructureProperties>) => void;
  onAction: (
    structureId: string,
    action: 'mark_verified' | 'lock_disputed',
    notes: string
  ) => Promise<void>;
  currentTehsil: string;
  isLoading: boolean;
}

export const VerificationQueue: React.FC<VerificationQueueProps> = ({
  queue,
  selectedStructureId,
  onSelectStructure,
  onAction,
  currentTehsil,
  isLoading,
}) => {
  const [filter, setFilter] = useState<'all' | 'audit_pending' | 'disputed'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [notesByStructure, setNotesByStructure] = useState<Record<string, string>>({});
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const filteredQueue = queue.filter((item) => {
    const props = item.properties;
    const matchesFilter = filter === 'all' || props.status === filter;
    const matchesSearch =
      props.structure_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (props.parcel_id && props.parcel_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (props.cadastral_record?.khasra_no &&
        props.cadastral_record.khasra_no.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const handleAction = async (
    structureId: string,
    action: 'mark_verified' | 'lock_disputed'
  ) => {
    const notes = notesByStructure[structureId] || '';
    setActionInProgress(structureId);
    try {
      await onAction(structureId, action, notes);
      setNotesByStructure((prev) => {
        const copy = { ...prev };
        delete copy[structureId];
        return copy;
      });
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <aside className="w-96 bg-slate-900 border-r border-slate-800 flex flex-col h-full z-20 shrink-0">
      {/* Header & Filter Controls */}
      <div className="p-3 border-b border-slate-800 bg-slate-900/90 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
              <span>Review Queue</span>
              <span className="text-xs font-normal text-slate-400">
                ({filteredQueue.length} items)
              </span>
            </h2>
          </div>
          <span className="text-[11px] bg-slate-800 border border-slate-700 text-amber-300 font-semibold px-2 py-0.5 rounded">
            {currentTehsil}
          </span>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Structure, Parcel, Khasra..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[11px]">
          <span className="text-slate-400 flex items-center gap-1 mr-1">
            <Filter className="w-3 h-3" />
          </span>
          <button
            onClick={() => setFilter('all')}
            className={`px-2 py-1 rounded transition ${
              filter === 'all'
                ? 'bg-slate-700 text-white font-medium'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({queue.length})
          </button>
          <button
            onClick={() => setFilter('audit_pending')}
            className={`px-2 py-1 rounded transition flex items-center gap-1 ${
              filter === 'audit_pending'
                ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30'
                : 'text-slate-400 hover:text-amber-300'
            }`}
          >
            <Clock className="w-3 h-3" />
            <span>Audit Pending</span>
          </button>
          <button
            onClick={() => setFilter('disputed')}
            className={`px-2 py-1 rounded transition flex items-center gap-1 ${
              filter === 'disputed'
                ? 'bg-red-500/20 text-red-300 font-semibold border border-red-500/30'
                : 'text-slate-400 hover:text-red-300'
            }`}
          >
            <AlertTriangle className="w-3 h-3" />
            <span>Disputed</span>
          </button>
        </div>
      </div>

      {/* Queue Item List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Loading tehsil review queue...
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="py-16 px-4 text-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-semibold text-slate-200">
              No Pending Reviews
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
              All structures in <span className="text-amber-400">{currentTehsil}</span> have been verified or locked.
            </p>
          </div>
        ) : (
          filteredQueue.map((item) => {
            const props = item.properties;
            const isSelected = selectedStructureId === props.structure_id;
            const isBusy = actionInProgress === props.structure_id;

            return (
              <div
                key={props.structure_id}
                onClick={() => onSelectStructure(item)}
                className={`rounded-lg p-3 border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-slate-800/90 border-indigo-500 shadow-md ring-1 ring-indigo-500/50'
                    : 'bg-slate-950/60 hover:bg-slate-800/50 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                {/* Header Row */}
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Building className="w-4 h-4 text-slate-400" />
                    <span className="text-xs font-bold text-slate-100">
                      {props.structure_id}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize bg-slate-800 px-1.5 py-0.5 rounded">
                      {props.class.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Status Badge */}
                  {props.status === 'audit_pending' ? (
                    <span className="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded border border-amber-500/40 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      <span>Audit Pending</span>
                    </span>
                  ) : (
                    <span className="text-[10px] bg-red-500/20 text-red-300 font-semibold px-2 py-0.5 rounded border border-red-500/40 flex items-center gap-1">
                      <AlertTriangle className="w-2.5 h-2.5" />
                      <span>Disputed</span>
                    </span>
                  )}
                </div>

                {/* Cadastral & Overflow Details */}
                <div className="grid grid-cols-2 gap-1.5 text-[11px] my-2 p-2 bg-slate-900/80 rounded border border-slate-800/60">
                  <div>
                    <span className="text-slate-500 block">Parcel / Khasra:</span>
                    <span className="text-slate-200 font-medium">
                      {props.parcel_id || 'N/A'} (
                      {props.cadastral_record?.khasra_no || 'N/A'})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Measured Overflow:</span>
                    <span className="text-amber-400 font-bold">
                      {props.overflow_measure !== undefined
                        ? `${props.overflow_measure.toFixed(1)} m`
                        : '0.0 m'}
                    </span>
                    <span className="text-slate-500 text-[10px] ml-1">
                      (&gt; {props.configured_threshold || 10}m rule)
                    </span>
                  </div>
                </div>

                {/* Dispute Reason */}
                <p className="text-[11px] text-slate-300 line-clamp-2 mb-2 leading-relaxed bg-slate-900/40 p-1.5 rounded border border-slate-800/40">
                  {props.reason || 'Boundary exceedance flagged by GeoAI cadastral validator.'}
                </p>

                {/* Decision Remarks & Action Controls */}
                <div
                  className="space-y-2 pt-2 border-t border-slate-800/80"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="text"
                    placeholder="Inspection remarks / field findings..."
                    value={notesByStructure[props.structure_id] || ''}
                    onChange={(e) =>
                      setNotesByStructure({
                        ...notesByStructure,
                        [props.structure_id]: e.target.value,
                      })
                    }
                    className="w-full bg-slate-900 border border-slate-700/80 rounded px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />

                  <div className="grid grid-cols-2 gap-2">
                    {/* Mark Verified Action Button */}
                    <button
                      disabled={isBusy}
                      onClick={() => handleAction(props.structure_id, 'mark_verified')}
                      title="Promote to Verified (Qualifies for Stage 4)"
                      className="flex items-center justify-center gap-1.5 bg-emerald-600/80 hover:bg-emerald-600 text-white text-xs font-semibold py-1.5 rounded transition shadow-sm disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mark Verified</span>
                    </button>

                    {/* Locked Disputed Action Button */}
                    <button
                      disabled={isBusy}
                      onClick={() => handleAction(props.structure_id, 'lock_disputed')}
                      title="Lock as Disputed (Excluded from Stage 4)"
                      className="flex items-center justify-center gap-1.5 bg-red-600/80 hover:bg-red-600 text-white text-xs font-semibold py-1.5 rounded transition shadow-sm disabled:opacity-50"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>Lock Disputed</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
