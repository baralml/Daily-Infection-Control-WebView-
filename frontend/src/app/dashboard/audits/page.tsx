"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { useRouter } from "next/navigation";
import {
  ClipboardCheck,
  Plus,
  Loader2,
  FileDown,
  Calendar,
  Layers,
  ChevronRight,
} from "lucide-react";import Link from "next/link";

export default function AuditsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [page, setPage] = useState(1);

  // Queries
  const { data: auditsPayload, isLoading: auditsLoading } = useQuery({
    queryKey: ["audits", page],
    queryFn: async () => {
      const res = await axiosInstance.get(`/audits?page=${page}&size=10`);
      return res.data;
    },
  });

  const { data: templates } = useQuery({
    queryKey: ["activeTemplates"],
    queryFn: async () => {
      const res = await axiosInstance.get("/templates");
      return res.data;
    },
    enabled: modalOpen,
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits/admin/departments");
      return res.data;
    },
    enabled: modalOpen,
  });

  // Mutation to initialize new Audit
  const createAuditMutation = useMutation({
    mutationFn: async (payload: { template_id: string; department_id: number; audited_at: string }) => {
      const res = await axiosInstance.post("/audits", payload);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["audits"] });
      setModalOpen(false);
      // Redirect to detailed audit sheet execution path
      router.push(`/dashboard/audits/${data.id}`);
    },
  });

  const handleStartAudit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDept || !selectedTemplate) return;
    createAuditMutation.mutate({
      template_id: selectedTemplate,
      department_id: parseInt(selectedDept),
      audited_at: new Date().toISOString(),
    });
  };

  const handleDownloadPDF = async (auditId: string) => {
    try {
      const res = await axiosInstance.get(`/audits/${auditId}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Audit_${auditId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download report", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Infection Audits</h1>
          <p className="text-sm text-text-secondary">
            Conduct, review, and export hospital clinical audits.
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-md bg-primary hover:bg-secondary py-2 px-4 text-sm font-semibold text-white shadow-sm cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          New Audit
        </button>
      </div>

      {/* Audits List */}
      {auditsLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="card-notion overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-left">
              <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                <tr>
                  <th className="px-6 py-3">Audit Details</th>
                  <th className="px-6 py-3">Department</th>
                  <th className="px-6 py-3">Auditor</th>
                  <th className="px-6 py-3">Execution Date</th>
                  <th className="px-6 py-3">Score</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-sm">
                {auditsPayload?.items.map((audit: any) => {
                  const dateStr = new Date(audit.audited_at).toLocaleDateString();
                  let badge = "bg-green-50 text-success border-green-200";
                  if (audit.compliance_percentage < 75) badge = "bg-red-50 text-danger border-red-200";
                  else if (audit.compliance_percentage < 90) badge = "bg-amber-50 text-warning border-amber-200";

                  return (
                    <tr key={audit.id} className="hover:bg-slate-50/50">
                      <td className="px-6 py-4">
                        <Link
                          href={`/dashboard/audits/${audit.id}`}
                          className="font-bold text-text-primary hover:text-primary block"
                        >
                          {audit.template_title}
                        </Link>
                        <span className="text-xs text-text-secondary">
                          Status: {audit.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium text-text-primary">
                        {audit.department_name}
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        {audit.auditor_name}
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        {dateStr}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`rounded-full border px-2 py-0.5 text-xs font-bold ${badge}`}>
                          {audit.compliance_percentage}%
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right space-x-2">
                        {audit.status === "SUBMITTED" && (
                          <button
                            onClick={() => handleDownloadPDF(audit.id)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-text-primary border border-border rounded hover:bg-hover cursor-pointer"
                          >
                            <FileDown className="h-3.5 w-3.5" />
                            PDF
                          </button>
                        )}
                        <Link
                          href={`/dashboard/audits/${audit.id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-primary rounded hover:bg-secondary"
                        >
                          View
                          <ChevronRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {auditsPayload?.pages > 1 && (
            <div className="flex items-center justify-between border-t border-border px-6 py-4">
              <button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
                className="text-xs font-semibold px-3 py-1.5 border border-border rounded hover:bg-hover disabled:opacity-40 cursor-pointer"
              >
                Previous
              </button>
              <span className="text-xs text-text-secondary">
                Page {page} of {auditsPayload.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(p + 1, auditsPayload.pages))}
                disabled={page === auditsPayload.pages}
                className="text-xs font-semibold px-3 py-1.5 border border-border rounded hover:bg-hover disabled:opacity-40 cursor-pointer"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modal Dialog for New Audit */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md bg-surface border border-border rounded-lg shadow-xl p-6">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Initialize New Audit
            </h3>
            
            <form onSubmit={handleStartAudit} className="mt-4 space-y-4">
              {/* Department */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Select Department
                </label>
                <select
                  required
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="input-notion focus:border-primary"
                >
                  <option value="">-- Choose Department --</option>
                  {departments?.map((d: any) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>

              {/* Template */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Select Audit Checklist
                </label>
                <select
                  required
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="input-notion focus:border-primary"
                >
                  <option value="">-- Choose Checklist --</option>
                  {templates?.map((t: any) => (
                    <option key={t.id} value={t.id}>
                      {t.title} (v{t.version})
                    </option>
                  ))}
                </select>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-3 border-t border-border mt-6">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAuditMutation.isPending}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer disabled:opacity-50"
                >
                  {createAuditMutation.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    "Start Audit"
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
