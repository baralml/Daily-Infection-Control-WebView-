"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import axiosInstance from "../lib/axios";

interface RoleResponse {
  id: number;
  name: string;
  permissions: {
    modules: Record<string, string[]>;
  };
}

interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  role_id: number;
  role: RoleResponse;
}

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (module: string, action: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function initAuth() {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await axiosInstance.get("/users/me");
        setUser(res.data);
      } catch (err) {
        console.error("Auth initialization failed:", err);
        // Axios interceptor will clear and redirect to /login if refresh fails
      } finally {
        setIsLoading(false);
      }
    }
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);
      
      const res = await axiosInstance.post("/auth/login", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      
      const { access_token, user_info } = res.data;
      localStorage.setItem("access_token", access_token);
      setUser(user_info);
      
      router.push("/dashboard");
    } catch (err: any) {
      setIsLoading(false);
      throw new Error(err.response?.data?.detail || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await axiosInstance.post("/auth/logout");
    } catch (err) {
      console.error("Logout API call failed:", err);
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
      setIsLoading(false);
      router.push("/login");
    }
  };

  const refreshUser = async () => {
    try {
      const res = await axiosInstance.get("/users/me");
      setUser(res.data);
    } catch (err) {
      console.error("Failed to refresh user:", err);
    }
  };

  const hasPermission = (module: string, action: string): boolean => {
    if (!user) return false;
    if (user.role.name.toUpperCase() === "SUPER ADMIN") return true;
    
    const permissions = user.role.permissions;
    const modules = permissions.modules || permissions;
    const allowed = modules[module] || [];
    return allowed.includes(action);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasPermission,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
