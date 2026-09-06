"""
Compliance: run the rule engine for an inspection, fetch results, and let inspectors
review/resolve individual violations (human-in-the-loop).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s
from app.services import compliance_engine, extraction_service

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


@router.post(
    "/{inspection_id}", response_model=s.ComplianceResultOut,
    summary="Run the compliance rule engine",
    description="Loads applicable rules for the product's category and evaluates the inspection's "
                "extracted fields against them, producing an explainable, preliminary compliance result.",
)
def run_compliance(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    fields = db.query(m.ExtractedField).filter(m.ExtractedField.inspection_id == inspection_id).all()
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No extracted fields found. Run extraction before compliance.")

    category = None
    if inspection.product_id:
        product = db.query(m.Product).get(inspection.product_id)
        category = product.category if product else None
    if not category:
        extracted_map = {f.field_name: f.field_value for f in fields}
        category = extraction_service.detect_category(extracted_map)

    result = compliance_engine.run_compliance_check(db, inspection, category)

    return s.ComplianceResultOut(
        inspection_id=inspection_id,
        overall_result=result["overall_result"],
        compliance_score=result["compliance_score"],
        risk_level=result["risk_level"],
        checks=result["checks"],
        violations=result["violations"],
    )


@router.get("/{inspection_id}", response_model=s.ComplianceResultOut, summary="Get compliance results")
def get_compliance(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    checks = db.query(m.ComplianceCheck).filter(m.ComplianceCheck.inspection_id == inspection_id).all()
    violations = db.query(m.Violation).filter(m.Violation.inspection_id == inspection_id).all()

    if inspection.status == m.InspectionStatus.PASS:
        overall = m.OverallResult.COMPLIANT
    elif inspection.status == m.InspectionStatus.FAIL:
        overall = m.OverallResult.NON_COMPLIANT
    else:
        overall = m.OverallResult.NEEDS_MANUAL_REVIEW

    return s.ComplianceResultOut(
        inspection_id=inspection_id,
        overall_result=overall,
        compliance_score=inspection.compliance_score or 0.0,
        risk_level=inspection.risk_level or m.RiskLevel.HIGH,
        checks=checks,
        violations=violations,
    )


@router.put(
    "/{inspection_id}/violations/{violation_id}", response_model=s.ViolationOut,
    summary="Review a violation (human-in-the-loop)",
    description="Lets an inspector mark a violation resolved, add a note, or override its status.",
)
def review_violation(inspection_id: str, violation_id: str, payload: s.ViolationReview,
                      db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    violation = db.query(m.Violation).filter(
        m.Violation.id == violation_id, m.Violation.inspection_id == inspection_id
    ).first()
    if not violation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Violation not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(violation, field, value)

    db.add(m.AuditLog(user_id=current_user.id, inspection_id=inspection_id,
                       action="REVIEW_VIOLATION", details={"violation_id": violation_id, **updates}))
    db.commit()
    db.refresh(violation)
    return violation
