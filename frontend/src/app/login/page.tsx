"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "../../context/AuthContext";
import axios from "axios";
import {
  Shield,
  Eye,
  EyeOff,
  Loader2,
  AlertTriangle,
  CheckCircle,
  MapPin,
  Camera,
  Upload,
  UserPlus,
  Sun,
  Moon,
} from "lucide-react";

const loginSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z.string().min(8, { message: "Password must be at least 8 characters" }),
});

type LoginSchemaType = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  
  // Navigation tabs: "signin" | "register" | "report"
  const [activeTab, setActiveTab] = useState<"signin" | "register" | "report">("signin");
  
  // Theme state
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Login states
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Self-Registration states
  const [roles, setRoles] = useState<any[]>([]);
  const [regEmail, setRegEmail] = useState("");
  const [regName, setRegName] = useState("");
  const [regPhone, setRegPhone] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRoleId, setRegRoleId] = useState("");
  const [regSuccess, setRegSuccess] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);
  const [registering, setRegistering] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpVal, setOtpVal] = useState("");
  const [otpMock, setOtpMock] = useState("");

  // Anonymous Staff Report states
  const [reportDesc, setReportDesc] = useState("");
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [gpsStatus, setGpsStatus] = useState<"idle" | "capturing" | "success" | "denied">("idle");
  const [reportSuccess, setReportSuccess] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [reporting, setReporting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginSchemaType>({
    resolver: zodResolver(loginSchema),
  });

  // Theme Sync on Mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("theme") as "light" | "dark" | null;
      if (savedTheme) {
        setTheme(savedTheme);
        if (savedTheme === "dark") {
          document.documentElement.classList.add("dark");
        } else {
          document.documentElement.classList.remove("dark");
        }
      } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        setTheme("dark");
        document.documentElement.classList.add("dark");
      }
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

  // Clear any existing access token on login mount to prevent interceptor pollution
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  }, []);

  // Check auth state
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  // Load roles list for registration dropdown (use raw axios to bypass interceptor)
  useEffect(() => {
    axios.get("/api/v1/auth/roles")
      .then(res => setRoles(res.data))
      .catch(err => console.error("Failed to load roles", err));
  }, []);

  // Trigger GPS capture automatically on clicking the report tab
  useEffect(() => {
    if (activeTab === "report") {
      triggerGpsCapture();
    }
  }, [activeTab]);

  const triggerGpsCapture = () => {
    setGpsStatus("capturing");
    if (!navigator.geolocation) {
      setGpsStatus("denied");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude);
        setLongitude(pos.coords.longitude);
        setGpsStatus("success");
      },
      (err) => {
        console.error("GPS Geolocation error", err);
        setGpsStatus("denied");
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  // Login handler
  const onSubmit = async (data: LoginSchemaType) => {
    setErrorMessage(null);
    try {
      await login(data.email, data.password);
    } catch (err: any) {
      setErrorMessage(err.message || "An unexpected error occurred. Please check your credentials.");
    }
  };

  // Self-Registration handler (use raw axios to bypass interceptor)
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError(null);
    setRegSuccess(false);
    setRegistering(true);

    try {
      if (!otpSent) {
        // Request verification OTP first
        const res = await axios.post("/api/v1/auth/register/send-otp", {
          email: regEmail
        });
        setOtpSent(true);
        setOtpMock(res.data.mock_otp || "");
        setRegError(null);
      } else {
        // Verify OTP and complete signup
        await axios.post("/api/v1/auth/register/verify-otp", {
          email: regEmail,
          otp: otpVal
        });

        // OTP verified! Submit final registration
        await axios.post("/api/v1/auth/register", {
          email: regEmail,
          password: regPassword,
          full_name: regName,
          phone_number: regPhone || null,
          role_id: parseInt(regRoleId),
          is_active: false,
        });

        setRegSuccess(true);
        setOtpSent(false);
        setOtpVal("");
        setOtpMock("");
        // Reset form fields
        setRegEmail("");
        setRegName("");
        setRegPhone("");
        setRegPassword("");
        setRegRoleId("");
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setRegError(typeof detail === "object" ? JSON.stringify(detail) : (detail || "Registration failed. Please check inputs."));
    } finally {
      setRegistering(false);
    }
  };

  // Quick Anonymous Report handler (use raw axios to bypass interceptor)
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportDesc.trim()) return;
    
    setReportError(null);
    setReportSuccess(false);
    setReporting(true);

    const formData = new FormData();
    formData.append("description", reportDesc);
    if (latitude !== null) formData.append("latitude", latitude.toString());
    if (longitude !== null) formData.append("longitude", longitude.toString());
    if (reportFile) {
      formData.append("file", reportFile);
    }

    try {
      await axios.post("/api/v1/staff-reports", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setReportSuccess(true);
      setReportDesc("");
      setReportFile(null);
      setLatitude(null);
      setLongitude(null);
      setGpsStatus("idle");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setReportError(typeof detail === "object" ? JSON.stringify(detail) : (detail || "Failed to submit safety report."));
    } finally {
      setReporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-950 transition-colors duration-300 relative">
      
      {/* Theme Toggle Button */}
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full border border-border bg-surface text-text-secondary hover:text-text-primary shadow-sm cursor-pointer transition-all hover:bg-hover"
          title="Toggle Theme"
        >
          {theme === "dark" ? <Sun className="h-5 w-5 text-amber-500" /> : <Moon className="h-5 w-5" />}
        </button>
      </div>

      <div className="w-full max-w-md card-notion relative overflow-hidden bg-surface border border-border shadow-md">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-secondary" />

        {/* Brand Header */}
        <div className="flex flex-col items-center pt-2">
          <div className="flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-primary">
            <Shield className="h-6 w-6 text-primary" />
          </div>
          <h2 className="mt-3 text-center text-lg font-bold tracking-tight text-text-primary">
            Infection Control Platform
          </h2>
          <p className="mt-1 text-center text-xs text-text-secondary">
            Hospital Quality Auditing & Safety Reporting
          </p>
        </div>

        {/* Tab Selector Ribbon */}
        <div className="flex border-b border-border mt-6 text-center text-xs font-bold uppercase tracking-wider">
          <button
            onClick={() => {
              setActiveTab("signin");
              setErrorMessage(null);
            }}
            className={`flex-1 pb-2 border-b-2 transition-all cursor-pointer ${
              activeTab === "signin"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => {
              setActiveTab("register");
              setRegError(null);
            }}
            className={`flex-1 pb-2 border-b-2 transition-all cursor-pointer ${
              activeTab === "register"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            Self-Register
          </button>
          <button
            onClick={() => {
              setActiveTab("report");
              setReportError(null);
            }}
            className={`flex-1 pb-2 border-b-2 transition-all cursor-pointer ${
              activeTab === "report"
                ? "border-primary text-primary"
                : "border-transparent text-text-secondary hover:text-text-primary"
            }`}
          >
            Quick Report
          </button>
        </div>

        {/* Sign In Form View (Kept in DOM to prevent React Hook Form reference loss) */}
        <form
          className={`mt-6 space-y-5 ${activeTab === "signin" ? "block" : "hidden"}`}
          onSubmit={handleSubmit(onSubmit)}
        >
          {errorMessage && (
            <div className="rounded-md bg-red-50 dark:bg-red-950/20 p-3 border border-red-200 dark:border-red-900/50 text-xs text-danger font-medium">
              {errorMessage}
            </div>
          )}

          <div className="space-y-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className="text-xs font-semibold text-text-primary">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                placeholder="doctor@hospital.com"
                {...register("email")}
              />
              {errors.email && (
                <span className="text-[10px] text-danger font-medium">{errors.email.message}</span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-xs font-semibold text-text-primary">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  className="input-notion w-full pr-10 focus:border-primary text-xs dark:bg-slate-900"
                  placeholder="••••••••"
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-text-secondary hover:text-text-primary"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <span className="text-[10px] text-danger font-medium">{errors.password.message}</span>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full justify-center items-center gap-2 rounded-md bg-primary py-2 px-3 text-xs font-bold text-white shadow-sm hover:bg-secondary focus:outline-none disabled:opacity-50 cursor-pointer"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </div>
        </form>

        {/* Self-Registration Form View (Kept in DOM to maintain local state inputs) */}
        <form
          className={`mt-6 space-y-4 ${activeTab === "register" ? "block" : "hidden"}`}
          onSubmit={handleRegister}
        >
          {regSuccess ? (
            <div className="rounded-md bg-green-50 dark:bg-emerald-950/20 p-4 border border-green-200 dark:border-emerald-900/50 text-xs text-success flex items-start gap-2">
              <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block uppercase tracking-wider text-[10px]">Registration Submitted</span>
                <p className="mt-0.5 text-text-secondary">
                  Your account has been registered in the system. Please ask your System Administrator to approve your account access to make it live.
                </p>
              </div>
            </div>
          ) : (
            <>
              {regError && (
                <div className="rounded-md bg-red-50 dark:bg-red-950/20 p-3 border border-red-200 dark:border-red-900/50 text-xs text-danger font-medium">
                  {regError}
                </div>
              )}

              {otpSent ? (
                /* OTP Verification fields */
                <div className="space-y-4">
                  <div className="rounded-md bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-slate-700 p-3 text-xs text-secondary leading-relaxed">
                    <span className="font-bold text-text-primary block mb-1">Email Validation Required</span>
                    An email verification OTP has been generated. Use code <span className="font-bold text-primary dark:text-sky-400">{otpMock}</span> to validate your email address.
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">
                      6-Digit OTP Verification Code
                    </label>
                    <input
                      type="text"
                      maxLength={6}
                      required
                      placeholder="Enter 6-digit OTP code"
                      className="input-notion focus:border-primary text-xs dark:bg-slate-900 text-center font-bold tracking-widest text-lg py-2.5"
                      value={otpVal}
                      onChange={(e) => setOtpVal(e.target.value)}
                    />
                  </div>

                  <div className="flex justify-between items-center pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setOtpSent(false);
                        setOtpVal("");
                        setOtpMock("");
                      }}
                      className="text-xs text-text-secondary hover:underline cursor-pointer"
                    >
                      Change registration details
                    </button>
                  </div>
                </div>
              ) : (
                /* Standard self-registration fields */
                <div className="space-y-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">Full Name</label>
                    <input
                      type="text"
                      required
                      className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                      placeholder="Dr. Sabarno Baral"
                      value={regName}
                      onChange={(e) => setRegName(e.target.value)}
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">Email Address</label>
                    <input
                      type="email"
                      required
                      className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                      placeholder="sbaral@hospital.com"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">Phone Number (Optional)</label>
                    <input
                      type="text"
                      className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                      placeholder="+91 98765 43210"
                      value={regPhone}
                      onChange={(e) => setRegPhone(e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-text-secondary uppercase">Role Title</label>
                      <select
                        required
                        className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                        value={regRoleId}
                        onChange={(e) => setRegRoleId(e.target.value)}
                      >
                        <option value="">-- Role --</option>
                        {roles.map((r: any) => (
                          <option key={r.id} value={r.id}>
                            {r.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-[10px] font-bold text-text-secondary uppercase">Password</label>
                      <input
                        type="password"
                        required
                        className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                        placeholder="Min 8 chars"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={registering}
                  className="flex w-full justify-center items-center gap-2 rounded-md bg-primary py-2 px-3 text-xs font-bold text-white shadow-sm hover:bg-secondary focus:outline-none disabled:opacity-50 cursor-pointer"
                >
                  {registering ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {otpSent ? "Verifying OTP..." : "Sending OTP..."}
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4" />
                      {otpSent ? "Verify & Register Account" : "Submit Registration Request"}
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </form>

        {/* Anonymous Quick Report Form View (Kept in DOM to maintain inputs) */}
        <form
          className={`mt-6 space-y-4 ${activeTab === "report" ? "block" : "hidden"}`}
          onSubmit={handleReportSubmit}
        >
          {reportSuccess ? (
            <div className="rounded-md bg-green-50 dark:bg-emerald-950/20 p-4 border border-green-200 dark:border-emerald-900/50 text-xs text-success flex items-start gap-2">
              <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block uppercase tracking-wider text-[10px]">Report Logged</span>
                <p className="mt-0.5 text-text-secondary">
                  Thank you for reporting. The safety issue has been compiled with photo evidence & GPS coordinates and submitted to the System Administrators for review.
                </p>
              </div>
            </div>
          ) : (
            <>
              {reportError && (
                <div className="rounded-md bg-red-50 dark:bg-red-950/20 p-3 border border-red-200 dark:border-red-900/50 text-xs text-danger font-medium">
                  {reportError}
                </div>
              )}

              <div className="space-y-3">
                <div className="flex flex-col gap-1">
                  <label className="text-[10px] font-bold text-text-secondary uppercase">
                    Describe the Safety Gap / Non-Conformance
                  </label>
                  <textarea
                    required
                    rows={3}
                    className="input-notion focus:border-primary text-xs dark:bg-slate-900"
                    placeholder="Describe what you observed (e.g., Blocked fire exit on 4th floor, Hand sanitizer empty in ICU Ward B)..."
                    value={reportDesc}
                    onChange={(e) => setReportDesc(e.target.value)}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3 items-center">
                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase flex items-center gap-1">
                      <Camera className="h-3 w-3" />
                      Photo Proof
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      required
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setReportFile(e.target.files[0]);
                          triggerGpsCapture();
                        }
                      }}
                      className="text-[10px] file:mr-2 file:py-1 file:px-2 file:rounded file:border file:border-border file:text-[10px] file:font-semibold file:bg-slate-50 dark:file:bg-slate-800 hover:file:bg-hover cursor-pointer"
                    />
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">GPS Geolocation</label>
                    {gpsStatus === "capturing" && (
                      <span className="flex items-center gap-1 text-[10px] text-text-secondary font-semibold">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Pinpointing...
                      </span>
                    )}
                    {gpsStatus === "success" && latitude && longitude && (
                      <span className="flex items-center gap-1 text-[10px] text-success font-bold">
                        <MapPin className="h-3.5 w-3.5" />
                        {latitude.toFixed(4)}, {longitude.toFixed(4)}
                      </span>
                    )}
                    {gpsStatus === "denied" && (
                      <button
                        type="button"
                        onClick={triggerGpsCapture}
                        className="text-[10px] text-danger hover:underline text-left font-bold"
                      >
                        Location Refused - Retry?
                      </button>
                    )}
                    {gpsStatus === "idle" && (
                      <span className="text-[10px] text-text-secondary italic">Awaiting photo...</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={reporting || gpsStatus === "capturing"}
                  className="flex w-full justify-center items-center gap-2 rounded-md bg-indigo-600 py-2 px-3 text-xs font-bold text-white shadow-sm hover:bg-indigo-700 focus:outline-none disabled:opacity-50 cursor-pointer"
                >
                  {reporting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Submitting Safety Report...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      Submit Safety Report
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
