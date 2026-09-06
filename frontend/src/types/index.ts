export type UserRole = "ADMIN" | "INSPECTOR" | "CONSUMER";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Product {
  id: string;
  product_name?: string | null;
  brand?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  packer?: string | null;
  importer?: string | null;
  address?: string | null;
  net_quantity?: string | null;
  mrp?: string | null;
  country_of_origin?: string | null;
  batch_number?: string | null;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  consumer_care_details?: string | null;
  created_at: string;
  updated_at: string;
}

export type InspectionStatus = "PASS" | "FAIL" | "WARNING" | "NEEDS_MANUAL_REVIEW";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface Inspection {
  id: string;
  inspector_id: string;
  product_id?: string | null;
  status: InspectionStatus;
  compliance_score?: number | null;
  risk_level?: RiskLevel | null;
  final_assessment?: string | null;
  notes?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  location_address?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: string;
  inspection_id: string;
  image_path: string;
  image_type?: string | null;
  width?: number | null;
  height?: number | null;
  is_blurry: boolean;
  is_low_resolution: boolean;
  quality_warning?: string | null;
  sharpness_score?: number | null;
  uploaded_at: string;
}

export interface OCRResult {
  id: string;
  inspection_id: string;
  image_id: string;
  raw_text?: string | null;
  confidence?: number | null;
  engine_used?: string | null;
  is_demo_mode: boolean;
  created_at: string;
}

export interface ExtractedField {
  id: string;
  inspection_id: string;
  field_name: string;
  field_value?: string | null;
  confidence?: number | null;
  source_text?: string | null;
  extraction_method?: string | null;
}

export type CheckStatus = "PASS" | "FAIL" | "WARNING" | "NOT_APPLICABLE" | "MANUAL_REVIEW";

export interface ComplianceCheck {
  id: string;
  rule_id: string;
  status: CheckStatus;
  explanation?: string | null;
  confidence?: number | null;
}

export interface Violation {
  id: string;
  field?: string | null;
  severity: "LOW" | "MEDIUM" | "HIGH";
  description?: string | null;
  detected_value?: string | null;
  expected_condition?: string | null;
  confidence?: number | null;
  status: CheckStatus;
  evidence_image_id?: string | null;
  evidence_ocr_id?: string | null;
  resolved: boolean;
  inspector_note?: string | null;
}

export interface ComplianceResult {
  inspection_id: string;
  overall_result: "COMPLIANT" | "NON_COMPLIANT" | "NEEDS_MANUAL_REVIEW";
  compliance_score: number;
  risk_level: RiskLevel;
  score_label: string;
  checks: ComplianceCheck[];
  violations: Violation[];
}

export interface AnalyticsOverview {
  total_inspections: number;
  compliant: number;
  non_compliant: number;
  manual_review: number;
  average_score: number;
  by_risk_level: Record<string, number>;
}
