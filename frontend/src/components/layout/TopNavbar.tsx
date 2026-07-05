"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../../context/AuthContext";
import { Menu, Bell, Search, LogOut, User, Activity, Sun, Moon, Check, MailOpen } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../lib/axios";

interface TopNavbarProps {
  onMenuClick: () => void;
}

export default function TopNavbar({ onMenuClick }: TopNavbarProps) {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Fetch Notifications
  const { data: notifications } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const res = await axiosInstance.get("/users/me/notifications");
      return res.data;
    },
    refetchInterval: 10000, // poll every 10 seconds for real-time alerts
    enabled: !!user,
  });

  // Mark Read mutation
  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await axiosInstance.post(`/users/me/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const handleMarkAllRead = () => {
    const unread = notifications?.filter((n: any) => !n.is_read) || [];
    unread.forEach((n: any) => {
      markReadMutation.mutate(n.id);
    });
  };

  const unreadCount = notifications?.filter((n: any) => !n.is_read).length || 0;

  useEffect(() => {
    if (typeof window !== "undefined") {
      const isDark = document.documentElement.classList.contains("dark");
      setTheme(isDark ? "dark" : "light");
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("theme", nextTheme);
    if (nextTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-surface px-4 md:px-8">
      {/* Mobile Menu & Hospital Name */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="rounded p-2 text-text-secondary hover:bg-hover md:hidden"
        >
          <Menu className="h-6 w-6" />
        </button>
        
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-secondary" />
          <span className="font-bold text-text-primary hidden sm:inline-block">
            City General Hospital
          </span>
          <span className="text-xs text-text-secondary border-l border-border pl-2 hidden md:inline-block">
            Infection Quality Desk
          </span>
        </div>
      </div>

      {/* Search and Action Items */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative max-w-xs hidden md:block">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-text-secondary" />
          </div>
          <input
            type="search"
            placeholder="Search audits..."
            className="input-notion w-60 pl-9 pr-4 py-1.5 focus:border-primary"
          />
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="rounded p-2 text-text-secondary hover:bg-hover cursor-pointer"
          title="Toggle Light/Dark Mode"
        >
          {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative rounded p-2 text-text-secondary hover:bg-hover cursor-pointer"
            title="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[9px] font-bold text-white px-0.5">
                {unreadCount}
              </span>
            )}
          </button>

          {notificationsOpen && (
            <>
              <div
                onClick={() => setNotificationsOpen(false)}
                className="fixed inset-0 z-30"
              />
              <div className="absolute right-0 mt-2 z-40 w-80 origin-top-right rounded-md border border-border bg-surface py-2 shadow-lg text-left">
                <div className="flex items-center justify-between px-4 py-2 border-b border-border text-xs font-bold">
                  <span className="text-text-primary">Alerts & Safety Reports ({unreadCount})</span>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-primary hover:underline cursor-pointer flex items-center gap-0.5"
                    >
                      <MailOpen className="h-3 w-3" />
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-64 overflow-y-auto divide-y divide-border">
                  {notifications?.slice(0, 5).map((n: any) => (
                    <div
                      key={n.id}
                      className={`px-4 py-2.5 text-xs hover:bg-hover transition-colors relative flex gap-2.5 items-start ${
                        !n.is_read ? "bg-blue-50/15" : ""
                      }`}
                    >
                      {!n.is_read && (
                        <span className="h-1.5 w-1.5 rounded-full bg-secondary shrink-0 mt-1.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <span className={`font-bold truncate ${!n.is_read ? "text-text-primary" : "text-text-secondary"}`}>
                            {n.title}
                          </span>
                          <span className="text-[9px] text-text-secondary shrink-0">
                            {new Date(n.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-text-secondary mt-0.5 text-[11px] leading-relaxed whitespace-pre-wrap">
                          {n.message}
                        </p>
                      </div>
                      {!n.is_read && (
                        <button
                          onClick={() => markReadMutation.mutate(n.id)}
                          className="shrink-0 p-0.5 rounded border border-border hover:bg-hover text-text-secondary hover:text-success cursor-pointer"
                          title="Mark read"
                        >
                          <Check className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  ))}

                  {(!notifications || notifications.length === 0) && (
                    <div className="py-8 text-center text-text-secondary italic text-xs">
                      No notifications logged.
                    </div>
                  )}
                </div>
                <div className="border-t border-border px-4 pt-2 text-center text-xs">
                  <Link
                    href="/dashboard/notifications"
                    onClick={() => setNotificationsOpen(false)}
                    className="text-primary hover:underline font-bold"
                  >
                    View all notifications
                  </Link>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 rounded-full border border-border p-1 hover:bg-hover"
          >
            <div className="h-7 w-7 rounded-full bg-secondary text-white flex items-center justify-center font-bold text-xs uppercase">
              {user?.full_name?.charAt(0) || "U"}
            </div>
          </button>

          {profileOpen && (
            <>
              <div
                onClick={() => setProfileOpen(false)}
                className="fixed inset-0 z-30"
              />
              <div className="absolute right-0 mt-2 z-40 w-56 origin-top-right rounded-md border border-border bg-surface py-1 shadow-lg">
                <div className="border-b border-border px-4 py-2 text-xs">
                  <p className="font-semibold text-text-primary">
                    {user?.full_name}
                  </p>
                  <p className="text-text-secondary truncate mt-0.5">
                    {user?.email}
                  </p>
                </div>
                
                <Link
                  href="/dashboard/profile"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-hover"
                >
                  <User className="h-4 w-4 text-text-secondary" />
                  My Profile
                </Link>
                
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    logout();
                  }}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-danger hover:bg-hover text-left"
                >
                  <LogOut className="h-4 w-4 text-danger" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
