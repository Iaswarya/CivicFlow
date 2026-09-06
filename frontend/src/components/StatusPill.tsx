import React from "react";

const STYLES: Record<string, string> = {
  PASS: "bg-ok/10 text-ok",
  COMPLIANT: "bg-ok/10 text-ok",
  FAIL: "bg-danger/10 text-danger",
  NON_COMPLIANT: "bg-danger/10 text-danger",
  WARNING: "bg-warn/10 text-warn",
  NEEDS_MANUAL_REVIEW: "bg-clay/10 text-clay",
  MANUAL_REVIEW: "bg-clay/10 text-clay",
  NOT_APPLICABLE: "bg-slate/10 text-slate",
  LOW: "bg-ok/10 text-ok",
  MEDIUM: "bg-warn/10 text-warn",
  HIGH: "bg-danger/10 text-danger",
};

export default function StatusPill({ status }: { status: string }) {
  const style = STYLES[status] || "bg-slate/10 text-slate";
  return (
    <span className={`status-pill ${style}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
