import React from 'react';
import { X, History, Lock, CheckCircle2, RefreshCw } from 'lucide-react';
import type { AuditLogEntry } from '../types';

interface AuditLogModalProps {
  isOpen: boolean;
  onClose: () => void;
  entries: AuditLogEntry[];
  onRefresh: () => void;
  isLoading: boolean;
}

export const AuditLogModal: React.FC<AuditLogModalProps> = ({
  isOpen,
  onClose,
  entries,
  onRefresh,
  isLoading,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl text-white overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="bg-indigo-600/30 p-2 rounded-lg text-indigo-400 border border-indigo-500/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Human Verification Audit Log
                <span className="text-xs bg-slate-800 text-slate-400 font-normal px-2 py-0.5 rounded-full border border-slate-700">
                  {entries.length} recorded events
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Append-only government decision trail (§8, §18)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh log"
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body: Audit Trail Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {entries.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-400">
              No human verification actions recorded yet.
            </div>
          ) : (
            entries.map((entry) => {
              const isVerified = entry.action === 'mark_verified';
              return (
                <div
                  key={entry.event_id}
                  className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isVerified ? (
                        <span className="text-xs bg-emerald-500/20 text-emerald-300 font-bold px-2 py-0.5 rounded border border-emerald-500/40 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Mark Verified</span>
                        </span>
                      ) : (
                        <span className="text-xs bg-red-500/20 text-red-300 font-bold px-2 py-0.5 rounded border border-red-500/40 flex items-center gap-1">
                          <Lock className="w-3 h-3" />
                          <span>Locked Disputed</span>
                        </span>
                      )}
                      <span className="text-xs font-bold text-slate-100">
                        Structure: {entry.structure_id}
                      </span>
                    </div>

                    <span className="text-[11px] text-slate-400 font-mono">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs bg-slate-900/60 p-2 rounded-lg border border-slate-800/60">
                    <div>
                      <span className="text-slate-500 block text-[10px]">Official / Lekhpal:</span>
                      <span className="font-semibold text-slate-200">
                        {entry.official_name} ({entry.official_id})
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">Tehsil:</span>
                      <span className="text-amber-400 font-semibold">{entry.tehsil}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px]">State Transition:</span>
                      <span className="text-slate-300">
                        <span className="line-through text-slate-500 mr-1">
                          {entry.previous_status}
                        </span>
                        &rarr; <strong className="text-white">{entry.new_status}</strong>
                      </span>
                    </div>
                  </div>

                  {entry.notes && (
                    <div className="text-xs bg-slate-900/40 p-2 rounded border border-slate-800/40 text-slate-300">
                      <span className="text-slate-500 text-[10px] block font-semibold">
                        Inspection Remarks:
                      </span>
                      {entry.notes}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
