import React, { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  inspectionsApi, imagesApi, ocrApi, extractionApi, complianceApi, reportsApi, extractErrorMessage,
} from "../api/client";
import type { Inspection, ProductImage, OCRResult, ExtractedField, ComplianceResult } from "../types";
import StatusPill from "../components/StatusPill";
import LocationPicker from "../components/LocationPicker";

const STEPS = ["Create", "Upload", "OCR", "Extract", "Compliance", "Report"] as const;

export default function InspectionWorkflow() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id;

  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [images, setImages] = useState<ProductImage[]>([]);
  const [ocrResults, setOcrResults] = useState<OCRResult[]>([]);
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);

  const loadAll = useCallback(async (inspectionId: string) => {
    try {
      const [insp, imgs, ocr, ext] = await Promise.all([
        inspectionsApi.get(inspectionId),
        imagesApi.list(inspectionId),
        ocrApi.get(inspectionId),
        extractionApi.get(inspectionId),
      ]);
      setInspection(insp.data);
      setNotes(insp.data.notes || "");
      setLat(insp.data.latitude ?? null);
      setLng(insp.data.longitude ?? null);
      setImages(imgs.data);
      setOcrResults(ocr.data);
      setFields(ext.data);
      if (insp.data.compliance_score != null) {
        const comp = await complianceApi.get(inspectionId);
        setCompliance(comp.data);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    if (id) loadAll(id);
  }, [id, loadAll]);

  async function handleCreate() {
    setBusy("create");
    setError(null);
    try {
      const res = await inspectionsApi.create({});
      navigate(`/inspections/${res.data.id}`, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!inspection || !e.target.files?.length) return;
    setBusy("upload");
    setError(null);
    try {
      for (const file of Array.from(e.target.files)) {
        await imagesApi.upload(inspection.id, file, "front_label");
      }
      const res = await imagesApi.list(inspection.id);
      setImages(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
      e.target.value = "";
    }
  }

  async function handleRunOcr() {
    if (!inspection) return;
    setBusy("ocr");
    setError(null);
    try {
      const res = await ocrApi.run(inspection.id);
      setOcrResults(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleExtract() {
    if (!inspection) return;
    setBusy("extract");
    setError(null);
    try {
      const res = await extractionApi.run(inspection.id);
      setFields(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleFieldCorrection(fieldId: string, value: string) {
    if (!inspection) return;
    try {
      const res = await extractionApi.correctField(inspection.id, fieldId, value);
      setFields((prev) => prev.map((f) => (f.id === fieldId ? res.data : f)));
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleRunCompliance() {
    if (!inspection) return;
    setBusy("compliance");
    setError(null);
    try {
      const res = await complianceApi.run(inspection.id);
      setCompliance(res.data);
      const refreshed = await inspectionsApi.get(inspection.id);
      setInspection(refreshed.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleResolveViolation(violationId: string, resolved: boolean) {
    if (!inspection) return;
    try {
      await complianceApi.reviewViolation(inspection.id, violationId, { resolved });
      const res = await complianceApi.get(inspection.id);
      setCompliance(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleSaveNotes() {
    if (!inspection) return;
    setBusy("notes");
    try {
      const res = await inspectionsApi.update(inspection.id, { notes, latitude: lat ?? undefined, longitude: lng ?? undefined });
      setInspection(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleDownloadPdf() {
    if (!inspection) return;
    setBusy("pdf");
    setError(null);
    try {
      const res = await reportsApi.downloadPdf(inspection.id);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `CivicFlow_Report_${inspection.id.slice(0, 8)}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  if (isNew) {
    return (
      <div className="max-w-lg mx-auto card p-10 text-center space-y-4">
        <h1 className="font-display text-2xl text-ink">Start a new inspection</h1>
        <p className="text-sm text-slate/60">
          You'll be able to upload label images, run OCR, review extracted declarations, and check
          compliance in the next steps.
        </p>
        {error && <p className="text-sm text-danger">{error}</p>}
        <button className="btn-primary w-full" onClick={handleCreate} disabled={busy === "create"}>
          {busy === "create" ? "Creating…" : "Create Inspection"}
        </button>
      </div>
    );
  }

  if (!inspection) return <p className="text-slate">Loading inspection…</p>;

  const currentStepIndex = compliance
    ? 4
    : fields.length > 0
    ? 3
    : ocrResults.length > 0
    ? 2
    : images.length > 0
    ? 1
    : 0;

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink">Inspection</h1>
          <p className="text-slate/50 text-xs font-mono mt-1">{inspection.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusPill status={inspection.status} />
          {inspection.risk_level && <StatusPill status={inspection.risk_level} />}
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex gap-2">
        {STEPS.map((step, idx) => (
          <div
            key={step}
            className={`flex-1 h-1.5 rounded-full ${idx <= currentStepIndex ? "bg-brand" : "bg-slate/10"}`}
          />
        ))}
      </div>

      {error && <p className="text-sm text-danger bg-danger/5 border border-danger/20 rounded-sm px-3 py-2">{error}</p>}

      {/* Step 1: Upload images */}
      <section className="card p-6 space-y-4">
        <h2 className="font-display text-lg">1 · Upload Label Images</h2>
        <label className="btn-secondary inline-block cursor-pointer">
          {busy === "upload" ? "Uploading…" : "Choose image(s)"}
          <input type="file" accept="image/*" multiple hidden onChange={handleUpload} disabled={busy === "upload"} />
        </label>
        {images.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {images.map((img) => (
              <div key={img.id} className="border border-slate/10 rounded-sm p-3 text-xs">
                <p className="font-medium text-ink">{img.image_type}</p>
                <p className="text-slate/50">{img.width ?? "?"}×{img.height ?? "?"}px</p>
                {img.quality_warning && <p className="text-warn mt-1">{img.quality_warning}</p>}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Step 2: OCR */}
      <section className="card p-6 space-y-4">
        <h2 className="font-display text-lg">2 · Run OCR</h2>
        <button className="btn-primary" onClick={handleRunOcr} disabled={images.length === 0 || busy === "ocr"}>
          {busy === "ocr" ? "Reading label…" : "Run OCR"}
        </button>
        {ocrResults.length > 0 && (
          <div className="space-y-2">
            {ocrResults.map((r) => (
              <div key={r.id} className="bg-mist rounded-sm p-3 text-xs">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium">{r.engine_used}</span>
                  {r.is_demo_mode && (
                    <span className="status-pill bg-clay/10 text-clay">DEMO MODE — sample text, not a real scan</span>
                  )}
                  {r.confidence != null && <span className="text-slate/50">confidence: {r.confidence}</span>}
                </div>
                <pre className="whitespace-pre-wrap text-slate/70 font-sans">{r.raw_text}</pre>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Step 3: Extraction */}
      <section className="card p-6 space-y-4">
        <h2 className="font-display text-lg">3 · Structured Extraction</h2>
        <button className="btn-primary" onClick={handleExtract} disabled={ocrResults.length === 0 || busy === "extract"}>
          {busy === "extract" ? "Extracting…" : "Run Extraction"}
        </button>
        {fields.length > 0 && (
          <div className="grid md:grid-cols-2 gap-3">
            {fields.map((f) => (
              <div key={f.id} className="border border-slate/10 rounded-sm p-3">
                <p className="text-xs uppercase tracking-wide text-slate/50 mb-1">{f.field_name.replace(/_/g, " ")}</p>
                <input
                  className="input text-sm"
                  defaultValue={f.field_value ?? ""}
                  placeholder="Not detected"
                  onBlur={(e) => {
                    if (e.target.value !== (f.field_value ?? "")) handleFieldCorrection(f.id, e.target.value);
                  }}
                />
                {f.confidence != null && (
                  <p className="text-[11px] text-slate/40 mt-1">
                    {f.extraction_method === "manual" ? "Manually corrected" : `confidence ${f.confidence}`}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Step 4: Compliance */}
      <section className="card p-6 space-y-4">
        <h2 className="font-display text-lg">4 · Compliance Check</h2>
        <button className="btn-primary" onClick={handleRunCompliance} disabled={fields.length === 0 || busy === "compliance"}>
          {busy === "compliance" ? "Evaluating…" : "Run Compliance Engine"}
        </button>
        {compliance && (
          <div className="space-y-6">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate/50">{compliance.score_label}</p>
                <p className="font-display text-3xl text-brand">{compliance.compliance_score}/100</p>
              </div>
              <StatusPill status={compliance.overall_result} />
              <StatusPill status={compliance.risk_level} />
            </div>

            <div>
              <h3 className="text-sm font-medium text-ink mb-2">Checks</h3>
              <div className="space-y-2">
                {compliance.checks.map((c) => (
                  <div key={c.id} className="flex items-start gap-3 text-sm border-b border-slate/5 pb-2">
                    <StatusPill status={c.status} />
                    <p className="text-slate/70 flex-1">{c.explanation}</p>
                  </div>
                ))}
              </div>
            </div>

            {compliance.violations.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-ink mb-2">Violations &amp; Evidence</h3>
                <div className="space-y-3">
                  {compliance.violations.map((v) => (
                    <div key={v.id} className="border border-danger/20 bg-danger/5 rounded-sm p-4">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">{v.field?.replace(/_/g, " ")}</span>
                        <div className="flex items-center gap-2">
                          <StatusPill status={v.severity} />
                          <StatusPill status={v.status} />
                        </div>
                      </div>
                      <p className="text-sm text-slate/70">{v.description}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <label className="text-xs flex items-center gap-1.5">
                          <input
                            type="checkbox"
                            checked={v.resolved}
                            onChange={(e) => handleResolveViolation(v.id, e.target.checked)}
                          />
                          Mark resolved (inspector reviewed)
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Location + notes */}
      <section className="card p-6 space-y-4">
        <h2 className="font-display text-lg">Location &amp; Notes</h2>
        <LocationPicker latitude={lat} longitude={lng} onChange={(la, ln) => { setLat(la); setLng(ln); }} />
        <p className="text-xs text-slate/50">Click the map to set the inspection location (optional).</p>
        <div>
          <label className="label">Manual verification notes / final assessment</label>
          <textarea className="input" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
        <button className="btn-secondary" onClick={handleSaveNotes} disabled={busy === "notes"}>
          {busy === "notes" ? "Saving…" : "Save notes & location"}
        </button>
      </section>

      {/* Report */}
      <section className="card p-6 flex items-center justify-between">
        <div>
          <h2 className="font-display text-lg">5 · Compliance Report</h2>
          <p className="text-sm text-slate/60">Generates a preliminary PDF assessment for this inspection.</p>
        </div>
        <button className="btn-primary" onClick={handleDownloadPdf} disabled={!compliance || busy === "pdf"}>
          {busy === "pdf" ? "Generating…" : "Download PDF"}
        </button>
      </section>
    </div>
  );
}
