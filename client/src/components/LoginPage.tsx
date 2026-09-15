import React, { useState } from 'react';
import { Layers, Lock, User, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import type { OfficialProfile } from '../types';

interface LoginPageProps {
  onLogin: (official: OfficialProfile) => void;
  onNavigateToSignup: () => void;
}

// Synthetic officials pre-configured in system (§8)
const SYNTHETIC_OFFICIALS: Record<string, OfficialProfile & { defaultPass: string }> = {
  official_alpha: {
    official_id: 'official_alpha',
    username: 'ramesh_alpha',
    name: 'Ramesh Kumar',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
    defaultPass: 'lekhpal123',
  },
  official_beta: {
    official_id: 'official_beta',
    username: 'suresh_beta',
    name: 'Suresh Singh',
    role: 'Lekhpal',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
    defaultPass: 'lekhpal123',
  },
  revenue_alpha: {
    official_id: 'revenue_alpha',
    username: 'revenue_alpha',
    name: 'Vikram Sharma',
    role: 'Revenue Inspector',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
    defaultPass: 'revenue123',
  },
  tehsildar_alpha: {
    official_id: 'tehsildar_alpha',
    username: 'tehsildar_alpha',
    name: 'Dr. Anita Verma',
    role: 'Tehsildar',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
    defaultPass: 'tehsildar123',
  },
  revenue_beta: {
    official_id: 'revenue_beta',
    username: 'revenue_beta',
    name: 'mahesh Sharma',
    role: 'Revenue Inspector',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
    defaultPass: 'revenue123',
  },
  tehsildar_beta: {
    official_id: 'tehsildar_beta',
    username: 'tehsildar_beta',
    name: 'Mr Avinash gupta',
    role: 'Tehsildar',
    tehsil: 'Tehsil-Beta',
    district: 'Kumaon District',
    defaultPass: 'tehsildar123',
  },
};

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onNavigateToSignup }) => {
  const [selectedOfficialId, setSelectedOfficialId] = useState<string>('official_alpha');
  const [password, setPassword] = useState<string>('lekhpal123');
  const [error, setError] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const official = SYNTHETIC_OFFICIALS[selectedOfficialId];
    if (official) {
      if (!password) {
        setError('Please enter your password.');
        return;
      }
      onLogin({
        official_id: official.official_id,
        username: official.username,
        name: official.name,
        role: official.role,
        tehsil: official.tehsil,
        district: official.district,
      });
    } else {
      setError('Invalid official selection.');
    }
  };

  const handleQuickSelect = (id: string) => {
    setSelectedOfficialId(id);
    setPassword('lekhpal123');
    setError('');
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#f4f4ef] p-4 relative overflow-hidden">
      {/* Background Subtle Map Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#d2d2c8_1px,transparent_1px)] [background-size:16px_16px] opacity-60 pointer-events-none" />

      {/* Main Login Card */}
      <div className="w-full max-w-md bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl shadow-xl p-8 relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#29cc39] text-white shadow-lg shadow-[#29cc39]/25 mb-1">
            <Layers className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-800">
            GIS AutoPilot
          </h1>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            GeoAI Feature Extraction & Cadastral Land Records Dispute Management System
          </p>
        </div>

        {/* Quick Selection Pills */}
        <div className="space-y-2">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
            Select Official Account (3-Layer Workflow):
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickSelect('official_alpha')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'official_alpha'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">Ramesh Kumar</span>
                {selectedOfficialId === 'official_alpha' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-amber-700 font-medium mt-1 bg-amber-50 px-1 rounded border border-amber-200/60 w-max">
                Lekhpal (Alpha)
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickSelect('official_beta')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'official_beta'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">Suresh Singh</span>
                {selectedOfficialId === 'official_beta' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-indigo-700 font-medium mt-1 bg-indigo-50 px-1 rounded border border-indigo-200/60 w-max">
                Lekhpal (Beta)
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickSelect('revenue_alpha')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'revenue_alpha'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">Vikram Sharma</span>
                {selectedOfficialId === 'revenue_alpha' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-blue-700 font-medium mt-1 bg-blue-50 px-1 rounded border border-blue-200/60 w-max">
                Revenue Inspector
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickSelect('revenue_beta')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'revenue_beta'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">mahesh Sharma</span>
                {selectedOfficialId === 'revenue_beta' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-blue-700 font-medium mt-1 bg-blue-50 px-1 rounded border border-blue-200/60 w-max">
                Revenue Inspector
              </span>
            </button>

            

            <button
              type="button"
              onClick={() => handleQuickSelect('tehsildar_alpha')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'tehsildar_alpha'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">mahesh Sharma</span>
                {selectedOfficialId === 'tehsildar_alpha' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-purple-700 font-medium mt-1 bg-purple-50 px-1 rounded border border-purple-200/60 w-max">
                Tehsildar (Final DB)
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickSelect('tehsildar_beta')}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedOfficialId === 'tehsildar_beta'
                  ? 'border-[#29cc39] bg-[#29cc39]/10 shadow-sm ring-1 ring-[#29cc39]'
                  : 'border-[#e0e0d6] bg-white hover:border-slate-300'
              }`}
            >
              
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-slate-800">Mr Avinash gupta</span>
                {selectedOfficialId === 'tehsildar_beta' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#29cc39]" />
                )}
              </div>
              <span className="text-[9px] text-purple-700 font-medium mt-1 bg-purple-50 px-1 rounded border border-purple-200/60 w-max">
                Tehsildar (Final DB)
              </span>
            </button>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg p-2.5">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Official ID / Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                disabled
                value={SYNTHETIC_OFFICIALS[selectedOfficialId]?.username || ''}
                className="w-full bg-[#f4f4ef] border border-[#d2d2c8] rounded-xl pl-9 pr-3 py-2 text-xs font-medium text-slate-700 cursor-not-allowed"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Security Credentials / Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password..."
                className="w-full bg-white border border-[#d2d2c8] rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39] focus:ring-1 focus:ring-[#29cc39] transition"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-[#29cc39] hover:bg-[#22a229] text-white font-bold py-2.5 rounded-xl text-xs transition shadow-md shadow-[#29cc39]/20 flex items-center justify-center gap-2 group cursor-pointer"
          >
            <span>Access Lekhpal Portal</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </form>

        {/* Security Note & Signup Navigation */}
        <div className="pt-4 border-t border-[#e0e0d6] flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#29cc39]" />
            <span>SIH 2026 Secured</span>
          </div>

          <button
            type="button"
            onClick={onNavigateToSignup}
            className="text-indigo-600 hover:text-indigo-800 font-semibold hover:underline cursor-pointer"
          >
            New Lekhpal? Register Account
          </button>
        </div>
      </div>
    </div>
  );
};
