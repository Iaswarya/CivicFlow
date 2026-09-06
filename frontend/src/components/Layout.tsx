import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/inspections", label: "Inspections" },
  { to: "/inspections/new", label: "New Inspection" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-ink text-white">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="font-display text-xl tracking-tight">
              CivicFlow
            </Link>
            <nav className="hidden md:flex gap-1">
              {NAV_ITEMS.map((item) => {
                const active = location.pathname === item.to;
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`px-3 py-2 rounded-sm text-sm font-medium transition-colors ${
                      active ? "bg-white/10 text-white" : "text-white/70 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-white/60 hidden sm:inline">SIH26034</span>
            {user && (
              <div className="flex items-center gap-3">
                <span className="text-white/90">{user.full_name}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand/30 border border-brand/50">
                  {user.role}
                </span>
                <button
                  onClick={() => {
                    logout();
                    navigate("/login");
                  }}
                  className="text-white/70 hover:text-white"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">{children}</main>
      <footer className="text-center text-xs text-slate/50 py-6">
        CivicFlow — Smart India Hackathon 2026 — Problem Statement SIH26034
      </footer>
    </div>
  );
}
