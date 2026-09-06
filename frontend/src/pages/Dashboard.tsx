import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { analyticsApi, extractErrorMessage } from "../api/client";
import type { AnalyticsOverview } from "../types";

interface ViolationStat { field: string; count: number; severity_breakdown: Record<string, number> }
interface CategoryStat { category: string; total: number; average_score: number }

export default function Dashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [topViolations, setTopViolations] = useState<ViolationStat[]>([]);
  const [categories, setCategories] = useState<CategoryStat[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analyticsApi.overview(), analyticsApi.violations(), analyticsApi.categories()])
      .then(([ov, vi, cat]) => {
        setOverview(ov.data);
        setTopViolations((vi.data as ViolationStat[]).slice(0, 5));
        setCategories(cat.data as CategoryStat[]);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-slate">Loading dashboard…</p>;
  if (error) return <p className="text-danger">{error}</p>;
  if (!overview) return null;

  const stat = (label: string, value: number | string, accent = "text-ink") => (
    <div className="card p-5">
      <p className="text-xs uppercase tracking-wide text-slate/50 mb-1">{label}</p>
      <p className={`font-display text-3xl ${accent}`}>{value}</p>
    </div>
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink">Compliance Dashboard</h1>
          <p className="text-slate/60 text-sm mt-1">Live inspection statistics across all uploaded scans.</p>
        </div>
        <Link to="/inspections/new" className="btn-primary">Start Inspection</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stat("Total Inspections", overview.total_inspections)}
        {stat("Compliant", overview.compliant, "text-ok")}
        {stat("Non-Compliant", overview.non_compliant, "text-danger")}
        {stat("Manual Review", overview.manual_review, "text-clay")}
        {stat("Avg. Score", `${overview.average_score}`, "text-brand")}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="font-display text-lg mb-4">Risk Level Breakdown</h2>
          {Object.keys(overview.by_risk_level).length === 0 ? (
            <p className="text-sm text-slate/50">No scored inspections yet.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(overview.by_risk_level).map(([level, count]) => (
                <div key={level} className="flex items-center gap-3">
                  <span className="w-16 text-xs font-medium text-slate/60">{level}</span>
                  <div className="flex-1 bg-mist rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${level === "HIGH" ? "bg-danger" : level === "MEDIUM" ? "bg-warn" : "bg-ok"}`}
                      style={{ width: `${(count / overview.total_inspections) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate/60 w-6 text-right">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card p-6">
          <h2 className="font-display text-lg mb-4">Most Common Violations</h2>
          {topViolations.length === 0 ? (
            <p className="text-sm text-slate/50">No violations recorded yet.</p>
          ) : (
            <ul className="space-y-2">
              {topViolations.map((v) => (
                <li key={v.field} className="flex items-center justify-between text-sm">
                  <span className="text-ink">{v.field.replace(/_/g, " ")}</span>
                  <span className="text-slate/60">{v.count} occurrence{v.count !== 1 ? "s" : ""}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="card p-6">
        <h2 className="font-display text-lg mb-4">By Product Category</h2>
        {categories.length === 0 ? (
          <p className="text-sm text-slate/50">No categorized inspections yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate/50 border-b border-slate/10">
                <th className="py-2">Category</th>
                <th className="py-2">Inspections</th>
                <th className="py-2">Avg. Score</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((c) => (
                <tr key={c.category} className="border-b border-slate/5">
                  <td className="py-2">{c.category}</td>
                  <td className="py-2">{c.total}</td>
                  <td className="py-2">{c.average_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
