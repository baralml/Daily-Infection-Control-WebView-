"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "../../../../lib/axios";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../../context/AuthContext";
import {
  Footprints,
  Plus,
  Loader2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Search,
  Camera,
  Mic,
  ArrowLeft,
  Calendar,
  MicOff,
  Layers,
  CheckSquare,
} from "lucide-react";

export default function ActiveRoundWorkspace() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const roundId = params.id as string;

  // State controls
  const [modalOpen, setModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedObs, setSelectedObs] = useState<any>(null);
  
  // Observation form state
  const [roomNumber, setRoomNumber] = useState("");
  const [isCustomRoom, setIsCustomRoom] = useState(false);
  const [remarks, setRemarks] = useState("");
  const [severity, setSeverity] = useState<string>("MEDIUM");
  
  // CAPA details
  const [shouldGenerateCapa, setShouldGenerateCapa] = useState(false);
  const [capaAssignee, setCapaAssignee] = useState("");
  const [capaDeadline, setCapaDeadline] = useState("");

  // Recording & Photo states
  const [isRecording, setIsRecording] = useState(false);
  const [recordedTranscript, setRecordedTranscript] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadingMedia, setUploadingMedia] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [finishModalOpen, setFinishModalOpen] = useState(false);

  // Dynamic layout states
  const [currentFloor, setCurrentFloor] = useState<any>(null);
  const [currentDept, setCurrentDept] = useState<any>(null);

  // Filter chips list
  const filterChips = [
    "BMW", "Hand Hygiene", "PPE", "Dust", "Equipment", "Housekeeping", 
    "Patient Safety", "Medication", "OT", "ICU", "Laboratory", 
    "Isolation", "Linen", "Catheter", "Fire Safety", "General"
  ];

  // Fetch Round details
  const { data: round, isLoading } = useQuery({
    queryKey: ["roundDetails", roundId],
    queryFn: async () => {
      const res = await axiosInstance.get(`/daily-rounds/${roundId}`);
      return res.data;
    },
  });

  // Fetch Building Layout configuration if round has building_id
  const { data: layout, isLoading: layoutLoading } = useQuery({
    queryKey: ["buildingLayout", round?.building_id],
    queryFn: async () => {
      const res = await axiosInstance.get(`/daily-rounds/layouts/${round.building_id}`);
      return res.data;
    },
    enabled: !!round?.building_id,
  });

  // Fetch Master Observations for search
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ["observationSearch", searchQuery],
    queryFn: async () => {
      const res = await axiosInstance.get(`/daily-rounds/observations/search?query=${searchQuery}`);
      return res.data;
    },
    enabled: modalOpen,
  });

  // Fetch Users for CAPA assignment
  const { data: users } = useQuery({
    queryKey: ["usersList"],
    queryFn: async () => {
      try {
        const res = await axiosInstance.get("/users");
        return res.data;
      } catch (e) {
        // Fallback for non-admin users
        return [{ id: user?.id, full_name: user?.full_name, email: user?.email }];
      }
    },
  });

  // Sort floors descending by order_index
  const sortedFloors = React.useMemo(() => {
    if (!layout?.floors) return [];
    return [...layout.floors].sort((a: any, b: any) => b.order_index - a.order_index);
  }, [layout]);

  // Set initial currentFloor and currentDept
  useEffect(() => {
    if (sortedFloors.length > 0 && !currentFloor) {
      const firstFloor = sortedFloors[0];
      setCurrentFloor(firstFloor);
      if (firstFloor.departments?.length > 0) {
        setCurrentDept(firstFloor.departments[0]);
      }
    }
  }, [sortedFloors, currentFloor]);

  // Default Assignee Setup
  useEffect(() => {
    if (users && users.length > 0 && !capaAssignee) {
      setCapaAssignee(users[0].id);
    }
  }, [users, capaAssignee]);

  // Set default deadline 7 days in future
  useEffect(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    const dateStr = d.toISOString().split("T")[0];
    setCapaDeadline(dateStr);
  }, []);

  // Set default CAPA toggle on high/critical severity
  useEffect(() => {
    if (severity === "HIGH" || severity === "CRITICAL") {
      setShouldGenerateCapa(true);
    } else {
      setShouldGenerateCapa(false);
    }
  }, [severity]);

  // Add Floor State Status Update Mutation
  const updateFloorStatusMutation = useMutation({
    mutationFn: async (payload: { floorId: string; status: string }) => {
      const res = await axiosInstance.patch(
        `/daily-rounds/${roundId}/floors/${payload.floorId}/status`,
        { status: payload.status }
      );
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roundDetails", roundId] });
    },
  });

  // Add Observation Mutation
  const addObsMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await axiosInstance.post(`/daily-rounds/${roundId}/observations`, payload);
      return res.data;
    },
    onSuccess: async (data) => {
      // Handle file uploads if any
      if (selectedFiles.length > 0) {
        setUploadingMedia(true);
        for (const file of selectedFiles) {
          const formData = new FormData();
          formData.append("file", file);
          try {
            await axiosInstance.post(
              `/daily-rounds/${roundId}/observations/${data.id}/media`,
              formData,
              { headers: { "Content-Type": "multipart/form-data" } }
            );
          } catch (err) {
            console.error("Media upload failed", err);
          }
        }
        setUploadingMedia(false);
      }

      queryClient.invalidateQueries({ queryKey: ["roundDetails", roundId] });
      setModalOpen(false);
      resetForm();
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? JSON.stringify(detail) : detail;
      setErrorMsg(msg || "Failed to add observation");
    },
  });

  // Finish Round Mutation
  const finishRoundMutation = useMutation({
    mutationFn: async () => {
      const res = await axiosInstance.post(`/daily-rounds/${roundId}/finish`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roundDetails", roundId] });
      queryClient.invalidateQueries({ queryKey: ["dailyRounds"] });
      setFinishModalOpen(true);
    },
  });

  const resetForm = () => {
    setSelectedObs(null);
    setSearchQuery("");
    setRoomNumber("");
    setIsCustomRoom(false);
    setRemarks("");
    setSeverity("MEDIUM");
    setShouldGenerateCapa(false);
    setSelectedFiles([]);
    setRecordedTranscript("");
    setErrorMsg("");
  };

  const handleSelectObs = (obs: any) => {
    setSelectedObs(obs);
    // If master observation has default severity/category, pre-fill them
    if (obs.default_severity) {
      setSeverity(obs.default_severity);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files).slice(0, 3);
      setSelectedFiles(filesArray);
    }
  };

  const handleToggleRecord = () => {
    if (isRecording) {
      setIsRecording(false);
      setRecordedTranscript(
        "Observation notes captured: Catheter securement device was partially detached."
      );
    } else {
      setIsRecording(true);
      setRecordedTranscript("Recording voice note...");
    }
  };

  const handleSaveObservation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedObs) return;

    const payload: any = {
      observation_text: selectedObs.text,
      category: selectedObs.category,
      floor_name: currentFloor ? currentFloor.floor_name : (round.floor || "General Floor"),
      department_id: currentDept ? currentDept.department_id : round.department_id,
      room_number: roomNumber || null,
      severity: severity,
      remarks: remarks + (recordedTranscript ? `\n[Transcript]: ${recordedTranscript}` : ""),
      voice_note_url: recordedTranscript ? "http://mock-audio/voice.mp3" : null,
      voice_text_transcript: recordedTranscript || null,
      has_capa: shouldGenerateCapa,
    };

    if (shouldGenerateCapa) {
      payload.capa_details = {
        assigned_to: capaAssignee,
        deadline: capaDeadline,
        priority: severity,
      };
    }

    addObsMutation.mutate(payload);
  };

  const selectFloor = (floorObj: any) => {
    setCurrentFloor(floorObj);
    if (floorObj.departments?.length > 0) {
      setCurrentDept(floorObj.departments[0]);
    } else {
      setCurrentDept(null);
    }
    
    // Auto-inspecting
    const currentStatus = round?.floor_states?.find((fs: any) => fs.floor_id === floorObj.id)?.status || "BLUE";
    if (currentStatus === "BLUE") {
      updateFloorStatusMutation.mutate({ floorId: floorObj.id, status: "ORANGE" });
    }
  };

  const handleMarkFloorComplete = (floorObj: any) => {
    const floorObs = round?.observations?.filter((o: any) => o.floor_id === floorObj.id) || [];
    const hasCriticalOrHigh = floorObs.some((o: any) => o.severity === "HIGH" || o.severity === "CRITICAL");
    const nextStatus = hasCriticalOrHigh ? "RED" : "GREEN";
    
    updateFloorStatusMutation.mutate({ floorId: floorObj.id, status: nextStatus });
  };

  if (isLoading || (round?.building_id && layoutLoading)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!round) return <div className="text-center py-20">Round session not found</div>;

  const isCompleted = round.status === "COMPLETED";

  // Filter observations in main list
  const filteredObs = round.building_id
    ? (round.observations || []).filter(
        (o: any) => o.floor_id === currentFloor?.id && o.department_id === currentDept?.department_id
      )
    : (round.observations || []);

  return (
    <div className="space-y-6">
      {/* Back navigation */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => router.push("/dashboard/daily-rounds")}
          className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary hover:text-text-primary cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Logs
        </button>

        {!isCompleted && (
          <button
            onClick={() => finishRoundMutation.mutate()}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-green-600 hover:bg-green-700 text-white rounded-md cursor-pointer transition-all shadow-sm"
          >
            <CheckCircle2 className="h-4 w-4" />
            Finish Round Walk
          </button>
        )}
      </div>

      {/* Round Header Widget */}
      <div className="card-notion p-6 bg-surface border border-border relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-primary to-secondary" />

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-xs text-text-secondary">
          <div>
            <span className="block font-medium">Hospital Center</span>
            <span className="font-bold text-text-primary text-sm mt-1 block">
              {round.hospital}
            </span>
            <span className="text-[10px] text-text-secondary block mt-0.5">
              {round.building_id ? `${round.building} (Layout)` : `${round.building} • Floor ${round.floor}`}
            </span>
          </div>

          <div>
            <span className="block font-medium">Clinical Unit</span>
            <span className="font-bold text-text-primary text-sm mt-1 block">
              {round.building_id
                ? (currentDept?.department?.name || "Multiple Wards")
                : (round.department?.name || "General Unit")}
            </span>
            <span className="text-[10px] text-text-secondary block mt-0.5 uppercase font-bold">
              Shift: {round.round_type}
            </span>
          </div>

          <div>
            <span className="block font-medium">Observation Logs</span>
            <span className="font-extrabold text-primary text-base mt-1 block">
              {round.observations?.length || 0} Gaps
            </span>
          </div>

          <div>
            <span className="block font-medium">CAPA Actions Generated</span>
            <span className="font-extrabold text-success text-base mt-1 block">
              {round.observations?.filter((o: any) => o.has_capa).length || 0} Tickets
            </span>
          </div>
        </div>
      </div>

      {/* Building Layout Selector Bar */}
      {round.building_id && (
        <div className="space-y-4">
          {/* Floor selector horizontal ribbon */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
              <Layers className="h-3.5 w-3.5 text-text-secondary" />
              Floor Navigation
            </label>
            <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin">
              {sortedFloors.map((fl: any) => {
                const fs = round.floor_states?.find((state: any) => state.floor_id === fl.id);
                const status = fs?.status || "BLUE";
                const isActive = currentFloor?.id === fl.id;

                let cardStyle = "bg-white border-border text-text-secondary hover:bg-hover hover:border-text-secondary/30";
                let badgeLabel = "Not Visited";
                let dotColor = "bg-slate-300";

                if (status === "ORANGE") {
                  cardStyle = "bg-amber-50/50 border-amber-300 text-amber-800 ring-2 ring-amber-300/30";
                  badgeLabel = "Inspecting";
                  dotColor = "bg-amber-500 animate-ping";
                } else if (status === "GREEN") {
                  cardStyle = "bg-emerald-50/40 border-emerald-300 text-emerald-800";
                  badgeLabel = "Completed";
                  dotColor = "bg-emerald-500";
                } else if (status === "RED") {
                  cardStyle = "bg-rose-50/40 border-rose-300 text-rose-800";
                  badgeLabel = "Completed (Gaps)";
                  dotColor = "bg-rose-500";
                }

                if (isActive) {
                  cardStyle += " ring-2 ring-primary border-primary";
                }

                return (
                  <button
                    key={fl.id}
                    type="button"
                    onClick={() => selectFloor(fl)}
                    className={`flex flex-col items-start p-3 rounded-lg border min-w-[130px] shrink-0 text-left transition-all cursor-pointer ${cardStyle}`}
                  >
                    <span className="font-extrabold text-sm text-text-primary">{fl.floor_name}</span>
                    <span className="flex items-center gap-1 mt-1 text-[9px] font-bold uppercase tracking-wider">
                      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
                      {badgeLabel}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Department Selection Cards */}
          {currentFloor && (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-text-primary">
                Active Ward / Clinical Department in {currentFloor.floor_name}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {currentFloor.departments?.map((dept: any) => {
                  const isActive = currentDept?.id === dept.id;
                  const obsCount = (round.observations || []).filter(
                    (o: any) => o.floor_id === currentFloor.id && o.department_id === dept.department_id
                  ).length || 0;

                  return (
                    <button
                      key={dept.id}
                      type="button"
                      onClick={() => setCurrentDept(dept)}
                      className={`flex flex-col justify-between p-4 rounded-xl border text-left cursor-pointer transition-all ${
                        isActive
                          ? "bg-primary/5 border-primary text-primary shadow-sm"
                          : "bg-surface border-border hover:border-text-secondary/20 hover:bg-hover"
                      }`}
                    >
                      <div>
                        <span className={`text-xs font-bold ${isActive ? "text-primary" : "text-text-primary"}`}>
                          {dept.department?.name || `Dept #${dept.department_id}`}
                        </span>
                        <span className="block text-[9px] text-text-secondary uppercase font-semibold mt-0.5">
                          Code: {dept.department?.code || "N/A"}
                        </span>
                      </div>
                      <div className="mt-4 flex items-center justify-between w-full">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          obsCount > 0
                            ? "bg-red-50 text-danger border border-red-100"
                            : "bg-slate-100 text-text-secondary border border-slate-200"
                        }`}>
                          {obsCount} Gaps
                        </span>
                        {isActive && (
                          <span className="text-[10px] font-semibold text-primary">Active</span>
                        )}
                      </div>
                    </button>
                  );
                })}
                {currentFloor.departments?.length === 0 && (
                  <div className="col-span-full py-6 text-center text-xs text-text-secondary border border-dashed border-border rounded-xl">
                    No clinical departments configured for this floor level.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Floor actions control panel */}
          {currentFloor && !isCompleted && (
            <div className="flex justify-between items-center bg-slate-50 p-4 rounded-xl border border-border/80 text-xs">
              <div>
                <span className="font-semibold text-text-primary">Floor Completion Control</span>
                <p className="text-[10px] text-text-secondary mt-0.5">
                  Confirm inspection status of {currentFloor.floor_name} walks.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleMarkFloorComplete(currentFloor)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md font-bold cursor-pointer transition-colors shadow-sm"
                >
                  <CheckCircle2 className="h-4.5 w-4.5" />
                  Mark Floor Complete
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Observations list */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
              {round.building_id
                ? `Observations in ${currentFloor?.floor_name || "Active Floor"} • ${currentDept?.department?.name || "Active Dept"}`
                : "Recorded Observations"}
            </h3>
            {!isCompleted && (!round.building_id || currentDept) && (
              <button
                onClick={() => {
                  resetForm();
                  setModalOpen(true);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-primary hover:bg-secondary text-white rounded-md cursor-pointer transition-all"
              >
                <Plus className="h-4 w-4" />
                Add Observation
              </button>
            )}
          </div>

          <div className="space-y-4">
            {filteredObs.map((obs: any) => {
              let badgeColor = "bg-slate-100 text-text-secondary border-slate-200";
              if (obs.severity === "HIGH") badgeColor = "bg-red-50 text-danger border-red-200";
              else if (obs.severity === "CRITICAL")
                badgeColor = "bg-red-100 text-danger border-red-300 animate-pulse";
              else if (obs.severity === "MEDIUM")
                badgeColor = "bg-amber-50 text-warning border-amber-200";

              return (
                <div
                  key={obs.id}
                  className="card-notion p-5 bg-surface border border-border flex flex-col md:flex-row gap-5 items-start relative hover:shadow-md transition-shadow"
                >
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide bg-slate-50 text-text-secondary">
                        {obs.category}
                      </span>
                      <span className={`rounded border px-1.5 py-0.5 text-[9px] font-bold ${badgeColor}`}>
                        {obs.severity}
                      </span>
                      {obs.room_number && (
                        <span className="text-[10px] text-text-secondary font-medium">
                          Room: {obs.room_number}
                        </span>
                      )}
                    </div>

                    <h4 className="font-bold text-text-primary text-sm leading-tight">
                      {obs.observation_text}
                    </h4>

                    {obs.remarks && (
                      <p className="text-xs text-text-secondary bg-slate-50/50 p-2.5 rounded border border-border/40 whitespace-pre-wrap">
                        {obs.remarks}
                      </p>
                    )}

                    {obs.voice_text_transcript && (
                      <div className="flex items-center gap-1.5 text-[10px] text-primary bg-blue-50/20 px-2 py-1 rounded border border-blue-100">
                        <Mic className="h-3 w-3" />
                        <span>Voice Transcript: {obs.voice_text_transcript}</span>
                      </div>
                    )}
                  </div>

                  {/* Photo thumbnails */}
                  {obs.media?.length > 0 && (
                    <div className="flex gap-2 shrink-0 overflow-x-auto max-w-[200px]">
                      {obs.media.map((med: any) => (
                        <img
                          key={med.id}
                          src={med.thumbnail_url || med.original_url}
                          alt="Observation Attachment"
                          className="h-16 w-16 rounded object-cover border border-border hover:scale-105 transition-transform"
                        />
                      ))}
                    </div>
                  )}

                  {/* CAPA check */}
                  {obs.has_capa && (
                    <div className="absolute bottom-4 right-4 flex items-center gap-1 text-[10px] font-bold text-success border border-green-200 bg-green-50 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="h-3 w-3" />
                      CAPA Active
                    </div>
                  )}
                </div>
              );
            })}

            {filteredObs.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-xl bg-slate-50/20 text-text-secondary">
                <Footprints className="h-10 w-10 opacity-30 mb-2" />
                <p className="font-semibold text-sm">No observations recorded</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  {round.building_id
                    ? "Tap '+ Add Observation' to log gaps for this unit."
                    : "Start walking and tap '+ Add Observation' to log gaps."}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Side summary details card */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">
            Round Walk Info
          </h3>
          <div className="card-notion p-6 bg-surface border border-border space-y-4 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-text-secondary font-medium">Session Status</span>
              {isCompleted ? (
                <span className="font-bold text-success">Walk Sealed</span>
              ) : (
                <span className="font-bold text-warning animate-pulse">Live Walking</span>
              )}
            </div>

            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-text-secondary font-medium">Start Time</span>
              <span className="font-bold text-text-primary">
                {new Date(round.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>

            {isCompleted && (
              <div className="flex justify-between items-center py-2 border-b border-border">
                <span className="text-text-secondary font-medium">Sealed Time</span>
                <span className="font-bold text-text-primary">
                  {new Date(round.ended_at!).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            )}

            <div className="flex justify-between items-center py-2 border-b border-border">
              <span className="text-text-secondary font-medium">Walk Duration</span>
              <span className="font-bold text-text-primary">
                {isCompleted
                  ? `${Math.round((new Date(round.ended_at!).getTime() - new Date(round.started_at).getTime()) / 60000)} Mins`
                  : "Calculating..."}
              </span>
            </div>

            <div className="flex justify-between items-center py-2">
              <span className="text-text-secondary font-medium">Infection Auditor</span>
              <span className="font-bold text-text-primary">
                {round.auditor?.full_name}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline Widget */}
      <div className="card-notion p-6 bg-surface border border-border space-y-4">
        <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-1.5">
          <Clock className="h-4 w-4 text-text-secondary" />
          Round Audit Timeline & Logs
        </h3>
        <div className="relative border-l border-slate-200 pl-5 ml-2.5 space-y-5 py-2">
          {/* Start Point */}
          <div className="relative">
            <span className="absolute -left-[24.5px] top-1.5 h-2 w-2 rounded-full bg-primary ring-4 ring-white" />
            <span className="text-[10px] text-text-secondary font-bold">
              {new Date(round.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
            <span className="block text-xs font-bold text-text-primary mt-0.5">Round walk initialized</span>
          </div>

          {round.observations?.map((obs: any) => (
            <div key={obs.id} className="relative">
              <span className="absolute -left-[24.5px] top-1.5 h-2 w-2 rounded-full bg-danger ring-4 ring-white" />
              <div className="flex justify-between items-start gap-4">
                <div>
                  <span className="text-[10px] text-text-secondary font-bold">
                    {new Date(obs.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                  <span className="block text-xs font-bold text-text-primary mt-0.5">
                    {obs.observation_text}
                  </span>
                  <span className="block text-[10px] text-text-secondary mt-0.5">
                    {obs.floor_name} &bull; {obs.department?.name || "General Unit"} {obs.room_number ? `&bull; Room ${obs.room_number}` : ""}
                  </span>
                </div>
                <span className={`rounded border px-1.5 py-0.5 text-[8px] font-bold shrink-0 ${
                  obs.severity === "HIGH" || obs.severity === "CRITICAL"
                    ? "bg-red-50 text-danger border-red-200"
                    : obs.severity === "MEDIUM"
                    ? "bg-amber-50 text-warning border-amber-200"
                    : "bg-slate-50 text-text-secondary border-slate-200"
                }`}>
                  {obs.severity}
                </span>
              </div>
            </div>
          ))}

          {isCompleted && (
            <div className="relative">
              <span className="absolute -left-[24.5px] top-1.5 h-2 w-2 rounded-full bg-green-500 ring-4 ring-white" />
              <span className="text-[10px] text-text-secondary font-bold">
                {new Date(round.ended_at!).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
              <span className="block text-xs font-bold text-text-primary mt-0.5">Round walk finished & sealed</span>
            </div>
          )}
        </div>
      </div>

      {/* Observation Search & Add Modal Drawer */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 animate-fade-in">
          <div className="w-full max-w-2xl bg-surface border border-border rounded-lg shadow-xl p-6 relative flex flex-col max-h-[85vh] overflow-hidden">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider border-b border-border pb-3">
              Add Floor Observation
            </h3>

            {errorMsg && (
              <div className="mt-3 flex items-center gap-2 rounded-md bg-red-50 border border-red-200 p-3 text-xs text-danger shrink-0">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                {errorMsg}
              </div>
            )}

            {/* Smart Google-Style Search */}
            {!selectedObs ? (
              <div className="mt-4 flex-1 flex flex-col min-h-0">
                <div className="relative shrink-0">
                  <Search className="absolute top-2.5 left-3 h-4 w-4 text-text-secondary" />
                  <input
                    type="text"
                    placeholder="Search observations... (e.g. dus, ppe, bmw)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 border border-border rounded-md focus:outline-none focus:border-primary text-xs"
                    autoFocus
                  />
                </div>

                {/* Filter Chips */}
                <div className="flex flex-wrap gap-1.5 mt-3 py-1 overflow-y-auto max-h-16 shrink-0">
                  {filterChips.map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => setSearchQuery(chip.toLowerCase())}
                      className="px-2 py-0.5 text-[9px] font-bold border border-border rounded bg-slate-50 text-text-secondary hover:bg-hover cursor-pointer"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* List Results */}
                <div className="flex-1 overflow-y-auto mt-4 border border-border rounded-md divide-y divide-border min-h-48 pr-1">
                  {searchLoading ? (
                    <div className="flex h-32 items-center justify-center">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                  ) : (
                    searchResults?.map((res: any) => (
                      <button
                        key={res.id}
                        type="button"
                        onClick={() => handleSelectObs(res)}
                        className="w-full text-left p-3 hover:bg-hover flex justify-between items-center gap-3 text-xs text-text-primary transition-colors cursor-pointer"
                      >
                        <span className="font-semibold">{res.text}</span>
                        <span className="rounded border px-1.5 py-0.5 text-[8px] font-bold uppercase shrink-0 bg-slate-100 text-text-secondary border-slate-200">
                          {res.category}
                        </span>
                      </button>
                    ))
                  )}

                  {searchResults?.length === 0 && (
                    <div className="text-center py-10 text-text-secondary text-xs">
                      No matching observations found.
                    </div>
                  )}
                </div>

                <div className="flex justify-end pt-4 border-t border-border mt-4 shrink-0">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              /* Selected Observation Form Details */
              <form onSubmit={handleSaveObservation} className="mt-4 space-y-4 overflow-y-auto pr-1 flex-1">
                <div className="bg-slate-50 p-3 rounded-lg border border-border/80 text-xs">
                  <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider block">
                    Selected Observation Text
                  </span>
                  <span className="font-bold text-text-primary mt-1 block">
                    {selectedObs.text}
                  </span>
                  <span className="rounded border px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wide inline-block mt-2 bg-slate-200/60 text-text-secondary border-slate-300">
                    {selectedObs.category}
                  </span>
                </div>

                {/* Severity & Room */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-primary">
                      Observation Severity
                    </label>
                    <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-bold">
                      {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((sev) => {
                        let btnStyle = "border-border hover:bg-hover text-text-secondary";
                        if (severity === sev) {
                          if (sev === "LOW") btnStyle = "bg-slate-500 border-slate-500 text-white";
                          else if (sev === "MEDIUM") btnStyle = "bg-warning border-warning text-white";
                          else btnStyle = "bg-danger border-danger text-white";
                        }
                        return (
                          <button
                            key={sev}
                            type="button"
                            onClick={() => setSeverity(sev)}
                            className={`py-1.5 border rounded cursor-pointer transition-colors ${btnStyle}`}
                          >
                            {sev}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-primary">
                      Room Number / Bed No (Optional)
                    </label>
                    {currentDept?.rooms && currentDept.rooms.length > 0 && !isCustomRoom ? (
                      <select
                        value={roomNumber}
                        onChange={(e) => {
                          if (e.target.value === "__CUSTOM__") {
                            setIsCustomRoom(true);
                            setRoomNumber("");
                          } else {
                            setRoomNumber(e.target.value);
                          }
                        }}
                        className="input-notion focus:border-primary text-xs"
                      >
                        <option value="">-- Select Room / Bed --</option>
                        {currentDept.rooms.map((r: any) => (
                          <option key={r.id} value={r.room_number}>
                            {r.room_number}
                          </option>
                        ))}
                        <option value="__CUSTOM__">✍️ Enter Custom Room Number...</option>
                      </select>
                    ) : (
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          placeholder="e.g. ICU-3A"
                          value={roomNumber}
                          onChange={(e) => setRoomNumber(e.target.value)}
                          className="input-notion focus:border-primary text-xs flex-1"
                        />
                        {currentDept?.rooms && currentDept.rooms.length > 0 && (
                          <button
                            type="button"
                            onClick={() => {
                              setIsCustomRoom(false);
                              setRoomNumber("");
                            }}
                            className="px-2.5 py-1.5 text-[10px] font-bold border border-border rounded hover:bg-hover bg-slate-50 text-text-secondary cursor-pointer shrink-0"
                          >
                            Show List
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Remarks */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-text-primary">
                    Remarks & Auditing Comments
                  </label>
                  <textarea
                    placeholder="Enter observations, details, or specific gaps..."
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    className="input-notion focus:border-primary text-xs h-16 min-h-12"
                  />
                </div>

                {/* Media Capture & Voice Note */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                      <Camera className="h-3.5 w-3.5 text-text-secondary" />
                      Attach Photos (Max 3)
                    </label>
                    <input
                      type="file"
                      multiple
                      accept="image/*"
                      onChange={handleFileChange}
                      className="text-xs file:mr-3 file:py-1 file:px-2.5 file:rounded file:border file:border-border file:text-xs file:font-semibold file:bg-slate-50 hover:file:bg-hover cursor-pointer"
                    />
                    {selectedFiles.length > 0 && (
                      <span className="text-[10px] text-text-secondary font-medium">
                        {selectedFiles.length} file(s) selected
                      </span>
                    )}
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-semibold text-text-primary flex items-center gap-1">
                      <Mic className="h-3.5 w-3.5 text-text-secondary" />
                      Voice Note (Simulated Speech-To-Text)
                    </label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={handleToggleRecord}
                        className={`flex items-center gap-1 px-3 py-1.5 border rounded text-xs font-bold cursor-pointer transition-colors ${
                          isRecording
                            ? "bg-red-500 border-red-500 text-white animate-pulse"
                            : "bg-slate-50 border-border text-text-secondary hover:bg-hover"
                        }`}
                      >
                        {isRecording ? (
                          <>
                            <MicOff className="h-3.5 w-3.5" />
                            Stop
                          </>
                        ) : (
                          <>
                            <Mic className="h-3.5 w-3.5" />
                            Record
                          </>
                        )}
                      </button>
                      {recordedTranscript && (
                        <div className="flex-1 bg-blue-50/30 border border-blue-100 p-1.5 rounded text-[9px] text-primary truncate">
                          {recordedTranscript}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Integrated CAPA Creation */}
                {shouldGenerateCapa && (
                  <div className="rounded-lg border border-green-200 bg-green-50/10 p-4 space-y-4">
                    <div className="flex items-center gap-2 border-b border-green-200 pb-2">
                      <CheckCircle2 className="h-4 w-4 text-success" />
                      <span className="text-xs font-bold text-success uppercase tracking-wider">
                        Integrated CAPA Ticket Generation
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-text-primary">
                          Assign Responsible Person
                        </label>
                        <select
                          value={capaAssignee}
                          onChange={(e) => setCapaAssignee(e.target.value)}
                          className="input-notion focus:border-primary text-xs"
                        >
                          {users?.map((u: any) => (
                            <option key={u.id} value={u.id}>
                              {u.full_name} ({u.role.name})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-text-primary">
                          Target Resolution Deadline
                        </label>
                        <input
                          type="date"
                          value={capaDeadline}
                          onChange={(e) => setCapaDeadline(e.target.value)}
                          className="input-notion focus:border-primary text-xs"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-between items-center pt-4 border-t border-border mt-6 shrink-0">
                  <button
                    type="button"
                    onClick={() => setSelectedObs(null)}
                    className="flex items-center gap-1 text-xs font-semibold border border-border rounded-md px-3 py-1.5 hover:bg-hover cursor-pointer"
                  >
                    <ArrowLeft className="h-3.5 w-3.5" />
                    Back to Search
                  </button>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setModalOpen(false)}
                      className="px-4 py-2 text-xs font-semibold border border-border rounded-md hover:bg-hover cursor-pointer"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={addObsMutation.isPending || uploadingMedia}
                      className="flex items-center gap-1 px-4 py-2 text-xs font-semibold bg-primary text-white rounded-md hover:bg-secondary cursor-pointer disabled:opacity-50"
                    >
                      {addObsMutation.isPending || uploadingMedia ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        "Save Observation"
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Completion Summary Modal */}
      {finishModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 animate-fade-in">
          <div className="w-full max-w-md bg-surface border border-border rounded-lg shadow-xl p-6 text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-green-100 text-success flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-6 w-6" />
            </div>

            <div>
              <h3 className="text-base font-bold text-text-primary uppercase tracking-wide">
                Daily Round Walk Finished
              </h3>
              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                Your walking round session has been sealed. The observations have been compiled and sent to the dashboard logbooks.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg text-xs text-text-secondary border border-border/40">
              <div>
                <span className="block font-medium">Gaps Found</span>
                <span className="font-bold text-text-primary text-sm mt-0.5 block">
                  {round.observations?.length || 0} Gaps
                </span>
              </div>
              <div>
                <span className="block font-medium">CAPAs Generated</span>
                <span className="font-bold text-success text-sm mt-0.5 block">
                  {round.observations?.filter((o: any) => o.has_capa).length || 0} Tickets
                </span>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <button
                type="button"
                onClick={() => {
                  setFinishModalOpen(false);
                  router.push("/dashboard/daily-rounds");
                }}
                className="w-full py-2 bg-primary hover:bg-secondary text-white rounded-md text-xs font-semibold cursor-pointer transition-colors"
              >
                Return to Daily Round Logs
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
