import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Lock,
  Building,
  Clock,
  Search,
  Filter,
  ChevronLeft,
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
  onCloseQueue?: () => void;
}

export const VerificationQueue: React.FC<VerificationQueueProps> = ({
  queue,
  selectedStructureId,
  onSelectStructure,
  onAction,
  currentTehsil,
  isLoading,
  onCloseQueue,
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
    <aside className="w-96 bg-[#fafaf7] border-r border-[#d2d2c8] flex flex-col h-full z-20 shrink-0 shadow-md">
      {/* Header & Filter Controls */}
      <div className="p-3.5 border-b border-[#d2d2c8] bg-[#efefea] space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-black text-slate-800 flex items-center gap-1.5">
              <span>Review Queue</span>
              <span className="text-xs font-semibold text-slate-500 bg-[#e4e4dc] px-2 py-0.5 rounded-full">
                {filteredQueue.length}
              </span>
            </h2>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] bg-amber-100 border border-amber-300 text-amber-800 font-bold px-2 py-0.5 rounded-md">
              {currentTehsil}
            </span>
            {onCloseQueue && (
              <button
                onClick={onCloseQueue}
                title="Close Review Queue"
                className="text-slate-500 hover:text-slate-900 p-1 rounded-md hover:bg-[#e4e4dc] transition cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search Structure, Parcel, Khasra..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-[#d2d2c8] rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#29cc39] focus:ring-1 focus:ring-[#29cc39] transition"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 text-[11px]">
          <span className="text-slate-400 flex items-center gap-1 mr-1">
            <Filter className="w-3 h-3" />
          </span>
          <button
            onClick={() => setFilter('all')}
            className={`px-2 py-1 rounded-lg transition font-semibold cursor-pointer ${
              filter === 'all'
                ? 'bg-[#29cc39] text-white shadow-sm'
                : 'text-slate-600 hover:bg-[#e4e4dc]'
            }`}
          >
            All ({queue.length})
          </button>
          <button
            onClick={() => setFilter('audit_pending')}
            className={`px-2 py-1 rounded-lg transition flex items-center gap-1 font-semibold cursor-pointer ${
              filter === 'audit_pending'
                ? 'bg-amber-500 text-white shadow-sm'
                : 'text-slate-600 hover:bg-[#e4e4dc]'
            }`}
          >
            <Clock className="w-3 h-3" />
            <span>Audit Pending</span>
          </button>
          <button
            onClick={() => setFilter('disputed')}
            className={`px-2 py-1 rounded-lg transition flex items-center gap-1 font-semibold cursor-pointer ${
              filter === 'disputed'
                ? 'bg-red-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-[#e4e4dc]'
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
          <div className="py-12 text-center text-xs font-semibold text-slate-400">
            Loading tehsil review queue...
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="py-16 px-4 text-center">
            <CheckCircle2 className="w-9 h-9 text-[#29cc39] mx-auto mb-2 opacity-90" />
            <p className="text-sm font-bold text-slate-800">
              No Pending Reviews
            </p>
            <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
              All structures in <span className="text-amber-700 font-bold">{currentTehsil}</span> have been verified or locked.
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
                className={`rounded-xl p-3.5 border transition-all cursor-pointer shadow-sm ${
                  isSelected
                    ? 'bg-white border-[#29cc39] ring-2 ring-[#29cc39]/40 shadow-md'
                    : 'bg-[#f4f4ef] hover:bg-white border-[#d2d2c8]'
                }`}
              >
                {/* Header Row */}
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Building className="w-4 h-4 text-slate-500" />
                    <span className="text-xs font-bold text-slate-900">
                      {props.structure_id}
                    </span>
                    <span className="text-[10px] text-slate-600 font-medium capitalize bg-[#e4e4dc] px-1.5 py-0.5 rounded">
                      {props.class.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Status Badge */}
                  {props.status === 'audit_pending' ? (
                    <span className="text-[10px] bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded-md border border-amber-300 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      <span>Audit Pending</span>
                    </span>
                  ) : (
                    <span className="text-[10px] bg-red-100 text-red-700 font-bold px-2 py-0.5 rounded-md border border-red-300 flex items-center gap-1">
                      <AlertTriangle className="w-2.5 h-2.5" />
                      <span>Disputed</span>
                    </span>
                  )}
                </div>

                {/* Cadastral & Overflow Details */}
                <div className="grid grid-cols-2 gap-1.5 text-[11px] my-2 p-2 bg-white rounded-lg border border-[#e0e0d6]">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Parcel / Khasra:</span>
                    <span className="text-slate-800 font-bold">
                      {props.parcel_id || 'N/A'} (
                      {props.cadastral_record?.khasra_no || 'N/A'})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Measured Overflow:</span>
                    <span className="text-amber-700 font-extrabold">
                      {props.overflow_measure !== undefined
                        ? `${props.overflow_measure.toFixed(1)} m`
                        : '0.0 m'}
                    </span>
                  </div>
                </div>

                {/* Dispute Reason */}
                <p className="text-[11px] text-slate-600 line-clamp-2 mb-2 leading-relaxed bg-[#efefea] p-1.5 rounded-md border border-[#e0e0d6]">
                  {props.reason || 'Boundary exceedance flagged by GeoAI cadastral validator.'}
                </p>

                {/* Decision Remarks & Action Controls */}
                <div
                  className="space-y-2 pt-2 border-t border-[#e0e0d6]"
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
                    className="w-full bg-white border border-[#d2d2c8] rounded-lg px-2.5 py-1 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#29cc39]"
                  />

                  <div className="grid grid-cols-2 gap-2">
                    {/* Mark Verified Action Button */}
                    <button
                      disabled={isBusy}
                      onClick={() => handleAction(props.structure_id, 'mark_verified')}
                      title="Promote to Verified (Qualifies for Stage 4)"
                      className="flex items-center justify-center gap-1 bg-[#29cc39] hover:bg-[#22a229] text-white text-xs font-bold py-1.5 rounded-lg transition shadow-sm disabled:opacity-50 cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mark Verified</span>
                    </button>

                    {/* Locked Disputed Action Button */}
                    <button
                      disabled={isBusy}
                      onClick={() => handleAction(props.structure_id, 'lock_disputed')}
                      title="Lock as Disputed (Excluded from Stage 4)"
                      className="flex items-center justify-center gap-1 bg-red-600 hover:bg-red-700 text-white text-xs font-bold py-1.5 rounded-lg transition shadow-sm disabled:opacity-50 cursor-pointer"
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
