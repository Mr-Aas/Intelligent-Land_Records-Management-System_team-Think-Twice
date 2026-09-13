import React, { useState } from 'react';
import { Layers, ArrowLeft, UserPlus, CheckCircle2, ShieldAlert } from 'lucide-react';

interface SignupPageProps {
  onNavigateToLogin: () => void;
}

export const SignupPage: React.FC<SignupPageProps> = ({ onNavigateToLogin }) => {
  const [formData, setFormData] = useState({
    fullName: '',
    officialId: '',
    email: '',
    password: '',
    confirmPassword: '',
    tehsil: 'Tehsil-Alpha',
    district: 'Kumaon District',
    role: 'Lekhpal',
  });

  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Front-end preview creation (unactivated backend route per user specifications)
    setIsSubmitted(true);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#f4f4ef] p-4 relative overflow-hidden">
      {/* Subtle Map Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#d2d2c8_1px,transparent_1px)] [background-size:16px_16px] opacity-60 pointer-events-none" />

      {/* Main Signup Card */}
      <div className="w-full max-w-lg bg-[#fafaf7] border border-[#d2d2c8] rounded-2xl shadow-xl p-8 relative z-10 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#e0e0d6] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#29cc39] text-white flex items-center justify-center shadow">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800">GIS AutoPilot</h1>
              <p className="text-xs text-slate-500">Lekhpal Account Registration</p>
            </div>
          </div>

          <button
            onClick={onNavigateToLogin}
            className="flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 font-medium bg-[#efefea] hover:bg-[#e4e4dc] px-3 py-1.5 rounded-lg transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Login</span>
          </button>
        </div>

        {isSubmitted ? (
          <div className="py-8 text-center space-y-4">
            <div className="w-16 h-16 bg-[#29cc39]/10 text-[#29cc39] rounded-full flex items-center justify-center mx-auto border border-[#29cc39]/30">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-slate-800">Registration Profile Created</h2>
            <p className="text-xs text-slate-600 max-w-sm mx-auto leading-relaxed">
              Account request for <span className="font-semibold text-slate-900">{formData.fullName}</span> ({formData.officialId}) in <span className="font-semibold text-amber-700">{formData.tehsil}</span> has been logged.
            </p>
            <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-xl text-xs flex items-start gap-2 max-w-sm mx-auto text-left">
              <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>Note: Per system specifications, signup is currently in preview mode. Please use activated Lekhpal credentials on the login screen.</span>
            </div>
            <button
              onClick={onNavigateToLogin}
              className="mt-2 inline-flex items-center gap-2 bg-[#29cc39] hover:bg-[#22a229] text-white font-bold px-5 py-2.5 rounded-xl text-xs shadow transition cursor-pointer"
            >
              <span>Return to Login Screen</span>
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Official ID / Employee Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. LKH-2026-003"
                  value={formData.officialId}
                  onChange={(e) => setFormData({ ...formData, officialId: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Official Email</label>
                <input
                  type="email"
                  required
                  placeholder="lekhpal@gov.in"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Assigned Tehsil</label>
                <select
                  value={formData.tehsil}
                  onChange={(e) => setFormData({ ...formData, tehsil: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                >
                  <option value="Tehsil-Alpha">Tehsil-Alpha</option>
                  <option value="Tehsil-Beta">Tehsil-Beta</option>
                  <option value="Tehsil-Gamma">Tehsil-Gamma</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Confirm Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full bg-white border border-[#d2d2c8] rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#29cc39]"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#29cc39] hover:bg-[#22a229] text-white font-bold py-2.5 rounded-xl text-xs transition shadow flex items-center justify-center gap-2 cursor-pointer mt-2"
            >
              <UserPlus className="w-4 h-4" />
              <span>Create Official Account</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
