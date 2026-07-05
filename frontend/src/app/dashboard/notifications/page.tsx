"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../lib/axios";
import { Bell, Check, Loader2, MailOpen, AlertTriangle } from "lucide-react";

export default function NotificationsPage() {
  const queryClient = useQueryClient();

  // Fetch Notifications
  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await axiosInstance.get("/users/me/notifications");
      return res.data;
    },
  });

  // Mark Read mutation
  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await axiosInstance.post(`/users/me/notifications/${id}/read`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const handleMarkAllRead = async () => {
    const unread = notifications?.filter((n: any) => !n.is_read) || [];
    unread.forEach((n: any) => {
      markReadMutation.mutate(n.id);
    });
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-text-primary">System Notifications</h1>
          <p className="text-sm text-text-secondary">
            In-app quality and critical risk infection control alerts.
          </p>
        </div>
        
        {notifications?.some((n: any) => !n.is_read) && (
          <button
            onClick={handleMarkAllRead}
            className="flex items-center gap-1 text-xs font-semibold text-primary hover:text-secondary bg-slate-50 border border-border rounded-md px-3 py-1.5 cursor-pointer transition-all"
          >
            <MailOpen className="h-3.5 w-3.5" />
            Mark all read
          </button>
        )}
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="space-y-4">
          {notifications?.map((item: any) => {
            const dateStr = new Date(item.created_at).toLocaleString();
            const isUnread = !item.is_read;

            return (
              <div
                key={item.id}
                className={`card-notion p-4 flex gap-4 items-start relative transition-all border border-border ${
                  isUnread ? "bg-blue-50/10 border-blue-100" : "bg-surface"
                }`}
              >
                {/* Unread indicator */}
                {isUnread && (
                  <span className="absolute top-4 left-3 h-2 w-2 rounded-full bg-secondary" />
                )}

                <div className={`p-2 rounded-lg shrink-0 ${isUnread ? "bg-blue-50 text-secondary" : "bg-slate-50 text-text-secondary"}`}>
                  <Bell className="h-5 w-5" />
                </div>

                <div className="flex-1 min-w-0 pl-1">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className={`text-sm font-bold ${isUnread ? "text-text-primary" : "text-text-secondary"}`}>
                      {item.title}
                    </h3>
                    <span className="text-[10px] text-text-secondary shrink-0 whitespace-nowrap pt-0.5">
                      {dateStr}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                    {item.message}
                  </p>
                </div>

                {isUnread && (
                  <button
                    onClick={() => markReadMutation.mutate(item.id)}
                    className="p-1 rounded-md border border-border hover:bg-hover text-text-secondary hover:text-success cursor-pointer transition-colors"
                    title="Mark as read"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                )}
              </div>
            );
          })}

          {notifications?.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-xl bg-slate-50/20 text-text-secondary">
              <Bell className="h-10 w-10 mb-2 opacity-45" />
              <p className="text-sm font-semibold">No alerts found</p>
              <p className="text-xs text-text-secondary mt-0.5">We will notify you when things require attention.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
