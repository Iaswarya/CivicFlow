import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("inspector@civicflow.demo");
  const [password, setPassword] = useState("Inspector123!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl text-white tracking-tight">CivicFlow</h1>
          <p className="text-white/50 text-sm mt-2">
            Packaged commodity compliance scanning — SIH26034
          </p>
        </div>
        <form onSubmit={handleSubmit} className="card p-8 space-y-4">
          <h2 className="font-display text-xl text-ink">Sign in</h2>
          {error && <p className="text-sm text-danger bg-danger/5 border border-danger/20 rounded-sm px-3 py-2">{error}</p>}
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="btn-primary w-full" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </button>
          <p className="text-xs text-slate/60 text-center">
            No account? <Link to="/register" className="text-brand font-medium">Register</Link>
          </p>
          <p className="text-xs text-slate/40 text-center pt-2 border-t border-slate/10">
            Demo: inspector@civicflow.demo / Inspector123! (run <code>seed_rules.py</code> first)
          </p>
        </form>
      </div>
    </div>
  );
}
