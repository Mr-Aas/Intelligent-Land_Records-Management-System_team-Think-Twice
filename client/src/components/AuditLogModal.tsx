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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
      <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl text-slate-800 overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-[#d2d2c8] flex items-center justify-between bg-[#efefea]">
          <div className="flex items-center gap-2.5">
            <div className="bg-[#29cc39]/20 p-2 rounded-xl text-[#1b7a21] border border-[#29cc39]/30">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
                Human Verification Audit Log
                <span className="text-xs bg-[#e4e4dc] text-slate-600 font-bold px-2 py-0.5 rounded-full">
                  {entries.length} recorded events
                </span>
              </h2>
              <p className="text-xs text-slate-500">
                Append-only government decision trail (§8, §18)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh log"
              className="p-1.5 rounded-lg bg-white hover:bg-[#e4e4dc] border border-[#d2d2c8] text-slate-700 transition cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-white hover:bg-[#e4e4dc] border border-[#d2d2c8] text-slate-500 hover:text-slate-900 transition cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body: Audit Trail Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#f4f4ef]">
          {entries.length === 0 ? (
            <div className="py-16 text-center text-xs font-semibold text-slate-500">
              No human verification actions recorded yet.
            </div>
          ) : (
            entries.map((entry) => {
              const isVerified = entry.action === 'mark_verified';
              return (
                <div
                  key={entry.event_id}
                  className="p-4 bg-white border border-[#d2d2c8] rounded-xl space-y-2 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {isVerified ? (
                        <span className="text-xs bg-[#29cc39]/15 text-[#1b7a21] font-extrabold px-2 py-0.5 rounded-md border border-[#29cc39]/30 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Mark Verified</span>
                        </span>
                      ) : (
                        <span className="text-xs bg-red-100 text-red-700 font-extrabold px-2 py-0.5 rounded-md border border-red-300 flex items-center gap-1">
                          <Lock className="w-3 h-3" />
                          <span>Locked Disputed</span>
                        </span>
                      )}
                      <span className="text-xs font-black text-slate-900">
                        Structure: {entry.structure_id}
                      </span>
                    </div>

                    <span className="text-[11px] text-slate-500 font-mono">
                      {new Date(entry.timestamp).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-xs bg-[#f4f4ef] p-2.5 rounded-lg border border-[#e0e0d6]">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Official ID:</span>
                      <span className="font-bold text-slate-800">{entry.official_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Tehsil Jurisdiction:</span>
                      <span className="font-bold text-amber-700">{entry.tehsil}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Previous State:</span>
                      <span className="font-semibold text-slate-700 uppercase">{entry.previous_status}</span>
                    </div>
                  </div>

                  {entry.notes && (
                    <p className="text-xs text-slate-600 bg-[#efefea] p-2 rounded-lg border border-[#e0e0d6] font-medium">
                      Remarks: "{entry.notes}"
                    </p>
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
