"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import {
  LayoutDashboard,
  ClipboardCheck,
  Building2,
  Footprints,
  AlertOctagon,
  FileSpreadsheet,
  BarChart3,
  Bell,
  Users,
  Settings,
  Shield,
} from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export default function Sidebar({ isOpen, setIsOpen }: SidebarProps) {
  const pathname = usePathname();
  const { user, hasPermission } = useAuth();

  const menuItems = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      show: true,
    },
    {
      name: "Audits",
      href: "/dashboard/audits",
      icon: ClipboardCheck,
      show: hasPermission("audits", "read"),
    },
    {
      name: "Departments",
      href: "/dashboard/departments",
      icon: Building2,
      show: hasPermission("departments", "read") || user?.role.name.includes("ADMIN"),
    },
    {
      name: "Daily Rounds",
      href: "/dashboard/daily-rounds",
      icon: Footprints,
      show: hasPermission("audits", "read"),
    },
    {
      name: "CAPA",
      href: "/dashboard/capa",
      icon: AlertOctagon,
      show: hasPermission("capa", "read"),
    },
    {
      name: "Reports",
      href: "/dashboard/reports",
      icon: FileSpreadsheet,
      show: hasPermission("reports", "read"),
    },
    {
      name: "Analytics",
      href: "/dashboard/analytics",
      icon: BarChart3,
      show: true, // everyone has read-only dashboards
    },
    {
      name: "Notifications",
      href: "/dashboard/notifications",
      icon: Bell,
      show: true,
    },
    {
      name: "Users",
      href: "/dashboard/users",
      icon: Users,
      show: hasPermission("users", "read"),
    },
  ];

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-surface border-r border-border transition-transform duration-300 ease-in-out md:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-border">
        <Link href="/dashboard" className="flex items-center gap-2">
          <Shield className="h-6 w-6 text-primary" />
          <span className="text-sm font-bold text-primary tracking-wide uppercase">
            Infection Ctrl
          </span>
        </Link>
        <button
          onClick={() => setIsOpen(false)}
          className="rounded p-1 text-text-secondary hover:bg-hover md:hidden"
        >
          <span className="sr-only">Close sidebar</span>
          &times;
        </button>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 space-y-1 px-4 py-6 overflow-y-auto">
        {menuItems
          .filter((item) => item.show)
          .map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? "bg-hover text-primary font-semibold"
                    : "text-text-secondary hover:bg-hover hover:text-text-primary"
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive ? "text-primary" : "text-text-secondary"}`} />
                {item.name}
              </Link>
            );
          })}
      </nav>

      {/* User Info Bar at Bottom */}
      <div className="border-t border-border p-4 bg-slate-50">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-primary text-white flex items-center justify-center font-bold text-sm">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-text-primary truncate">
              {user?.full_name}
            </p>
            <p className="text-[10px] text-text-secondary truncate uppercase font-bold">
              {user?.role.name}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
