import React, { useState } from 'react';
import {
  UserCheck,
  History,
  Layers,
  Play,
  RefreshCw,
  User,
  LogOut,
  X,
  Menu,
  ShieldCheck,
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
  onLogout: () => void;
  isQueueOpen: boolean;
  onToggleQueue: () => void;
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
  onLogout,
  isQueueOpen,
  onToggleQueue,
}) => {
  const [showProfileModal, setShowProfileModal] = useState<boolean>(false);

  return (
    <>
      <header className="bg-[#fafaf7] border-b border-[#d2d2c8] text-slate-800 px-4 py-2.5 flex items-center justify-between z-30 shadow-sm shrink-0 gap-4">
        {/* Brand & System Title with Hamburger Toggle */}
        <div className="flex items-center gap-3">
          {/* Hamburger Toggle Button for Review Queue Sidebar */}
          {activeView === 'queue' && (
            <button
              onClick={onToggleQueue}
              title={isQueueOpen ? 'Close Review Queue' : 'Open Review Queue'}
              className="p-2 rounded-xl bg-[#efefea] hover:bg-[#29cc39]/20 text-slate-700 hover:text-[#22a229] border border-[#d2d2c8] transition cursor-pointer flex items-center justify-center"
            >
              {isQueueOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5 text-[#29cc39]" />}
            </button>
          )}

          <div className="bg-[#29cc39] p-2 rounded-xl text-white shadow-md shadow-[#29cc39]/20 flex items-center justify-center ">
            <Layers className="w-5 h-5" />
          </div>

          <div>
            <h1 className="text-base font-black tracking-tight text-slate-900 flex flex-col items-center gap-2">
              GIS AutoPilot
              <span className="text-xs bg-[#29cc39]/15 text-[#1b7a21] font-bold px-2 py-0.5 rounded-md border border-[#29cc39]/30">
                GeoAI + Multi-Dept SSOT
              </span>
            </h1>
          </div>
        </div>

        {/* Main Navigation Views */}
        <div className="flex items-center gap-1 bg-[#efefea] p-1 rounded-xl border border-[#d2d2c8]">
          <button
            onClick={() => onSelectView('queue')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeView === 'queue'
                ? 'bg-[#29cc39] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-[#e4e4dc]'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Lekhpal Review Queue</span>
            {pendingCount > 0 && (
              <span className="bg-amber-500 text-white font-black px-1.5 py-0.2 rounded-full text-[10px]">
                {pendingCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onSelectView('parcels')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeView === 'parcels'
                ? 'bg-[#29cc39] text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-[#e4e4dc]'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Consolidated Parcels (SSOT)</span>
          </button>
        </div>

        {/* Actions & Official Profile */}
        <div className="flex items-center gap-3">
          {/* Stage 4 Runner Trigger */}
          <button
            onClick={onTriggerStage4}
            disabled={isStage4Running}
            title="Run Stage 4 Multi-Department Consolidation"
            className="flex items-center gap-1.5 bg-[#29cc39] hover:bg-[#22a229] text-white text-xs font-bold px-3 py-1.5 rounded-lg transition border border-[#29cc39]/40 shadow-sm disabled:opacity-50 cursor-pointer"
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
            className="flex items-center gap-1.5 bg-[#efefea] hover:bg-[#e4e4dc] text-slate-700 text-xs font-bold px-3 py-1.5 rounded-lg transition border border-[#d2d2c8] shadow-sm cursor-pointer"
          >
            <History className="w-3.5 h-3.5 text-slate-500" />
            <span>Audit Log</span>
          </button>

          {/* Lekhpal Profile Dialog Button */}
          <button
            onClick={() => setShowProfileModal(true)}
            className="flex items-center gap-2 bg-[#efefea] hover:bg-[#e4e4dc] px-3 py-1.5 rounded-xl border border-[#d2d2c8] text-slate-800 transition cursor-pointer shadow-sm"
          >
            <div className="w-6 h-6 rounded-full bg-[#29cc39] text-white flex items-center justify-center text-xs font-bold">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-bold leading-tight">{currentOfficial.name}</div>
              <div className="text-[10px] text-amber-700 font-semibold">{currentOfficial.tehsil}</div>
            </div>
          </button>
        </div>
      </header>

      {/* Official Profile Dialog / Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl shadow-2xl w-full max-w-sm p-6 relative space-y-5 animate-in fade-in zoom-in duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[#e0e0d6] pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#29cc39]" />
                <h3 className="text-sm font-bold text-slate-800">Official Lekhpal Profile</h3>
              </div>
              <button
                onClick={() => setShowProfileModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-[#efefea] transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Lekhpal Info Body */}
            <div className="space-y-3 bg-[#f4f4ef] p-4 rounded-xl border border-[#e0e0d6]">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-[#29cc39] text-white font-black text-lg flex items-center justify-center shadow">
                  {currentOfficial.name.charAt(0)}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{currentOfficial.name}</h4>
                  <span className="text-[11px] bg-[#29cc39]/20 text-[#1b7a21] font-bold px-2 py-0.5 rounded">
                    {currentOfficial.role}
                  </span>
                </div>
              </div>

              <div className="space-y-1.5 text-xs text-slate-700 pt-2 border-t border-[#e0e0d6]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Official ID:</span>
                  <span className="font-semibold">{currentOfficial.official_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Assigned Tehsil:</span>
                  <span className="font-bold text-amber-700">{currentOfficial.tehsil}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">District Jurisdiction:</span>
                  <span className="font-semibold">{currentOfficial.district}</span>
                </div>
              </div>

              {/* Quick Switch Official Dropdown */}
              <div className="pt-2 border-t border-[#e0e0d6]">
                <label className="text-[11px] font-semibold text-slate-500 block mb-1">
                  Switch Active Lekhpal Profile:
                </label>
                <select
                  value={currentOfficial.official_id}
                  onChange={(e) => {
                    onSwitchOfficial(e.target.value);
                  }}
                  className="w-full bg-white border border-[#d2d2c8] text-xs text-slate-800 rounded-lg px-2.5 py-1.5 outline-none focus:border-[#29cc39] transition cursor-pointer"
                >
                  <option value="official_alpha">Ramesh Kumar (Tehsil-Alpha)</option>
                  <option value="official_beta">Suresh Singh (Tehsil-Beta)</option>
                </select>
              </div>
            </div>

            {/* Logout Action */}
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => {
                  setShowProfileModal(false);
                  onLogout();
                }}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-xl text-xs transition shadow flex items-center justify-center gap-2 cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout Session</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
