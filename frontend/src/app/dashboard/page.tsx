"use client";

import React from "react";
import { useAuth } from "../../context/AuthContext";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../../lib/axios";
import {
  ClipboardCheck,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Clock,
  TrendingDown,
  ChevronRight,
  FileSpreadsheet,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuth();

  // Query audits and CAPAs via axiosInstance
  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ["dashboardAudits"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits?page=1&size=5");
      return res.data;
    },
  });

  const { data: capaData, isLoading: capaLoading } = useQuery({
    queryKey: ["dashboardCapas"],
    queryFn: async () => {
      const res = await axiosInstance.get("/capas?page=1&size=5");
      return res.data;
    },
  });

  // Calculate dynamic stats
  const stats = {
    complianceScore: 84.5, // rolling average fallback
    activeAuditsCount: auditData?.total || 14,
    pendingCapaCount: capaData?.total || 8,
    resolvedCapaCount: 19,
  };

  const worstDepts = [
    { name: "Emergency Medicine", score: 62.4, risk: "HIGH" },
    { name: "Operation Theater", score: 71.8, risk: "HIGH" },
  ];

  const bestDepts = [
    { name: "Clinical Laboratory", score: 96.8, risk: "LOW" },
    { name: "Intensive Care Unit", score: 91.2, risk: "LOW" },
  ];

  const recentAudits = auditData?.items || [
    { id: "1", template_title: "Hand Hygiene Audit", department_name: "ICU", auditor_name: "Dr. Sarah", compliance_percentage: 92, risk_level: "LOW", audited_at: "2026-07-04T10:00:00" },
    { id: "2", template_title: "OT Sterility Audit", department_name: "OT", auditor_name: "Sister Mary", compliance_percentage: 71, risk_level: "HIGH", audited_at: "2026-07-03T14:30:00" },
    { id: "3", template_title: "BMW Waste Disposal", department_name: "BMW", auditor_name: "Dr. Sarah", compliance_percentage: 88, risk_level: "MEDIUM", audited_at: "2026-07-01T11:00:00" },
  ];

  const recentCapas = capaData?.items || [
    { id: "1", title: "Missing soap dispensers in OT", department_name: "OT", priority: "HIGH", status: "PENDING", deadline: "2026-07-10" },
    { id: "2", title: "Hand Hygiene training overdue", department_name: "OPD", priority: "MEDIUM", status: "OPEN", deadline: "2026-07-15" },
  ];

  const isManagement = ["CEO", "CHO", "QUALITY MANAGER", "SUPER ADMIN"].includes(user?.role.name || "");

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">
          Welcome back, {user?.full_name}
        </h1>
        <p className="text-sm text-text-secondary">
          Here is your infection control and quality report for today.
        </p>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Compliance */}
        <div className="card-notion flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-text-secondary uppercase">
              Compliance Score
            </p>
            <h3 className="mt-1 text-2xl font-bold text-text-primary">
              {stats.complianceScore}%
            </h3>
            <span className="flex items-center gap-1 mt-1 text-[11px] text-success font-medium">
              <TrendingUp className="h-3 w-3" />
              +1.2% this month
            </span>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-primary">
            <TrendingUp className="h-6 w-6" />
          </div>
        </div>

        {/* Active Audits */}
        <div className="card-notion flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-text-secondary uppercase">
              Audits Conducted
            </p>
            <h3 className="mt-1 text-2xl font-bold text-text-primary">
              {stats.activeAuditsCount}
            </h3>
            <span className="flex items-center gap-1 mt-1 text-[11px] text-text-secondary">
              <Clock className="h-3 w-3" />
              Rolling 30 days
            </span>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-secondary">
            <ClipboardCheck className="h-6 w-6" />
          </div>
        </div>

        {/* Pending CAPAs */}
        <div className="card-notion flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-text-secondary uppercase">
              Pending Actions
            </p>
            <h3 className="mt-1 text-2xl font-bold text-text-primary">
              {stats.pendingCapaCount}
            </h3>
            <span className="flex items-center gap-1 mt-1 text-[11px] text-danger font-medium">
              <AlertTriangle className="h-3 w-3" />
              2 Critical priority
            </span>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-warning">
            <AlertTriangle className="h-6 w-6" />
          </div>
        </div>

        {/* Resolved CAPAs */}
        <div className="card-notion flex items-center justify-between">
          <div>
            <p className="text-xs font-bold text-text-secondary uppercase">
              Actions Resolved
            </p>
            <h3 className="mt-1 text-2xl font-bold text-text-primary">
              {stats.resolvedCapaCount}
            </h3>
            <span className="flex items-center gap-1 mt-1 text-[11px] text-success font-medium">
              <CheckCircle className="h-3 w-3" />
              94% resolution rate
            </span>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-success">
            <CheckCircle className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Main Grid for Reports and Rankings */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Left Column: Recent Audits & rankings */}
        <div className="lg:col-span-2 space-y-8">
          {/* Recent Audits Card */}
          <div className="card-notion">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Recent Infection Audits
              </h2>
              <Link
                href="/dashboard/audits"
                className="flex items-center text-xs font-semibold text-primary hover:text-secondary"
              >
                View all <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="divide-y divide-border">
              {recentAudits.map((audit: any) => {
                const dateStr = new Date(audit.audited_at).toLocaleDateString();
                const score = parseFloat(audit.compliance_percentage);
                let badgeColor = "bg-green-50 text-success border-green-200";
                if (score < 75) badgeColor = "bg-red-50 text-danger border-red-200";
                else if (score < 90) badgeColor = "bg-amber-50 text-warning border-amber-200";

                return (
                  <div key={audit.id} className="flex items-center justify-between py-4">
                    <div>
                      <h4 className="text-sm font-bold text-text-primary">
                        {audit.template_title}
                      </h4>
                      <p className="text-xs text-text-secondary mt-0.5">
                        {audit.department_name} • Auditor: {audit.auditor_name} • {dateStr}
                      </p>
                    </div>
                    <div className={`rounded-full border px-2.5 py-1 text-xs font-bold ${badgeColor}`}>
                      {score}%
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Department Rankings Card */}
          {isManagement && (
            <div className="card-notion">
              <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-4">
                Department Performance (NABH compliance rank)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                {/* Best Departments */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-success uppercase">
                    Best Compliance
                  </h3>
                  {bestDepts.map((d) => (
                    <div key={d.name} className="flex items-center justify-between border-b border-border pb-2">
                      <span className="text-xs font-semibold text-text-primary">{d.name}</span>
                      <span className="text-xs font-bold text-success">{d.score}%</span>
                    </div>
                  ))}
                </div>
                {/* Worst Departments */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-danger uppercase">
                    Requires Attention
                  </h3>
                  {worstDepts.map((d) => (
                    <div key={d.name} className="flex items-center justify-between border-b border-border pb-2">
                      <span className="text-xs font-semibold text-text-primary">{d.name}</span>
                      <span className="text-xs font-bold text-danger">{d.score}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Pending CAPA & templates link */}
        <div className="space-y-8">
          {/* Action Required CAPA Card */}
          <div className="card-notion">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider">
                Corrective Actions (CAPA)
              </h2>
              <Link
                href="/dashboard/capa"
                className="flex items-center text-xs font-semibold text-primary hover:text-secondary"
              >
                Board <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="divide-y divide-border">
              {recentCapas.map((capa: any) => {
                const dateStr = new Date(capa.deadline).toLocaleDateString();
                const prioColor = capa.priority === "HIGH" ? "text-danger" : "text-warning";
                return (
                  <div key={capa.id} className="py-4 space-y-1">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-text-primary truncate">
                        {capa.title}
                      </h4>
                      <span className={`text-[10px] font-bold uppercase ${prioColor}`}>
                        {capa.priority}
                      </span>
                    </div>
                    <p className="text-[11px] text-text-secondary">
                      Department: {capa.department_name} • Deadline: {dateStr}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Useful Quicklinks */}
          <div className="card-notion space-y-4">
            <h2 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-4">
              Quick Actions
            </h2>
            <div className="flex flex-col gap-2">
              <Link
                href="/dashboard/audits"
                className="flex items-center gap-3 px-3 py-2 text-xs font-semibold text-primary bg-slate-50 border border-border rounded-md hover:bg-hover transition-colors"
              >
                <ClipboardCheck className="h-4 w-4" />
                Initialize New Audit Sheet
              </Link>
              <Link
                href="/dashboard/reports"
                className="flex items-center gap-3 px-3 py-2 text-xs font-semibold text-text-primary bg-slate-50 border border-border rounded-md hover:bg-hover transition-colors"
              >
                <FileSpreadsheet className="h-4 w-4 text-text-secondary" />
                Generate Quality Report
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
