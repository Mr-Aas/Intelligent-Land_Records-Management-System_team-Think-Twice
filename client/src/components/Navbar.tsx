import React from 'react';
import { useState } from 'react';
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
  const [showprofile, setshowprofile] = useState<boolean>(true)
  return (
    <header className="bg-gray-400 border-b border-slate-800 text-white px-4 py-2.5 flex items-center justify-between z-30 shadow-md shrink-0 gap-4">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="bg-indigo-600 p-2 rounded-lg text-white shadow">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2 flex-col">
            Survey Automation
            <span className="text-xs bg-indigo-500/20 text-indigo-300 font-medium px-2 py-0.5 rounded border border-indigo-500/30">
              One parcel , One data
            </span>
            <p className="text-xs text-slate-400">
              Dispute Resolution
            </p>
          </h1>
        </div>
      </div>

      {/* Main Navigation Views */}
      <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700/60">
        <button
          onClick={() => onSelectView('queue')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${activeView === 'queue'
            ? 'bg-teal-600 text-white shadow-sm'
            : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
        >
          <UserCheck className="w-4 h-4" />
          <span>Conflicts</span>
          {pendingCount > 0 && (
            <span className="bg-amber-500 text-slate-950 font-bold px-1.5 py-0.2 rounded-full text-[10px]">
              {pendingCount}
            </span>
          )}
        </button>

        <button
          onClick={() => onSelectView('parcels')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${activeView === 'parcels'
            ? 'bg-indigo-600 text-white shadow-sm'
            : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
            }`}
        >
          <Layers className="w-4 h-4" />
          <span>Parcels</span>
        </button>
      </div>

      {/* Actions & Official Switcher */}
      <div className="flex items-center gap-3">
        {/* Stage 4 Runner Trigger */}


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
        {showprofile ? <div><div className={`flex items-center gap-2 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700 overflow-hidden  mr-4h-10 `}></div></div> :
          <div className={`flex items-center gap-2 bg-slate-800/90 px-3 py-1.5 rounded-lg border border-slate-700 overflow-hidden  mr-4h-10 `}>
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


          </div>}
      </div>

    </header>
  );
};
