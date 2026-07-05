"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { useAuth } from "../../../context/AuthContext";
import { Building2, Plus, Loader2, ArrowUpRight, AlertTriangle, ShieldCheck } from "lucide-react";

export default function DepartmentsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const isAdmin = user?.role.name === "SUPER ADMIN" || user?.role.name === "HOSPITAL ADMIN";

  // Fetch Departments
  const { data: departments, isLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits/admin/departments");
      return res.data;
    },
  });

  // Create Department mutation
  const createDeptMutation = useMutation({
    mutationFn: async (payload: { name: string; code: string }) => {
      const res = await axiosInstance.post("/audits/admin/departments", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] });
      setModalOpen(false);
      setName("");
      setCode("");
      setErrorMsg("");
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to create department");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !code) return;
    createDeptMutation.mutate({ name, code: code.toUpperCase() });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Hospital Departments</h1>
          <p className="text-sm text-text-secondary">
            View clinical departments, access codes, and register new wards.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 rounded-md bg-primary hover:bg-secondary py-2 px-4 text-sm font-semibold text-white shadow-sm cursor-pointer transition-all"
          >
            <Plus className="h-4 w-4" />
            Add Department
          </button>
        )}
      </div>

      {/* Grid List */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {departments?.map((dept: any) => (
            <div
              key={dept.id}
              className="card-notion p-6 hover:shadow-lg transition-all relative overflow-hidden group bg-surface border border-border"
            >
              {/* Decorative top border */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-secondary opacity-80" />

              <div className="flex items-center justify-between mb-4">
                <div className="rounded-lg bg-slate-50 p-2.5 text-secondary group-hover:scale-110 transition-transform">
                  <Building2 className="h-6 w-6" />
                </div>
                <span className="rounded-md bg-slate-100 border border-slate-200 px-2 py-0.5 text-xs font-bold text-text-secondary uppercase tracking-wider">
                  {dept.code}
                </span>
              </div>

              <h3 className="font-bold text-text-primary text-base mb-1">
                {dept.name}
              </h3>
              <p className="text-xs text-text-secondary">
                Registered on: {new Date(dept.created_at).toLocaleDateString()}
              </p>

              {/* Dynamic Stats Section */}
              <div className="grid grid-cols-2 gap-4 border-t border-border mt-6 pt-4 text-xs">
                <div>
                  <span className="text-text-secondary block">Compliance Status</span>
                  <span className="font-bold text-success flex items-center gap-0.5 mt-0.5">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Active Wards
                  </span>
                </div>
                <div>
                  <span className="text-text-secondary block">System ID</span>
                  <span className="font-bold text-text-primary block mt-0.5">
                    #{dept.id}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {departments?.length === 0 && (
            <div className="col-span-full flex flex-col items-center justify-center h-64 border border-dashed border-border rounded-xl bg-slate-50/30 text-text-secondary">
              <Building2 className="h-10 w-10 mb-2 opacity-50" />
              <p className="text-sm font-semibold">No Wards Registered</p>
            </div>
          )}
        </div>
      )}

      {/* Modal Dialog Form */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 animate-fade-in">
          <div className="w-full max-w-md bg-surface border border-border rounded-lg shadow-xl p-6 relative">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Register New Department
            </h3>

            {errorMsg && (
              <div className="mt-3 flex items-center gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-xs text-danger">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Department Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Neonatal Intensive Care Unit"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-notion focus:border-primary"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Department Code (max 10 chars)
                </label>
                <input
                  type="text"
                  required
                  maxLength={10}
                  placeholder="e.g. NICU"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="input-notion focus:border-primary uppercase"
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
                  disabled={createDeptMutation.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer disabled:opacity-50"
                >
                  {createDeptMutation.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Register"
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
