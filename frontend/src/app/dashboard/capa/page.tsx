"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import Link from "next/link";
import {
  AlertTriangle,
  Clock,
  User,
  Plus,
  Loader2,
  ChevronRight,
  Filter,
} from "lucide-react";

export default function CapaBoardPage() {
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [selectedPriority, setSelectedPriority] = useState<string>("");

  // Query CAPAs
  const { data: capaPayload, isLoading } = useQuery({
    queryKey: ["capas", selectedDept, selectedPriority],
    queryFn: async () => {
      let url = "/capas?page=1&size=100";
      if (selectedDept) url += `&department_id=${selectedDept}`;
      if (selectedPriority) url += `&priority=${selectedPriority}`;
      const res = await axiosInstance.get(url);
      return res.data;
    },
  });

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits/admin/departments");
      return res.data;
    },
  });

  const columns = [
    { id: "PENDING", title: "Pending", bg: "bg-slate-100/50" },
    { id: "OPEN", title: "Open / In Progress", bg: "bg-blue-50/20" },
    { id: "CLOSED", title: "Closed / Resolved", bg: "bg-green-50/20" },
  ];

  const capas = capaPayload?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Corrective Actions (CAPA)</h1>
          <p className="text-sm text-text-secondary">
            Manage non-conformances, assign tasks, and track resolutions.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card-notion flex flex-wrap gap-4 items-center p-4 bg-slate-50">
        <div className="flex items-center gap-2 text-xs font-bold text-text-secondary uppercase">
          <Filter className="h-4 w-4" />
          Filters
        </div>

        {/* Dept Filter */}
        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="input-notion py-1 focus:border-primary text-xs w-48"
        >
          <option value="">All Departments</option>
          {departments?.map((d: any) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>

        {/* Priority Filter */}
        <select
          value={selectedPriority}
          onChange={(e) => setSelectedPriority(e.target.value)}
          className="input-notion py-1 focus:border-primary text-xs w-40"
        >
          <option value="">All Priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>

      {/* Kanban Columns */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {columns.map((col) => {
            const filteredCapas = capas.filter((c: any) => c.status === col.id);
            return (
              <div key={col.id} className={`rounded-xl border border-border p-4 ${col.bg} flex flex-col min-h-[500px]`}>
                <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
                  <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
                    {col.title}
                  </h3>
                  <span className="rounded-full bg-slate-200/60 px-2 py-0.5 text-xs font-bold text-text-secondary">
                    {filteredCapas.length}
                  </span>
                </div>

                <div className="flex-1 space-y-4 overflow-y-auto max-h-[600px] pr-1">
                  {filteredCapas.map((capa: any) => {
                    const dateStr = new Date(capa.deadline).toLocaleDateString();
                    let prioBadge = "bg-slate-100 text-text-secondary border-slate-200";
                    if (capa.priority === "HIGH") prioBadge = "bg-red-50 text-danger border-red-200";
                    else if (capa.priority === "CRITICAL") prioBadge = "bg-red-100 text-danger border-red-300 animate-pulse";
                    else if (capa.priority === "MEDIUM") prioBadge = "bg-amber-50 text-warning border-amber-200";

                    return (
                      <div key={capa.id} className="card-notion p-4 hover:shadow-md transition-shadow bg-surface border border-border">
                        <div className="flex items-start justify-between gap-3">
                          <Link
                            href={`/dashboard/capa/${capa.id}`}
                            className="text-xs font-bold text-text-primary hover:text-primary leading-tight line-clamp-2"
                          >
                            {capa.title}
                          </Link>
                        </div>
                        
                        <p className="text-[11px] text-text-secondary mt-1.5 font-medium">
                          {capa.department_name}
                        </p>
                        
                        <div className="flex items-center justify-between mt-4 pt-3 border-t border-border/60">
                          {/* Deadline */}
                          <span className="flex items-center gap-1 text-[10px] text-text-secondary">
                            <Clock className="h-3 w-3" />
                            {dateStr}
                          </span>
                          
                          {/* Priority badge */}
                          <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold ${prioBadge}`}>
                            {capa.priority}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  {filteredCapas.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-48 border border-dashed border-border rounded-lg text-text-secondary text-xs bg-slate-50/20">
                      No tickets in this section
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
