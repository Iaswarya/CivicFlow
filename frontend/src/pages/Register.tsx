import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../api/client";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("INSPECTOR");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(fullName, email, password, role);
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
        </div>
        <form onSubmit={handleSubmit} className="card p-8 space-y-4">
          <h2 className="font-display text-xl text-ink">Create an account</h2>
          {error && <p className="text-sm text-danger bg-danger/5 border border-danger/20 rounded-sm px-3 py-2">{error}</p>}
          <div>
            <label className="label">Full name</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="label">Password (min 8 characters)</label>
            <input className="input" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div>
            <label className="label">Role</label>
            <select className="input" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="INSPECTOR">Inspector</option>
              <option value="ADMIN">Admin</option>
              <option value="CONSUMER">Consumer</option>
            </select>
          </div>
          <button className="btn-primary w-full" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </button>
          <p className="text-xs text-slate/60 text-center">
            Already registered? <Link to="/login" className="text-brand font-medium">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
