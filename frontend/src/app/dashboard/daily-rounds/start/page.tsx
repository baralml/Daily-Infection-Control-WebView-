"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import axiosInstance from "../../../../lib/axios";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../../context/AuthContext";
import {
  Footprints,
  Building,
  MapPin,
  Clock,
  User,
  ArrowRight,
  Loader2,
  AlertTriangle,
  Layers,
} from "lucide-react";

export default function StartDailyRound() {
  const router = useRouter();
  const { user } = useAuth();

  const [mode, setMode] = useState<"layout" | "adhoc">("layout");
  const [hospital, setHospital] = useState("ABC Hospital");
  const [building, setBuilding] = useState("");
  const [selectedBuildingId, setSelectedBuildingId] = useState("");
  const [floor, setFloor] = useState("6th Floor");
  const [selectedDept, setSelectedDept] = useState("");
  const [roundType, setRoundType] = useState("Morning");
  const [errorMsg, setErrorMsg] = useState("");

  // Fetch configured building layouts
  const { data: buildings, isLoading: buildingsLoading } = useQuery({
    queryKey: ["buildingLayouts"],
    queryFn: async () => {
      const res = await axiosInstance.get("/daily-rounds/layouts");
      return res.data;
    },
  });

  // Fetch Departments (for ad-hoc mode)
  const { data: departments, isLoading: deptsLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: async () => {
      const res = await axiosInstance.get("/audits/admin/departments");
      return res.data;
    },
  });

  // Set default building when layouts load
  useEffect(() => {
    if (buildings && buildings.length > 0 && !selectedBuildingId) {
      setSelectedBuildingId(buildings[0].id);
      setBuilding(buildings[0].name);
    }
  }, [buildings]);

  // Start walking round mutation
  const startRoundMutation = useMutation({
    mutationFn: async (payload: {
      hospital: string;
      building: string;
      building_id?: string | null;
      floor?: string | null;
      department_id?: number | null;
      round_type: string;
    }) => {
      const res = await axiosInstance.post("/daily-rounds", payload);
      return res.data;
    },
    onSuccess: (data) => {
      router.push(`/dashboard/daily-rounds/${data.id}`);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? JSON.stringify(detail) : detail;
      setErrorMsg(msg || "Failed to start walking round");
    },
  });

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");

    if (mode === "layout") {
      if (!selectedBuildingId) {
        setErrorMsg("Please select a building layout configuration");
        return;
      }
      startRoundMutation.mutate({
        hospital,
        building,
        building_id: selectedBuildingId,
        floor: null,
        department_id: null,
        round_type: roundType,
      });
    } else {
      if (!selectedDept) {
        setErrorMsg("Please select a target clinical department");
        return;
      }
      startRoundMutation.mutate({
        hospital,
        building: building || "Main Block",
        building_id: null,
        floor,
        department_id: parseInt(selectedDept),
        round_type: roundType,
      });
    }
  };

  const todayStr = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <Footprints className="h-6 w-6 text-primary" />
          Start Daily Round
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          Configure location parameters to initialize your floor walking observation sheet.
        </p>
      </div>

      {/* Mode Selector */}
      <div className="flex gap-2 p-1 bg-slate-100/80 rounded-lg border border-border/40 text-xs font-bold max-w-sm">
        <button
          type="button"
          onClick={() => {
            setMode("layout");
            setErrorMsg("");
            // Set defaults from layouts if available
            if (buildings && buildings.length > 0) {
              setSelectedBuildingId(buildings[0].id);
              setBuilding(buildings[0].name);
            }
          }}
          className={`flex-1 py-1.5 px-3 rounded-md transition-all cursor-pointer ${
            mode === "layout"
              ? "bg-white text-primary shadow-sm"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          🏢 Configured Layout
        </button>
        <button
          type="button"
          onClick={() => {
            setMode("adhoc");
            setErrorMsg("");
            setBuilding("Main Block");
          }}
          className={`flex-1 py-1.5 px-3 rounded-md transition-all cursor-pointer ${
            mode === "adhoc"
              ? "bg-white text-primary shadow-sm"
              : "text-text-secondary hover:text-text-primary"
          }`}
        >
          ✏️ Ad-hoc Walk
        </button>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-xs text-danger">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleStart} className="card-notion p-6 space-y-6 bg-surface border border-border">
        {/* Auditor & Time Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg text-xs border border-border/60">
          <div className="flex items-center gap-2 text-text-secondary">
            <User className="h-4 w-4 text-primary" />
            <div>
              <span className="block font-medium">Auditor (Auto-assigned)</span>
              <span className="font-bold text-text-primary mt-0.5 block">{user?.full_name}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-text-secondary">
            <Clock className="h-4 w-4 text-primary" />
            <div>
              <span className="block font-medium">Date & Session</span>
              <span className="font-bold text-text-primary mt-0.5 block">{todayStr}</span>
            </div>
          </div>
        </div>

        {/* Form Inputs */}
        <div className="space-y-4">
          {/* Hospital Center */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
              <Building className="h-3.5 w-3.5 text-text-secondary" />
              Hospital Center
            </label>
            <select
              value={hospital}
              onChange={(e) => setHospital(e.target.value)}
              className="input-notion focus:border-primary text-xs"
            >
              <option value="ABC Hospital">ABC Hospital</option>
              <option value="Apollo City Hospital">Apollo City Hospital</option>
              <option value="District General Hospital">District General Hospital</option>
            </select>
          </div>

          {mode === "layout" ? (
            /* Layout Mode Inputs */
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-text-secondary" />
                Select Building Layout Configuration
              </label>
              {buildingsLoading ? (
                <div className="flex items-center gap-2 text-xs text-text-secondary py-2">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  Loading layouts...
                </div>
              ) : (
                <select
                  value={selectedBuildingId}
                  onChange={(e) => {
                    const bId = e.target.value;
                    setSelectedBuildingId(bId);
                    const bName = buildings?.find((b: any) => b.id === bId)?.name || "";
                    setBuilding(bName);
                  }}
                  className="input-notion focus:border-primary text-xs"
                >
                  {buildings?.map((b: any) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                  {buildings?.length === 0 && (
                    <option value="">No layouts available. Please seed them in the backend.</option>
                  )}
                </select>
              )}
              <span className="text-[10px] text-text-secondary">
                ℹ️ Floors and departments will be selected dynamically floor-by-floor during the active round walk workspace.
              </span>
            </div>
          ) : (
            /* Ad-hoc Mode Inputs */
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-text-secondary" />
                    Building / Block Name
                  </label>
                  <input
                    type="text"
                    required
                    value={building}
                    onChange={(e) => setBuilding(e.target.value)}
                    placeholder="e.g. Main Block"
                    className="input-notion focus:border-primary text-xs"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-primary">
                    Floor Level
                  </label>
                  <select
                    value={floor}
                    onChange={(e) => setFloor(e.target.value)}
                    className="input-notion focus:border-primary text-xs"
                  >
                    <option value="Ground Floor">Ground Floor</option>
                    <option value="1st Floor">1st Floor</option>
                    <option value="2nd Floor">2nd Floor</option>
                    <option value="3rd Floor">3rd Floor</option>
                    <option value="4th Floor">4th Floor</option>
                    <option value="5th Floor">5th Floor</option>
                    <option value="6th Floor">6th Floor</option>
                    <option value="7th Floor">7th Floor</option>
                  </select>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold text-text-primary">
                  Target Department / Ward
                </label>
                <select
                  value={selectedDept}
                  required
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="input-notion focus:border-primary text-xs"
                >
                  <option value="">-- Select Department --</option>
                  {departments?.map((d: any) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Round Type Shift */}
          <div className="flex flex-col gap-1.5 pt-2">
            <label className="text-xs font-semibold text-text-primary">
              Shift Session
            </label>
            <div className="grid grid-cols-4 gap-3 text-center">
              {["Morning", "Afternoon", "Evening", "Night"].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setRoundType(type)}
                  className={`py-2 px-3 text-xs font-bold border rounded-lg cursor-pointer transition-all ${
                    roundType === type
                      ? "bg-primary border-primary text-white shadow-sm"
                      : "bg-surface border-border text-text-secondary hover:bg-hover"
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-border mt-6">
          <button
            type="button"
            onClick={() => router.push("/dashboard/daily-rounds")}
            className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={startRoundMutation.isPending || (mode === "adhoc" && deptsLoading) || (mode === "layout" && buildingsLoading)}
            className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer shadow disabled:opacity-50 transition-all"
          >
            {startRoundMutation.isPending ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Initializing...
              </>
            ) : (
              <>
                Start Walking
                <ArrowRight className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
