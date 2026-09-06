"""
Pydantic request/response schemas. Mirrors app/models/models.py 1:1 where sensible.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.models import (
    UserRole, InspectionStatus, CheckStatus, OverallResult, RiskLevel, Severity, ValidationType,
)


# ---------- Auth / Users ----------

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.INSPECTOR


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Products ----------

class ProductCreate(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    packer: Optional[str] = None
    importer: Optional[str] = None
    address: Optional[str] = None
    net_quantity: Optional[str] = None
    mrp: Optional[str] = None
    country_of_origin: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    consumer_care_details: Optional[str] = None


class ProductUpdate(ProductCreate):
    pass


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime


# ---------- Inspections ----------

class InspectionCreate(BaseModel):
    product_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_address: Optional[str] = None
    notes: Optional[str] = None


class InspectionUpdate(BaseModel):
    status: Optional[InspectionStatus] = None
    final_assessment: Optional[str] = None
    notes: Optional[str] = None
    product_id: Optional[str] = None


class InspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inspector_id: str
    product_id: Optional[str]
    status: InspectionStatus
    compliance_score: Optional[float]
    risk_level: Optional[RiskLevel]
    final_assessment: Optional[str]
    notes: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    location_address: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------- Images ----------

class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inspection_id: str
    image_path: str
    image_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    is_blurry: bool
    is_low_resolution: bool
    quality_warning: Optional[str]
    sharpness_score: Optional[float]
    uploaded_at: datetime


# ---------- OCR ----------

class OCRResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inspection_id: str
    image_id: str
    raw_text: Optional[str]
    confidence: Optional[float]
    bounding_boxes: Optional[Any]
    engine_used: Optional[str]
    is_demo_mode: bool
    created_at: datetime


# ---------- Extraction ----------

class ExtractedFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    inspection_id: str
    field_name: str
    field_value: Optional[str]
    confidence: Optional[float]
    source_text: Optional[str]
    extraction_method: Optional[str]


class ExtractedFieldUpdate(BaseModel):
    field_value: str


# ---------- Rules ----------

class RuleCreate(BaseModel):
    rule_name: str
    category: str
    description: Optional[str] = None
    field_to_check: str
    validation_type: ValidationType
    expected_pattern: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    active: bool = True
    source_reference: Optional[str] = None


class RuleOut(RuleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str


# ---------- Compliance ----------

class ComplianceCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    rule_id: str
    status: CheckStatus
    explanation: Optional[str]
    confidence: Optional[float]


class ViolationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    field: Optional[str]
    severity: Severity
    description: Optional[str]
    detected_value: Optional[str]
    expected_condition: Optional[str]
    confidence: Optional[float]
    status: CheckStatus
    evidence_image_id: Optional[str]
    evidence_ocr_id: Optional[str]
    resolved: bool
    inspector_note: Optional[str]


class ComplianceResultOut(BaseModel):
    inspection_id: str
    overall_result: OverallResult
    compliance_score: float
    risk_level: RiskLevel
    score_label: str = "Preliminary Compliance Assessment"
    checks: List[ComplianceCheckOut]
    violations: List[ViolationOut]


class ViolationReview(BaseModel):
    resolved: Optional[bool] = None
    inspector_note: Optional[str] = None
    status: Optional[CheckStatus] = None


# ---------- Complaints ----------

class ComplaintCreate(BaseModel):
    description: str
    product_id: Optional[str] = None
    inspection_id: Optional[str] = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    description: str
    status: str
    product_id: Optional[str]
    inspection_id: Optional[str]
    created_at: datetime


# ---------- Analytics ----------

class AnalyticsOverview(BaseModel):
    total_inspections: int
    compliant: int
    non_compliant: int
    manual_review: int
    average_score: float
    by_risk_level: Dict[str, int]


class AnalyticsCategoryStat(BaseModel):
    category: str
    total: int
    average_score: float


class AnalyticsViolationStat(BaseModel):
    field: str
    count: int
    severity_breakdown: Dict[str, int]


class AnalyticsTrendPoint(BaseModel):
    date: str
    total: int
    compliant: int
    non_compliant: int
