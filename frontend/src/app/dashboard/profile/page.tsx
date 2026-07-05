"use client";

import React, { useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import axiosInstance from "../../../lib/axios";
import { User, Mail, Shield, CheckCircle, Loader2, AlertCircle, Phone, Lock } from "lucide-react";

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [phoneNumber, setPhoneNumber] = useState(user?.phone_number || "");
  const [password, setPassword] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg("");
    setErrorMsg("");

    try {
      const payload: any = {
        full_name: fullName,
        phone_number: phoneNumber || null,
      };

      if (password) {
        payload.password = password;
      }

      await axiosInstance.put("/users/me", payload);
      await refreshUser();
      
      setSuccessMsg("Profile details updated successfully!");
      setPassword("");
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Failed to update profile details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-text-primary">My Account Settings</h1>
        <p className="text-sm text-text-secondary">
          Manage your personal details, credentials, and check your security configuration.
        </p>
      </div>

      <div className="card-notion bg-surface border border-border shadow-sm p-6 space-y-6">
        {/* Profile Card Summary */}
        <div className="flex items-center gap-4 border-b border-border pb-6">
          <div className="h-16 w-16 rounded-full bg-primary text-white flex items-center justify-center font-bold text-2xl uppercase shadow-sm">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div>
            <h2 className="text-base font-bold text-text-primary">{user?.full_name}</h2>
            <div className="flex items-center gap-1.5 text-xs text-text-secondary mt-1">
              <Shield className="h-3.5 w-3.5" />
              <span className="font-semibold uppercase tracking-wider">{user?.role?.name}</span>
              <span className="inline-flex items-center gap-1 rounded bg-green-50 dark:bg-emerald-950/20 text-success text-[10px] px-1.5 py-0.5 font-bold border border-green-200/50">
                <CheckCircle className="h-3 w-3" />
                Active
              </span>
            </div>
          </div>
        </div>

        {/* Update Profile Form */}
        <form onSubmit={handleUpdate} className="space-y-4">
          {successMsg && (
            <div className="rounded-md bg-green-50 dark:bg-emerald-950/20 border border-green-200 dark:border-emerald-900/50 p-3 text-xs text-success flex items-center gap-2">
              <CheckCircle className="h-4 w-4 shrink-0" />
              {successMsg}
            </div>
          )}

          {errorMsg && (
            <div className="rounded-md bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 p-3 text-xs text-danger flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {errorMsg}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Full Name */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                <User className="h-3.5 w-3.5 text-text-secondary" />
                Full Name
              </label>
              <input
                type="text"
                required
                className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>

            {/* Email Address (Disabled) */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                <Mail className="h-3.5 w-3.5 text-text-secondary" />
                Email Address (ReadOnly)
              </label>
              <input
                type="email"
                disabled
                className="input-notion bg-slate-50 dark:bg-slate-950 text-text-secondary border border-border/60 text-xs cursor-not-allowed"
                value={user?.email || ""}
              />
            </div>

            {/* Phone Number */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                <Phone className="h-3.5 w-3.5 text-text-secondary" />
                Phone Number
              </label>
              <input
                type="text"
                placeholder="e.g. +91 98765 43210"
                className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
              />
            </div>

            {/* Password (Optional for updates) */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                <Lock className="h-3.5 w-3.5 text-text-secondary" />
                Change Password (Optional)
              </label>
              <input
                type="password"
                placeholder="Leave blank to keep current password"
                className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-border mt-6">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Updating...
                </>
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Permissions Summary Card */}
      <div className="card-notion bg-surface border border-border shadow-sm p-6 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">System Access Permissions</h3>
        <p className="text-xs text-text-secondary leading-relaxed">
          Your role <span className="font-bold text-text-primary">{user?.role?.name}</span> is configured with the following module capabilities:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {Object.entries(user?.role?.permissions?.modules || {}).map(([mod, ops]: [string, any]) => (
            <div key={mod} className="p-3 border border-border/80 bg-slate-50/50 dark:bg-slate-900/50 rounded-lg text-xs">
              <span className="font-bold text-text-primary capitalize">{mod}</span>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {ops.map((op: string) => (
                  <span key={op} className="bg-slate-200/60 dark:bg-slate-800 border border-border text-text-secondary font-semibold uppercase text-[9px] px-1.5 py-0.5 rounded">
                    {op}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
