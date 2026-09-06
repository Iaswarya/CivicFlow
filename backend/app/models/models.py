"""
SQLAlchemy ORM models for every CivicFlow table.

Kept in one module (rather than split per the suggested file tree) because the tables
are heavily cross-referenced (Inspection -> Images -> OCRResults -> ExtractedFields ->
ComplianceChecks -> Violations) and circular imports across files would add complexity
without real benefit at this project's size. Each class is still self-contained and
documented, so splitting later (one file per model) is a mechanical refactor if needed.
"""
import enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    INSPECTOR = "INSPECTOR"
    CONSUMER = "CONSUMER"


class InspectionStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"


class CheckStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class OverallResult(str, enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_MANUAL_REVIEW = "NEEDS_MANUAL_REVIEW"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ValidationType(str, enum.Enum):
    REQUIRED_FIELD = "REQUIRED_FIELD"
    TEXT_PRESENT = "TEXT_PRESENT"
    PATTERN_MATCH = "PATTERN_MATCH"
    NUMERIC_VALUE = "NUMERIC_VALUE"
    READABILITY = "READABILITY"
    MANUAL_VERIFICATION = "MANUAL_VERIFICATION"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INSPECTOR, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inspections = relationship("Inspection", back_populates="inspector")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=gen_uuid)
    product_name = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    manufacturer = Column(String, nullable=True)
    packer = Column(String, nullable=True)
    importer = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    net_quantity = Column(String, nullable=True)
    mrp = Column(String, nullable=True)
    country_of_origin = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    manufacturing_date = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    consumer_care_details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inspections = relationship("Inspection", back_populates="product")


# ---------------------------------------------------------------------------
# Inspections
# ---------------------------------------------------------------------------

class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspector_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)

    status = Column(Enum(InspectionStatus), default=InspectionStatus.NEEDS_MANUAL_REVIEW)
    compliance_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    final_assessment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_address = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    inspector = relationship("User", back_populates="inspections")
    product = relationship("Product", back_populates="inspections")
    images = relationship("ProductImage", back_populates="inspection", cascade="all, delete-orphan")
    ocr_results = relationship("OCRResult", back_populates="inspection", cascade="all, delete-orphan")
    extracted_fields = relationship("ExtractedField", back_populates="inspection", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="inspection", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="inspection", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="inspection", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="inspection", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Product Images
# ---------------------------------------------------------------------------

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)

    image_path = Column(String, nullable=False)
    image_type = Column(String, nullable=True)  # front_label / back_label / side_label / top_bottom
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    is_blurry = Column(Boolean, default=False)
    is_low_resolution = Column(Boolean, default=False)
    quality_warning = Column(String, nullable=True)
    sharpness_score = Column(Float, nullable=True)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="images")
    ocr_results = relationship("OCRResult", back_populates="image", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# OCR Results
# ---------------------------------------------------------------------------

class OCRResult(Base):
    __tablename__ = "ocr_results"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    image_id = Column(String, ForeignKey("product_images.id"), nullable=False)

    raw_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    bounding_boxes = Column(JSON, nullable=True)  # list of {text, left, top, width, height, conf}
    engine_used = Column(String, nullable=True)  # tesseract | demo
    is_demo_mode = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="ocr_results")
    image = relationship("ProductImage", back_populates="ocr_results")


# ---------------------------------------------------------------------------
# Extracted Fields
# ---------------------------------------------------------------------------

class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    ocr_result_id = Column(String, ForeignKey("ocr_results.id"), nullable=True)

    field_name = Column(String, nullable=False)   # e.g. "net_quantity"
    field_value = Column(Text, nullable=True)      # null/unknown if not found -- never fabricated
    confidence = Column(Float, nullable=True)
    source_text = Column(Text, nullable=True)
    bounding_box = Column(JSON, nullable=True)
    extraction_method = Column(String, nullable=True)  # regex | keyword | manual

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="extracted_fields")


# ---------------------------------------------------------------------------
# Rules (configurable rule base -- NOT hard-coded legal text)
# ---------------------------------------------------------------------------

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=gen_uuid)
    rule_name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)  # applies to which product category
    description = Column(Text, nullable=True)
    field_to_check = Column(String, nullable=False)
    validation_type = Column(Enum(ValidationType), nullable=False)
    expected_pattern = Column(String, nullable=True)  # regex, when validation_type == PATTERN_MATCH
    severity = Column(Enum(Severity), default=Severity.MEDIUM)
    active = Column(Boolean, default=True)
    source_reference = Column(String, nullable=True)  # e.g. "Configured by admin -- verify against LMR 2011"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Compliance Checks
# ---------------------------------------------------------------------------

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String, ForeignKey("rules.id"), nullable=False)

    status = Column(Enum(CheckStatus), nullable=False)
    explanation = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="compliance_checks")
    rule = relationship("Rule")


# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

class Violation(Base):
    __tablename__ = "violations"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    rule_id = Column(String, ForeignKey("rules.id"), nullable=True)

    field = Column(String, nullable=True)
    severity = Column(Enum(Severity), default=Severity.MEDIUM)
    description = Column(Text, nullable=True)
    detected_value = Column(Text, nullable=True)
    expected_condition = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(Enum(CheckStatus), default=CheckStatus.MANUAL_REVIEW)

    evidence_image_id = Column(String, ForeignKey("product_images.id"), nullable=True)
    evidence_ocr_id = Column(String, ForeignKey("ocr_results.id"), nullable=True)

    resolved = Column(Boolean, default=False)
    inspector_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="violations")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=False)
    file_path = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="reports")


# ---------------------------------------------------------------------------
# Complaints (consumer-facing, referenced by the spec's /api/complaints)
# ---------------------------------------------------------------------------

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String, primary_key=True, default=gen_uuid)
    submitted_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=True)

    description = Column(Text, nullable=False)
    status = Column(String, default="OPEN")  # OPEN | IN_REVIEW | RESOLVED | REJECTED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    inspection_id = Column(String, ForeignKey("inspections.id"), nullable=True)

    action = Column(String, nullable=False)   # e.g. "EDIT_EXTRACTED_FIELD", "APPROVE_CHECK"
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="audit_logs")
