import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { inspectionsApi, extractErrorMessage } from "../api/client";
import type { Inspection } from "../types";
import StatusPill from "../components/StatusPill";

export default function Inspections() {
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    const params: Record<string, string> = {};
    if (statusFilter) params.status_filter = statusFilter;
    if (riskFilter) params.risk_level = riskFilter;
    inspectionsApi
      .list(params)
      .then((res) => setInspections(res.data))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, [statusFilter, riskFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl text-ink">Inspection History</h1>
        <Link to="/inspections/new" className="btn-primary">New Inspection</Link>
      </div>

      <div className="flex gap-3">
        <select className="input max-w-xs" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="PASS">Pass</option>
          <option value="FAIL">Fail</option>
          <option value="WARNING">Warning</option>
          <option value="NEEDS_MANUAL_REVIEW">Needs Manual Review</option>
        </select>
        <select className="input max-w-xs" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
          <option value="">All risk levels</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
        </select>
      </div>

      {error && <p className="text-danger text-sm">{error}</p>}
      {loading ? (
        <p className="text-slate">Loading…</p>
      ) : inspections.length === 0 ? (
        <div className="card p-10 text-center text-slate/60">
          No inspections match these filters yet. Start a new inspection to see it here.
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-mist">
              <tr className="text-left text-xs uppercase tracking-wide text-slate/50">
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Risk</th>
                <th className="py-3 px-4">Score</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {inspections.map((i) => (
                <tr key={i.id} className="border-t border-slate/5 hover:bg-mist/50">
                  <td className="py-3 px-4">{new Date(i.created_at).toLocaleString()}</td>
                  <td className="py-3 px-4"><StatusPill status={i.status} /></td>
                  <td className="py-3 px-4">{i.risk_level ? <StatusPill status={i.risk_level} /> : "—"}</td>
                  <td className="py-3 px-4">{i.compliance_score != null ? `${i.compliance_score}/100` : "—"}</td>
                  <td className="py-3 px-4 text-right">
                    <Link to={`/inspections/${i.id}`} className="text-brand font-medium">Open →</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
