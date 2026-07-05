"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../../lib/axios";
import {
  Loader2,
  ChevronLeft,
  Camera,
  CheckCircle,
  FileCheck,
  AlertTriangle,
  Upload,
} from "lucide-react";
import Link from "next/link";

export default function AuditExecutionPage() {
  const { id: auditId } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<string>("");
  const [remarksInput, setRemarksInput] = useState<Record<string, string>>({});
  const [uploadingResponseId, setUploadingResponseId] = useState<string | null>(null);

  // Query audit details
  const { data: audit, isLoading, error } = useQuery({
    queryKey: ["auditDetails", auditId],
    queryFn: async () => {
      const res = await axiosInstance.get(`/audits/${auditId}`);
      return res.data;
    },
  });

  // Sync state using useEffect on data fetch
  React.useEffect(() => {
    if (audit) {
      // Set first group tab as active by default
      if (audit.groups && audit.groups.length > 0 && !activeTab) {
        setActiveTab(audit.groups[0].group_id);
      }
      // Populate remarks state
      const initialRemarks: Record<string, string> = {};
      audit.groups?.forEach((g: any) => {
        g.questions.forEach((q: any) => {
          initialRemarks[q.question_id] = q.remarks || "";
        });
      });
      setRemarksInput((prev) => ({ ...initialRemarks, ...prev }));
    }
  }, [audit, activeTab]);

  // Mutation to save draft responses
  const saveResponsesMutation = useMutation({
    mutationFn: async (payload: { question_id: string; answer: string; remarks?: string }[]) => {
      const res = await axiosInstance.put(`/audits/${auditId}/responses`, {
        responses: payload,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auditDetails", auditId] });
    },
  });

  // Mutation to submit the audit
  const submitAuditMutation = useMutation({
    mutationFn: async () => {
      const res = await axiosInstance.post(`/audits/${auditId}/submit`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auditDetails", auditId] });
      queryClient.invalidateQueries({ queryKey: ["audits"] });
    },
  });

  const handleResponseChange = (questionId: string, answer: string) => {
    if (audit.status !== "DRAFT") return;
    const currentRemarks = remarksInput[questionId] || "";
    saveResponsesMutation.mutate([
      {
        question_id: questionId,
        answer,
        remarks: currentRemarks,
      },
    ]);
  };

  const handleRemarksBlur = (questionId: string, answer: string) => {
    if (audit.status !== "DRAFT") return;
    const currentRemarks = remarksInput[questionId] || "";
    saveResponsesMutation.mutate([
      {
        question_id: questionId,
        answer,
        remarks: currentRemarks,
      },
    ]);
  };

  const handleFileUpload = async (questionId: string, responseId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (audit.status !== "DRAFT") return;
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    setUploadingResponseId(responseId);
    const file = files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      await axiosInstance.post(
        `/audits/${auditId}/media?response_id=${responseId}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      queryClient.invalidateQueries({ queryKey: ["auditDetails", auditId] });
    } catch (err) {
      console.error("File upload failed", err);
    } finally {
      setUploadingResponseId(null);
    }
  };

  const handleSubmitAudit = () => {
    if (confirm("Are you sure you want to submit this audit? This will lock all scores and generate corrective action tickets.")) {
      submitAuditMutation.mutate();
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !audit) {
    return (
      <div className="text-center py-12">
        <p className="text-danger font-medium">Failed to load audit sheet.</p>
        <Link href="/dashboard/audits" className="text-primary hover:underline mt-2 inline-block">
          Go back to Audits
        </Link>
      </div>
    );
  }

  const activeGroup = audit.groups?.find((g: any) => g.group_id === activeTab) || audit.groups?.[0];

  return (
    <div className="space-y-6">
      {/* Breadcrumb Header */}
      <div className="flex items-center gap-2">
        <Link href="/dashboard/audits" className="rounded p-1.5 text-text-secondary hover:bg-hover">
          <ChevronLeft className="h-5 w-5" />
        </Link>
        <div>
          <span className="text-[10px] font-bold text-text-secondary uppercase tracking-wider">
            Audit Checklist Execution
          </span>
          <h1 className="text-lg font-bold text-text-primary">
            {audit.template_title}
          </h1>
        </div>
      </div>

      {/* Audit Rollup Info */}
      <div className="card-notion grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-slate-50">
        <div>
          <span className="text-[10px] font-bold text-text-secondary uppercase">Department</span>
          <p className="text-xs font-bold text-text-primary mt-0.5">{audit.department_name}</p>
        </div>
        <div>
          <span className="text-[10px] font-bold text-text-secondary uppercase">Status</span>
          <p className="text-xs font-bold text-text-primary mt-0.5 uppercase tracking-wide">
            {audit.status}
          </p>
        </div>
        <div>
          <span className="text-[10px] font-bold text-text-secondary uppercase">Current Score</span>
          <p className="text-xs font-bold text-text-primary mt-0.5">{audit.compliance_percentage}%</p>
        </div>
        <div>
          <span className="text-[10px] font-bold text-text-secondary uppercase">Risk Assessment</span>
          <p className="text-xs font-bold text-text-primary mt-0.5 uppercase">{audit.risk_level}</p>
        </div>
      </div>

      {/* Section Tab Bar */}
      <div className="flex border-b border-border overflow-x-auto gap-2">
        {audit.groups?.map((g: any) => (
          <button
            key={g.group_id}
            onClick={() => setActiveTab(g.group_id)}
            className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap cursor-pointer border-b-2 transition-all ${
              activeTab === g.group_id || (!activeTab && audit.groups[0].group_id === g.group_id)
                ? "border-primary text-primary font-bold"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            {g.title}
          </button>
        ))}
      </div>

      {/* Questions Form Sheet */}
      {activeGroup && (
        <div className="card-notion space-y-8">
          <div className="divide-y divide-border">
            {activeGroup.questions.map((q: any) => {
              // Locate corresponding response
              const isUnanswered = !q.answer || q.answer === "N/A";
              
              return (
                <div key={q.question_id} className="py-6 first:pt-0 last:pb-0 space-y-4">
                  {/* Question Text */}
                  <div className="flex justify-between items-start gap-4">
                    <p className="text-sm font-semibold text-text-primary">
                      {q.text}
                    </p>
                    <span className="text-[10px] font-bold text-text-secondary bg-slate-100 rounded px-1.5 py-0.5 shrink-0">
                      Wt: {q.compliance_weight}
                    </span>
                  </div>

                  {/* Input Controls */}
                  <div className="flex flex-wrap gap-4 items-center">
                    {/* Yes/No/NA Radio Controls */}
                    <div className="flex items-center gap-2 border border-border rounded-md p-1 bg-slate-50">
                      {["Yes", "No", "N/A"].map((opt) => {
                        const isChecked = q.answer?.toUpperCase() === opt.toUpperCase() || 
                                          (opt === "N/A" && isUnanswered);
                        return (
                          <button
                            key={opt}
                            type="button"
                            disabled={audit.status !== "DRAFT"}
                            onClick={() => handleResponseChange(q.question_id, opt)}
                            className={`px-3 py-1.5 text-xs font-bold rounded cursor-pointer transition-colors ${
                              isChecked
                                ? opt === "Yes"
                                  ? "bg-success text-white"
                                  : opt === "No"
                                    ? "bg-danger text-white"
                                    : "bg-slate-300 text-text-primary"
                                : "text-text-secondary hover:bg-hover"
                            }`}
                          >
                            {opt}
                          </button>
                        );
                      })}
                    </div>

                    {/* Remarks Input */}
                    <div className="flex-1 min-w-[200px]">
                      <input
                        type="text"
                        disabled={audit.status !== "DRAFT"}
                        value={remarksInput[q.question_id] || ""}
                        onChange={(e) =>
                          setRemarksInput({
                            ...remarksInput,
                            [q.question_id]: e.target.value,
                          })
                        }
                        onBlur={() => handleRemarksBlur(q.question_id, q.answer || "N/A")}
                        placeholder="Add auditor remarks..."
                        className="input-notion w-full py-1.5 focus:border-primary text-xs"
                      />
                    </div>

                    {/* Image Upload Trigger */}
                    {audit.status === "DRAFT" && (
                      <div className="relative shrink-0">
                        <input
                          type="file"
                          accept="image/*"
                          id={`upload-${q.question_id}`}
                          className="hidden"
                          onChange={(e) => handleFileUpload(q.question_id, q.response_id, e)}
                        />
                        <label
                          htmlFor={`upload-${q.question_id}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-md text-xs font-semibold text-text-primary bg-slate-50 hover:bg-hover cursor-pointer"
                        >
                          {uploadingResponseId === q.response_id ? (
                            <>
                              <Loader2 className="h-3.5 w-3.5 animate-spin text-text-secondary" />
                              Uploading...
                            </>
                          ) : (
                            <>
                              <Camera className="h-3.5 w-3.5 text-text-secondary" />
                              Upload
                            </>
                          )}
                        </label>
                      </div>
                    )}
                  </div>

                  {/* Render Uploaded Media Thumbnails */}
                  {q.media && q.media.length > 0 && (
                    <div className="flex gap-2 flex-wrap pt-2">
                      {q.media.map((med: any) => (
                        <div key={med.id} className="relative h-14 w-14 border border-border rounded overflow-hidden bg-slate-100">
                          <img
                            src={med.thumbnail_url || med.original_url}
                            alt="audit evidence"
                            className="object-cover h-full w-full"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Form Actions Footer */}
          {audit.status === "DRAFT" && (
            <div className="flex justify-end gap-3 pt-6 border-t border-border mt-8">
              <button
                type="button"
                onClick={handleSubmitAudit}
                disabled={submitAuditMutation.isPending}
                className="flex items-center gap-1.5 px-6 py-2.5 bg-primary text-white rounded-md hover:bg-secondary font-bold text-xs cursor-pointer shadow-sm disabled:opacity-50"
              >
                <FileCheck className="h-4 w-4" />
                {submitAuditMutation.isPending ? "Submitting..." : "Submit Audit Checklist"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
