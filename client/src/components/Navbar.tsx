import React from 'react';
import {
  MapPin,
  UserCheck,
  History,
  Layers,
  Play,
  RefreshCw,
} from 'lucide-react';
import type { OfficialProfile } from '../types';

interface NavbarProps {
  currentOfficial: OfficialProfile;
  onSwitchOfficial: (officialId: string) => void;
  activeView: 'queue' | 'parcels';
  onSelectView: (view: 'queue' | 'parcels') => void;
  onOpenAuditLog: () => void;
  onTriggerStage4: () => void;
  isStage4Running: boolean;
  pendingCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentOfficial,
  onSwitchOfficial,
  activeView,
  onSelectView,
  onOpenAuditLog,
  onTriggerStage4,
  isStage4Running,
  pendingCount,
}) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white px-4 py-2.5 flex items-center justify-between z-30 shadow-md shrink-0">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-lg text-white shadow">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
            Urban Land Geospatial Integration
            <span className="text-xs bg-indigo-500/20 text-indigo-300 font-medium px-2 py-0.5 rounded border border-indigo-500/30">
              GeoAI + Multi-Dept SSOT
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Automated Feature Extraction & Cadastral Dispute Resolution
          </p>
        </div>
      </div>

      {/* Main Navigation Views */}
      <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700/60">
        <button
          onClick={() => onSelectView('queue')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activeView === 'queue'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          <span>Lekhpal Review Queue</span>
          {pendingCount > 0 && (
            <span className="bg-amber-500 text-slate-950 font-bold px-1.5 py-0.2 rounded-full text-[10px]">
              {pendingCount}
            </span>
          )}
        </button>

        <button
          onClick={() => onSelectView('parcels')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activeView === 'parcels'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Consolidated Parcels (SSOT)</span>
        </button>
      </div>

      {/* Actions & Official Switcher */}
      <div className="flex items-center gap-3">
        {/* Stage 4 Runner Trigger */}
        <button
          onClick={onTriggerStage4}
          disabled={isStage4Running}
          title="Run Stage 4 Multi-Department Consolidation"
          className="flex items-center gap-1.5 bg-emerald-600/90 hover:bg-emerald-600 text-white text-xs font-medium px-3 py-1.5 rounded-md transition border border-emerald-500/40 shadow-sm disabled:opacity-50"
        >
          {isStage4Running ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5" />
          )}
          <span>{isStage4Running ? 'Consolidating...' : 'Run Stage 4'}</span>
        </button>

        {/* Audit Log Modal Trigger */}
        <button
          onClick={onOpenAuditLog}
          title="View Human Verification Audit Trail"
          className="flex items-center gap-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-md transition border border-slate-700 shadow-sm"
        >
          <History className="w-3.5 h-3.5 text-slate-400" />
          <span>Audit Log</span>
        </button>

        {/* Synthetic Official Switcher */}
        <div className="flex items-center gap-2 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700">
          <MapPin className="w-4 h-4 text-indigo-400 shrink-0" />
          <div className="text-left">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-slate-100">
                {currentOfficial.name}
              </span>
              <span className="text-[10px] bg-slate-700 text-indigo-300 px-1.5 py-0.2 rounded font-medium">
                {currentOfficial.role}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-1">
              <span>Assigned Tehsil:</span>
              <span className="text-amber-400 font-semibold">
                {currentOfficial.tehsil}
              </span>
            </div>
          </div>

          <select
            value={currentOfficial.official_id}
            onChange={(e) => onSwitchOfficial(e.target.value)}
            className="ml-2 bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded px-2 py-1 outline-none hover:border-indigo-500 focus:border-indigo-500 transition cursor-pointer"
          >
            <option value="official_alpha">Ramesh Kumar (Tehsil-Alpha)</option>
            <option value="official_beta">Suresh Singh (Tehsil-Beta)</option>
          </select>
        </div>
      </div>
    </header>
  );
};
