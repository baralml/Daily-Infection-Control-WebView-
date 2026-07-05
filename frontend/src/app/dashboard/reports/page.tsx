"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { useRouter } from "next/navigation";
import {
  FileSpreadsheet,
  FileDown,
  Loader2,
  Filter,
  AlertOctagon,
  Calendar,
  Footprints,
  Eye,
} from "lucide-react";

export default function ReportsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"audits" | "rounds">("audits");
  const [deptFilter, setDeptFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [exporting, setExporting] = useState(false);

  // Fetch Departments
  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits/admin/departments");
      return res.data;
    },
  });

  // Fetch Audits List based on filters
  const { data: auditsPayload, isLoading: auditsLoading } = useQuery({
    queryKey: ["auditsReport", deptFilter, statusFilter, riskFilter],
    queryFn: async () => {
      let query = "/audits?page=1&size=50";
      if (deptFilter) query += `&department_id=${deptFilter}`;
      if (statusFilter) query += `&status=${statusFilter}`;
      if (riskFilter) query += `&risk_level=${riskFilter}`;
      const res = await axiosInstance.get(query);
      return res.data;
    },
    enabled: activeTab === "audits",
  });

  // Fetch Daily Rounds List
  const { data: roundsList, isLoading: roundsLoading } = useQuery({
    queryKey: ["dailyRoundsReport"],
    queryFn: async () => {
      const res = await axiosInstance.get("/daily-rounds?skip=0&limit=100");
      return res.data;
    },
    enabled: activeTab === "rounds",
  });

  // Programmatic authenticated Excel download for scheduled audits
  const handleExportExcel = async () => {
    setExporting(true);
    try {
      let query = "/audits/export/excel?";
      if (deptFilter) query += `department_id=${deptFilter}&`;
      if (statusFilter) query += `status=${statusFilter}&`;
      if (riskFilter) query += `risk_level=${riskFilter}&`;

      const res = await axiosInstance.get(query, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Infection_Audits_Report.xlsx");
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Excel download failed", err);
    } finally {
      setExporting(false);
    }
  };

  // Programmatic authenticated Excel download for daily rounds
  const handleExportRoundsExcel = async () => {
    setExporting(true);
    try {
      const res = await axiosInstance.get("/daily-rounds/export/excel", {
        responseType: "blob",
      });
      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Daily_Rounds_Walk_Report.xlsx");
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Rounds Excel download failed", err);
    } finally {
      setExporting(false);
    }
  };

  // Programmatic authenticated PDF download
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
      console.error("PDF download failed", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Reports & Exports</h1>
          <p className="text-sm text-text-secondary">
            Compile historical logs, generate Excel summaries, and download PDF sheets.
          </p>
        </div>
        <button
          onClick={activeTab === "audits" ? handleExportExcel : handleExportRoundsExcel}
          disabled={exporting}
          className="flex items-center gap-2 rounded-md bg-secondary hover:bg-opacity-90 py-2 px-4 text-sm font-semibold text-white shadow-sm cursor-pointer disabled:opacity-50 transition-all"
        >
          {exporting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Compiling...
            </>
          ) : (
            <>
              <FileSpreadsheet className="h-4 w-4" />
              Export {activeTab === "audits" ? "Audit Sheets" : "Rounds Sheet"}
            </>
          )}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border pb-px">
        <button
          onClick={() => setActiveTab("audits")}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "audits"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          Infection Scheduled Audits
        </button>
        <button
          onClick={() => setActiveTab("rounds")}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer ${
            activeTab === "rounds"
              ? "border-primary text-primary"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          🏥 Smart Daily Rounds
        </button>
      </div>

      {activeTab === "audits" ? (
        <>
          {/* Filter Bar */}
          <div className="card-notion flex flex-wrap gap-4 items-center p-4 bg-slate-50 border border-border">
            <div className="flex items-center gap-2 text-xs font-bold text-text-secondary uppercase">
              <Filter className="h-4 w-4" />
              Filter Logs
            </div>

            {/* Dept Selector */}
            <select
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="input-notion py-1 focus:border-primary text-xs w-48"
            >
              <option value="">All Departments</option>
              {departments?.map((d: any) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>

            {/* Status Selector */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-notion py-1 focus:border-primary text-xs w-40"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="REVIEWED">Reviewed</option>
            </select>

            {/* Risk Selector */}
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="input-notion py-1 focus:border-primary text-xs w-40"
            >
              <option value="">All Risks</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>

          {/* Table grid */}
          {auditsLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="card-notion overflow-hidden p-0 border border-border bg-surface">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border text-left">
                  <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                    <tr>
                      <th className="px-6 py-3">Audit Topic</th>
                      <th className="px-6 py-3">Department</th>
                      <th className="px-6 py-3">Risk Category</th>
                      <th className="px-6 py-3">Score</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3 text-right">Download</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-sm">
                    {auditsPayload?.items.map((audit: any) => {
                      let badge = "bg-green-50 text-success border-green-200";
                      if (audit.compliance_percentage < 75)
                        badge = "bg-red-50 text-danger border-red-200";
                      else if (audit.compliance_percentage < 90)
                        badge = "bg-amber-50 text-warning border-amber-200";

                      let riskColor = "text-text-secondary";
                      if (audit.risk_level === "CRITICAL" || audit.risk_level === "HIGH")
                        riskColor = "text-danger font-semibold";

                      return (
                        <tr key={audit.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 font-bold text-text-primary">
                            {audit.template_title}
                          </td>
                          <td className="px-6 py-4 text-text-primary">
                            {audit.department_name}
                          </td>
                          <td className={`px-6 py-4 flex items-center gap-1 text-xs ${riskColor}`}>
                            {(audit.risk_level === "CRITICAL" || audit.risk_level === "HIGH") && (
                              <AlertOctagon className="h-3.5 w-3.5" />
                            )}
                            {audit.risk_level}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`rounded-full border px-2 py-0.5 text-xs font-bold ${badge}`}>
                              {audit.compliance_percentage}%
                            </span>
                          </td>
                          <td className="px-6 py-4 text-xs font-semibold text-text-secondary">
                            {audit.status}
                          </td>
                          <td className="px-6 py-4 text-right">
                            {audit.status === "SUBMITTED" ? (
                              <button
                                onClick={() => handleDownloadPDF(audit.id)}
                                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-text-primary border border-border rounded hover:bg-hover cursor-pointer transition-all"
                              >
                                <FileDown className="h-3.5 w-3.5 text-text-secondary" />
                                PDF Sheet
                              </button>
                            ) : (
                              <span className="text-xs text-text-secondary italic">Drafting</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}

                    {auditsPayload?.items.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-10 text-text-secondary text-sm">
                          No matching records found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        /* Daily Rounds Reports */
        <>
          {roundsLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="card-notion overflow-hidden p-0 border border-border bg-surface">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border text-left">
                  <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                    <tr>
                      <th className="px-6 py-3">Hospital / Facility</th>
                      <th className="px-6 py-3">Building Block</th>
                      <th className="px-6 py-3">Shift / Shift Type</th>
                      <th className="px-6 py-3">Started Date</th>
                      <th className="px-6 py-3">Gaps Found</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3 text-right">Workspace</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border text-sm">
                    {roundsList?.map((r: any) => {
                      const isComplete = r.status === "COMPLETED";
                      const gapCount = r.observations?.length || 0;

                      return (
                        <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="px-6 py-4 font-bold text-text-primary">
                            {r.hospital}
                          </td>
                          <td className="px-6 py-4 text-text-primary">
                            {r.building} {r.floor ? `(Floor ${r.floor})` : "(Layout)"}
                          </td>
                          <td className="px-6 py-4 text-xs font-semibold uppercase tracking-wider text-text-secondary">
                            {r.round_type}
                          </td>
                          <td className="px-6 py-4 text-text-secondary">
                            {new Date(r.started_at).toLocaleDateString()} {new Date(r.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${
                              gapCount > 0
                                ? "bg-red-50 text-danger border-red-100"
                                : "bg-emerald-50 text-success border-emerald-100"
                            }`}>
                              {gapCount} Gaps
                            </span>
                          </td>
                          <td className="px-6 py-4 text-xs font-bold">
                            {isComplete ? (
                              <span className="text-success uppercase">Sealed</span>
                            ) : (
                              <span className="text-warning uppercase animate-pulse">Walking</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => router.push(`/dashboard/daily-rounds/${r.id}`)}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-primary border border-primary/20 rounded hover:bg-primary/5 cursor-pointer transition-all"
                            >
                              <Eye className="h-3.5 w-3.5" />
                              View Round
                            </button>
                          </td>
                        </tr>
                      );
                    })}

                    {roundsList?.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-10 text-text-secondary text-sm">
                          No daily round logs recorded.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
