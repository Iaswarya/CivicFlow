import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { User } from "../types";
import { authApi, registerAuthExpiredHandler } from "../api/client";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem("civicflow_token");
    setUser(null);
  }, []);

  useEffect(() => {
    registerAuthExpiredHandler(logout);
  }, [logout]);

  useEffect(() => {
    const token = localStorage.getItem("civicflow_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then((res) => setUser(res.data))
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  async function login(email: string, password: string) {
    const res = await authApi.login({ email, password });
    localStorage.setItem("civicflow_token", res.data.access_token);
    setUser(res.data.user);
  }

  async function register(fullName: string, email: string, password: string, role: string) {
    const res = await authApi.register({ full_name: fullName, email, password, role });
    localStorage.setItem("civicflow_token", res.data.access_token);
    setUser(res.data.user);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
