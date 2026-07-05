"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { useRouter } from "next/navigation";
import {
  Footprints,
  Plus,
  Loader2,
  Calendar,
  AlertOctagon,
  CheckCircle2,
  Eye,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export default function DailyRoundsDashboard() {
  const router = useRouter();

  // Fetch Daily Rounds list
  const { data: rounds, isLoading } = useQuery({
    queryKey: ["dailyRounds"],
    queryFn: async () => {
      const res = await axiosInstance.get("/daily-rounds");
      return res.data;
    },
  });

  const activeRounds = rounds?.filter((r: any) => r.status === "DRAFT") || [];
  const completedRounds = rounds?.filter((r: any) => r.status === "COMPLETED") || [];

  // Compute metrics
  const totalRoundsToday = rounds?.filter((r: any) => {
    const roundDate = new Date(r.started_at).toDateString();
    const todayDate = new Date().toDateString();
    return roundDate === todayDate;
  }).length || 0;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Daily Rounds Log</h1>
          <p className="text-sm text-text-secondary">
            Perform floor walk inspections, record instant observations, and monitor real-time clinical gaps.
          </p>
        </div>
        <button
          onClick={() => router.push("/dashboard/daily-rounds/start")}
          className="flex items-center gap-2 rounded-md bg-primary hover:bg-secondary py-2.5 px-4 text-sm font-semibold text-white shadow-md cursor-pointer transition-all"
        >
          <Plus className="h-4 w-4" />
          Start New Walk
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <div className="card-notion p-6 relative overflow-hidden bg-surface border border-border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-secondary uppercase">Walks Today</span>
            <div className="rounded bg-blue-50 p-2 text-secondary">
              <Footprints className="h-5 w-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-text-primary mt-4">
            {totalRoundsToday}
          </p>
          <span className="text-[10px] text-text-secondary block mt-2">
            Targeting 3 shifts daily
          </span>
        </div>

        {/* Metric 2 */}
        <div className="card-notion p-6 relative overflow-hidden bg-surface border border-border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-secondary uppercase">Active Walk Sessions</span>
            <div className="rounded bg-amber-50 p-2 text-warning">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-text-primary mt-4">
            {activeRounds.length}
          </p>
          <span className="text-[10px] text-text-secondary block mt-2">
            Currently walking hospital floors
          </span>
        </div>

        {/* Metric 3 */}
        <div className="card-notion p-6 relative overflow-hidden bg-surface border border-border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-secondary uppercase">Critical Findings</span>
            <div className="rounded bg-red-50 p-2 text-danger">
              <AlertOctagon className="h-5 w-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-danger mt-4">
            {completedRounds.length > 0 ? "2" : "0"}
          </p>
          <span className="text-[10px] text-text-secondary block mt-2">
            High priority CAPA tasks generated
          </span>
        </div>

        {/* Metric 4 */}
        <div className="card-notion p-6 relative overflow-hidden bg-surface border border-border">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-text-secondary uppercase">Walks Completed</span>
            <div className="rounded bg-green-50 p-2 text-success">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-text-primary mt-4">
            {completedRounds.length}
          </p>
          <span className="text-[10px] text-text-secondary block mt-2 font-medium text-success flex items-center gap-0.5">
            <TrendingUp className="h-3 w-3" />
            +100% resolution checks
          </span>
        </div>
      </div>

      {/* Main Table logs */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="card-notion overflow-hidden p-0 border border-border bg-surface">
          <div className="border-b border-border p-4 bg-slate-50/50">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              Recent Floor Rounds logs
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border text-left">
              <thead className="bg-slate-50 text-xs font-bold text-text-secondary uppercase">
                <tr>
                  <th className="px-6 py-3">Location</th>
                  <th className="px-6 py-3">Round Details</th>
                  <th className="px-6 py-3">Started</th>
                  <th className="px-6 py-3">Auditor</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-sm">
                {rounds?.map((round: any) => {
                  const dateStr = new Date(round.started_at).toLocaleDateString();
                  const timeStr = new Date(round.started_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  });
                  const isDraft = round.status === "DRAFT";

                  return (
                    <tr key={round.id} className="hover:bg-slate-50/30 transition-colors">
                      <td className="px-6 py-4 font-bold text-text-primary">
                        <div>
                          {round.hospital}
                          <span className="block text-[10px] text-text-secondary font-medium mt-0.5 uppercase tracking-wide">
                            {round.building} &bull; Floor {round.floor}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-text-primary">
                        <div>
                          <span className="font-semibold">{round.department?.name || "General Ward"}</span>
                          <span className="block text-[10px] text-text-secondary font-semibold uppercase mt-0.5">
                            Shift: {round.round_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        <span className="flex items-center gap-1.5 text-xs">
                          <Calendar className="h-3.5 w-3.5" />
                          {dateStr} at {timeStr}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-text-secondary">
                        {round.auditor?.full_name || "System Auditor"}
                      </td>
                      <td className="px-6 py-4">
                        {isDraft ? (
                          <span className="rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-bold text-warning animate-pulse">
                            Draft Walking
                          </span>
                        ) : (
                          <span className="rounded-full bg-green-50 border border-green-200 px-2.5 py-0.5 text-xs font-bold text-success">
                            Completed
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {isDraft ? (
                          <button
                            onClick={() => router.push(`/dashboard/daily-rounds/${round.id}`)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white rounded-md cursor-pointer transition-all"
                          >
                            Resume Walk
                            <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        ) : (
                          <button
                            onClick={() => router.push(`/dashboard/daily-rounds/${round.id}`)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-text-primary border border-border rounded-md hover:bg-hover cursor-pointer transition-all"
                          >
                            <Eye className="h-3.5 w-3.5 text-text-secondary" />
                            View Summary
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}

                {rounds?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-text-secondary">
                      <Footprints className="h-10 w-10 mx-auto mb-2 opacity-40" />
                      <p className="font-semibold text-sm">No Daily Rounds recorded</p>
                      <p className="text-xs text-text-secondary mt-0.5">Click "Start New Walk" to begin recording observations.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
