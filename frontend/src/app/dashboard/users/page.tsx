"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { useAuth } from "../../../context/AuthContext";
import {
  Users,
  Plus,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Mail,
  CheckCircle2,
  XCircle,
  MapPin,
  Image as ImageIcon,
  Check,
} from "lucide-react";

export default function UsersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"users" | "reports">("users");
  
  // Create User form state
  const [modalOpen, setModalOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const isAdmin = user?.role.name === "SUPER ADMIN" || user?.role.name === "HOSPITAL ADMIN";

  // Fetch Users
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const res = await axiosInstance.get("/users");
      return res.data;
    },
    enabled: isAdmin && activeTab === "users",
  });

  // Fetch System Roles
  const { data: roles } = useQuery({
    queryKey: ["roles"],
    queryFn: async () => {
      const res = await axiosInstance.get("/users/roles");
      return res.data;
    },
    enabled: modalOpen,
  });

  // Fetch Staff Anonymous Reports
  const { data: staffReports, isLoading: reportsLoading } = useQuery({
    queryKey: ["staffReports"],
    queryFn: async () => {
      const res = await axiosInstance.get("/staff-reports?skip=0&limit=100");
      return res.data;
    },
    enabled: isAdmin && activeTab === "reports",
  });

  // Create User Mutation
  const createUserMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await axiosInstance.post("/users", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setModalOpen(false);
      setEmail("");
      setFullName("");
      setPassword("");
      setRoleId("");
      setErrorMsg("");
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to register user");
    },
  });

  // Activate User Account Mutation (Go Live)
  const activateUserMutation = useMutation({
    mutationFn: async (userId: string) => {
      const res = await axiosInstance.put(`/users/${userId}`, { is_active: true });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      alert("User account activated and is now live!");
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to activate user account.");
    }
  });

  // Resolve Staff Report Mutation
  const resolveReportMutation = useMutation({
    mutationFn: async (reportId: string) => {
      const res = await axiosInstance.patch(`/staff-reports/${reportId}/resolve?is_resolved=true`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["staffReports"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to resolve report.");
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !fullName || !password || !roleId) return;
    createUserMutation.mutate({
      email,
      full_name: fullName,
      password,
      role_id: parseInt(roleId),
      is_active: true,
    });
  };

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-[500px] text-center">
        <ShieldAlert className="h-12 w-12 text-danger mb-3" />
        <h3 className="text-base font-bold text-text-primary">Unauthorized Access</h3>
        <p className="text-sm text-text-secondary mt-1">
          You need Hospital Administrator or Super Admin permissions to manage users.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">User & Staff Administration</h1>
          <p className="text-sm text-text-secondary">
            Manage clinical auditor accounts, approve live self-registrations, and review anonymous staff safety reports.
          </p>
        </div>
        {activeTab === "users" && (
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 rounded-md bg-primary hover:bg-secondary py-2 px-4 text-sm font-semibold text-white shadow-sm cursor-pointer transition-all"
          >
            <Plus className="h-4 w-4" />
            Add New User
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border pb-px">
        <button
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "users"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          User Accounts
        </button>
        <button
          onClick={() => setActiveTab("reports")}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "reports"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          Anonymous Staff Reports
        </button>
      </div>

      {activeTab === "users" ? (
        /* Users Accounts List Table */
        usersLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="card-notion overflow-hidden p-0 border border-border bg-surface">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-border text-left">
                <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                  <tr>
                    <th className="px-6 py-3">Full Name</th>
                    <th className="px-6 py-3">Email Address</th>
                    <th className="px-6 py-3">Role Designation</th>
                    <th className="px-6 py-3">Access Level</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm text-text-primary">
                  {users?.map((u: any) => (
                    <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-bold text-text-primary flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-slate-100 text-text-secondary flex items-center justify-center font-bold text-xs uppercase">
                          {u.full_name.charAt(0)}
                        </div>
                        {u.full_name}
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        <span className="flex items-center gap-1.5">
                          <Mail className="h-3.5 w-3.5" />
                          {u.email}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded bg-slate-100 border border-slate-200 px-2 py-0.5 text-xs font-bold text-text-secondary uppercase">
                          {u.role.name}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs text-text-secondary max-w-xs truncate">
                        {Object.keys(u.role.permissions.modules || {}).join(", ")}
                      </td>
                      <td className="px-6 py-4">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-success text-xs font-bold">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Active
                          </span>
                        ) : (
                          <div className="flex items-center gap-2.5">
                            <span className="inline-flex items-center gap-1 text-danger text-xs font-bold">
                              <XCircle className="h-3.5 w-3.5" />
                              Pending Approval
                            </span>
                            <button
                              onClick={() => activateUserMutation.mutate(u.id)}
                              disabled={activateUserMutation.isPending}
                              className="px-2 py-1 text-[10px] font-bold border border-primary text-primary rounded bg-primary/5 hover:bg-primary hover:text-white cursor-pointer transition-all"
                            >
                              Approve Access
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}

                  {users?.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center py-10 text-text-secondary text-sm">
                        No users registered.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )
      ) : (
        /* Anonymous Staff Reports List Table */
        reportsLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="card-notion overflow-hidden p-0 border border-border bg-surface">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-border text-left">
                <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                  <tr>
                    <th className="px-6 py-3">Report Details</th>
                    <th className="px-6 py-3">Photo Attachment</th>
                    <th className="px-6 py-3">GPS Location</th>
                    <th className="px-6 py-3">Submitted Date</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm text-text-primary">
                  {staffReports?.map((r: any) => (
                    <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 max-w-md">
                        <p className="text-sm font-bold text-text-primary whitespace-pre-wrap leading-relaxed">
                          {r.description}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        {r.photo_url ? (
                          <a
                            href={r.photo_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-2 py-1 border border-border rounded text-xs font-semibold text-text-primary bg-slate-50 hover:bg-hover transition-colors"
                          >
                            <ImageIcon className="h-3.5 w-3.5 text-text-secondary" />
                            View Evidence
                          </a>
                        ) : (
                          <span className="text-xs text-text-secondary italic">No Photo</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {r.latitude && r.longitude ? (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${r.latitude},${r.longitude}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline font-semibold"
                          >
                            <MapPin className="h-4 w-4" />
                            {r.latitude.toFixed(5)}, {r.longitude.toFixed(5)}
                          </a>
                        ) : (
                          <span className="text-xs text-text-secondary italic">No Coordinates</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs text-text-secondary">
                        {new Date(r.created_at).toLocaleDateString()} {new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-6 py-4">
                        {r.is_resolved ? (
                          <span className="inline-flex items-center gap-1 text-success text-xs font-bold">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Resolved
                          </span>
                        ) : (
                          <button
                            onClick={() => resolveReportMutation.mutate(r.id)}
                            disabled={resolveReportMutation.isPending}
                            className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold cursor-pointer transition-colors shadow-sm"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Resolve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}

                  {staffReports?.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center py-10 text-text-secondary text-sm">
                        No anonymous safety reports submitted by staff.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}

      {/* Modal Dialog Form */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 animate-fade-in">
          <div className="w-full max-w-md bg-surface border border-border rounded-lg shadow-xl p-6 relative">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Register New System Account
            </h3>

            {errorMsg && (
              <div className="mt-3 flex items-center gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-xs text-danger">
                <ShieldAlert className="h-4 w-4 shrink-0" />
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Sabarno Baral"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="input-notion focus:border-primary"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. sbaral@hospital.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-notion focus:border-primary"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Designated System Role
                </label>
                <select
                  required
                  value={roleId}
                  onChange={(e) => setRoleId(e.target.value)}
                  className="input-notion focus:border-primary text-xs"
                >
                  <option value="">-- Choose Role --</option>
                  {roles?.map((r: any) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Default Password
                </label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-notion focus:border-primary"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-border mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setModalOpen(false);
                    setErrorMsg("");
                  }}
                  className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer disabled:opacity-50"
                >
                  {createUserMutation.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Registering...
                    </>
                  ) : (
                    "Register Staff"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
