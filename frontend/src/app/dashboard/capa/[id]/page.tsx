"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../../lib/axios";
import { useAuth } from "../../../../context/AuthContext";
import {
  Loader2,
  ChevronLeft,
  Calendar,
  User,
  AlertTriangle,
  Upload,
  CheckCircle,
  FileCheck,
  Zap,
} from "lucide-react";
import Link from "next/link";

export default function CapaDetailsPage() {
  const { id: capaId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, hasPermission } = useAuth();

  // Form states
  const [rca, setRca] = useState("");
  const [corrective, setCorrective] = useState("");
  const [preventive, setPreventive] = useState("");
  const [uploading, setUploading] = useState(false);

  // Query CAPA details
  const { data: capa, isLoading, error } = useQuery({
    queryKey: ["capaDetails", capaId],
    queryFn: async () => {
      const res = await axiosInstance.get(`/capas/${capaId}`);
      return res.data;
    },
  });

  // Sync state using useEffect on data fetch
  React.useEffect(() => {
    if (capa) {
      setRca(capa.root_cause_analysis || "");
      setCorrective(capa.corrective_action || "");
      setPreventive(capa.preventive_action || "");
    }
  }, [capa]);

  // Save changes Mutation
  const saveMutation = useMutation({
    mutationFn: async (payload: { root_cause_analysis: string; corrective_action: string; preventive_action: string; status?: string }) => {
      const res = await axiosInstance.put(`/capas/${capaId}`, payload);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["capaDetails", capaId] });
      queryClient.invalidateQueries({ queryKey: ["capas"] });
      alert(data.status === "CLOSED" ? "CAPA resolved and closed successfully." : "CAPA draft plan saved successfully.");
    },
  });

  // Approve Closure Mutation
  const approveMutation = useMutation({
    mutationFn: async () => {
      const res = await axiosInstance.post(`/capas/${capaId}/approve`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["capaDetails", capaId] });
      queryClient.invalidateQueries({ queryKey: ["capas"] });
      alert("CAPA approved and closed.");
    },
  });

  const handleSave = (statusOverride?: string) => {
    saveMutation.mutate({
      root_cause_analysis: rca,
      corrective_action: corrective,
      preventive_action: preventive,
      status: statusOverride || capa.status,
    });
  };

  const handleOpenTicket = () => {
    handleSave("OPEN");
  };

  const handlePrefill = () => {
    const prefillRca = `Immediate cause: Non-conformance/deviation identified in the work area.\nRoot cause: Supply/operational gap, lack of standardized supervision checklists, or need for staff training refresher.`;
    const prefillCorrective = `Immediate corrective action: Corrected the immediate issue. Cleaned/sanitized/replenished items, replaced faulty equipment, and re-allocated necessary supplies immediately.`;
    const prefillPreventive = `Long-term preventive plan: Established weekly compliance checks and audits, conducted a staff briefing session, and assigned ownership to the department supervisor.`;
    
    setRca(prefillRca);
    setCorrective(prefillCorrective);
    setPreventive(prefillPreventive);
  };

  const handleDownloadPDF = async () => {
    try {
      const res = await axiosInstance.get(`/capas/${capaId}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `CAPA_Plan_${capaId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed", err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    
    const file = files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      await axiosInstance.post(`/capas/${capaId}/evidence`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      queryClient.invalidateQueries({ queryKey: ["capaDetails", capaId] });
    } catch (err) {
      console.error("Evidence upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  const handleApprove = () => {
    if (confirm("Are you sure you want to approve this corrective action and close the ticket?")) {
      approveMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !capa) {
    return (
      <div className="text-center py-12">
        <p className="text-danger font-medium">Failed to load CAPA details.</p>
        <Link href="/dashboard/capa" className="text-primary hover:underline mt-2 inline-block">
          Go back to CAPA Board
        </Link>
      </div>
    );
  }

  const isClosed = capa.status === "CLOSED";
  const canApprove = hasPermission("capa", "approve") && !isClosed;

  return (
    <div className="space-y-6">
      {/* Breadcrumb & PDF Actions Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-2">
          <Link href="/dashboard/capa" className="rounded p-1.5 text-text-secondary hover:bg-hover">
            <ChevronLeft className="h-5 w-5" />
          </Link>
          <div>
            <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              Corrective Action Plan
            </span>
            <h1 className="text-lg font-bold text-text-primary">
              {capa.title}
            </h1>
          </div>
        </div>

        <button
          onClick={handleDownloadPDF}
          className="flex items-center gap-1.5 px-3.5 py-2 border border-border text-xs font-bold text-text-primary rounded hover:bg-hover bg-slate-50 cursor-pointer transition-all shadow-sm shrink-0"
        >
          <FileCheck className="h-4 w-4 text-text-secondary" />
          Download PDF Plan
        </button>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left Columns: Forms */}
        <div className="lg:col-span-2 space-y-6">
          {/* Defect Description */}
          <div className="card-notion">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Non-Conformance Details
            </h3>
            <p className="text-sm text-text-primary pt-3 whitespace-pre-line leading-relaxed">
              {capa.description}
            </p>
          </div>

          {/* Action Resolution Form */}
          <div className="card-notion space-y-4">
            <div className="flex justify-between items-center border-b border-border pb-3">
              <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                Root Cause & Action Plan (CAPA)
              </h3>
              {!isClosed && (
                <button
                  type="button"
                  onClick={handlePrefill}
                  className="flex items-center gap-1 text-[10px] font-bold text-primary border border-primary/20 bg-blue-50/10 px-2 py-1 rounded hover:bg-blue-50/30 cursor-pointer"
                >
                  <Zap className="h-3 w-3" />
                  Auto-fill standard plan
                </button>
              )}
            </div>
            
            {/* RCA */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary">
                Root Cause Analysis (RCA)
              </label>
              <textarea
                disabled={isClosed}
                rows={3}
                value={rca}
                onChange={(e) => setRca(e.target.value)}
                placeholder="Analyze why the hand hygiene sink failed / soap was missing / etc."
                className="input-notion w-full p-2 focus:border-primary text-xs"
              />
            </div>

            {/* Corrective Action */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary">
                Corrective Action (Immediate Fix)
              </label>
              <textarea
                disabled={isClosed}
                rows={3}
                value={corrective}
                onChange={(e) => setCorrective(e.target.value)}
                placeholder="Immediate correction done: Soap dispenser replaced."
                className="input-notion w-full p-2 focus:border-primary text-xs"
              />
            </div>

            {/* Preventive Action */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary">
                Preventive Action (Long-term Prevention)
              </label>
              <textarea
                disabled={isClosed}
                rows={3}
                value={preventive}
                onChange={(e) => setPreventive(e.target.value)}
                placeholder="Preventive checks: Added weekly stock registers."
                className="input-notion w-full p-2 focus:border-primary text-xs"
              />
            </div>

            {/* Submit Action Block */}
            {!isClosed && (
              <div className="flex flex-wrap justify-between items-center gap-3 pt-3 border-t border-border mt-6">
                <div className="flex gap-2">
                  {capa.status === "PENDING" && (
                    <button
                      type="button"
                      onClick={handleOpenTicket}
                      className="px-4 py-2 text-xs font-semibold bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer"
                    >
                      Mark as In Progress
                    </button>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleSave()}
                    disabled={saveMutation.isPending}
                    className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover bg-slate-50 text-text-primary cursor-pointer disabled:opacity-50"
                  >
                    {saveMutation.isPending ? "Saving..." : "Save Draft Plan"}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSave("CLOSED")}
                    disabled={saveMutation.isPending}
                    className="px-4 py-2 text-xs font-bold bg-green-600 text-white rounded-md hover:bg-green-700 cursor-pointer disabled:opacity-50"
                  >
                    {saveMutation.isPending ? "Closing..." : "Resolve & Close CAPA"}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Evidence Uploads */}
          <div className="card-notion space-y-4">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Resolution Proof (Evidence)
            </h3>
            
            {/* Evidence List */}
            {capa.evidence && capa.evidence.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {capa.evidence.map((ev: any) => (
                  <div key={ev.id} className="relative group border border-border rounded overflow-hidden bg-slate-50">
                    <img
                      src={ev.file_url}
                      alt="capa resolution evidence"
                      className="object-cover h-32 w-full"
                    />
                    <div className="p-2 text-[10px] text-text-secondary">
                      Uploaded: {new Date(ev.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-text-secondary">No evidence uploaded yet.</p>
            )}

            {/* Upload Button */}
            {!isClosed && (
              <div className="pt-3 border-t border-border/60">
                <input
                  type="file"
                  accept="image/*"
                  id="evidence-file"
                  className="hidden"
                  onChange={handleFileUpload}
                />
                <label
                  htmlFor="evidence-file"
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-border rounded-md text-xs font-semibold text-text-primary bg-slate-50 hover:bg-hover cursor-pointer"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-text-secondary" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 text-text-secondary" />
                      Upload Evidence Image
                    </>
                  )}
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Sidebar Specs */}
        <div className="space-y-6">
          <div className="card-notion space-y-4">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Ticket Details
            </h3>

            <div className="space-y-3 pt-2">
              <div>
                <span className="text-[10px] font-bold text-text-secondary uppercase">Status</span>
                <p className="text-xs font-bold text-text-primary uppercase mt-0.5">{capa.status}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-text-secondary uppercase">Priority</span>
                <p className="text-xs font-bold text-text-primary uppercase mt-0.5">{capa.priority}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-text-secondary uppercase">Assigned To</span>
                <p className="text-xs font-bold text-text-primary mt-0.5">{capa.assigned_name}</p>
              </div>
              <div>
                <span className="text-[10px] font-bold text-text-secondary uppercase">Target Deadline</span>
                <p className="text-xs font-bold text-text-primary mt-0.5">
                  {new Date(capa.deadline).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Approval Workflow Block */}
            {canApprove && (
              <div className="pt-4 border-t border-border mt-6">
                <button
                  type="button"
                  onClick={handleApprove}
                  className="flex w-full items-center justify-center gap-1.5 px-4 py-2.5 bg-success text-white rounded-md hover:bg-success/90 font-bold text-xs cursor-pointer shadow-sm"
                >
                  <CheckCircle className="h-4 w-4" />
                  Approve & Close CAPA
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
