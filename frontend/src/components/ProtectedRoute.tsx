import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }: { children: React.ReactElement }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate">
        Loading CivicFlow…
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
