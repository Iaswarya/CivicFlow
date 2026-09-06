"""
Structured extraction: turn OCR text into named product fields, then optionally sync
them onto the linked Product record. Also supports inspector correction (human-in-the-loop).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s
from app.services import extraction_service

router = APIRouter(prefix="/api/extraction", tags=["Extraction"])


@router.post(
    "/{inspection_id}", response_model=List[s.ExtractedFieldOut], status_code=status.HTTP_201_CREATED,
    summary="Run structured extraction",
    description="Extracts structured product fields from the inspection's OCR text. Unfound fields are "
                "returned as null -- never guessed.",
)
def run_extraction(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    ocr_results = (
        db.query(m.OCRResult)
        .filter(m.OCRResult.inspection_id == inspection_id)
        .order_by(m.OCRResult.created_at.desc())
        .all()
    )
    if not ocr_results:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No OCR results found. Run OCR before extraction.")

    combined_text = "\n".join(r.raw_text or "" for r in ocr_results)
    most_recent_ocr_id = ocr_results[0].id

    db.query(m.ExtractedField).filter(m.ExtractedField.inspection_id == inspection_id).delete()

    field_dicts = extraction_service.extract_fields(combined_text)
    records = []
    for fd in field_dicts:
        record = m.ExtractedField(
            inspection_id=inspection_id,
            ocr_result_id=most_recent_ocr_id,
            field_name=fd["field_name"],
            field_value=fd["field_value"],
            confidence=fd["confidence"],
            source_text=fd["source_text"],
            extraction_method=fd["extraction_method"],
        )
        db.add(record)
        records.append(record)

    # Sync onto the Product record when one is linked, so the PDF report / product
    # catalogue reflect the latest scan.
    if inspection.product_id:
        product = db.query(m.Product).get(inspection.product_id)
        if product:
            values = {fd["field_name"]: fd["field_value"] for fd in field_dicts if fd["field_value"]}
            for field_name, value in values.items():
                if hasattr(product, field_name):
                    setattr(product, field_name, value)
            if not product.category:
                extracted_map = {fd["field_name"]: fd["field_value"] for fd in field_dicts}
                product.category = extraction_service.detect_category(extracted_map)

    db.commit()
    for r in records:
        db.refresh(r)
    return records


@router.get("/{inspection_id}", response_model=List[s.ExtractedFieldOut], summary="Get extracted fields")
def get_extraction(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    return db.query(m.ExtractedField).filter(m.ExtractedField.inspection_id == inspection_id).all()


@router.put(
    "/{inspection_id}/fields/{field_id}", response_model=s.ExtractedFieldOut,
    summary="Correct an extracted field (human-in-the-loop)",
)
def correct_field(inspection_id: str, field_id: str, payload: s.ExtractedFieldUpdate,
                   db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    field = db.query(m.ExtractedField).filter(
        m.ExtractedField.id == field_id, m.ExtractedField.inspection_id == inspection_id
    ).first()
    if not field:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Extracted field not found.")

    old_value = field.field_value
    field.field_value = payload.field_value
    field.extraction_method = "manual"
    field.confidence = 1.0
    db.add(m.AuditLog(
        user_id=current_user.id, inspection_id=inspection_id, action="EDIT_EXTRACTED_FIELD",
        details={"field_name": field.field_name, "old_value": old_value, "new_value": payload.field_value},
    ))
    db.commit()
    db.refresh(field)
    return field
