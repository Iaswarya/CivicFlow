"""
OCR: run text extraction on all images belonging to an inspection.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s
from app.services import ocr_service

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


@router.post(
    "/{inspection_id}", response_model=List[s.OCRResultOut], status_code=status.HTTP_201_CREATED,
    summary="Run OCR for an inspection",
    description="Runs OCR on every uploaded image for this inspection. Falls back to a clearly-labelled "
                "DEMO MODE if the OCR engine isn't available on the server.",
)
def run_ocr_for_inspection(inspection_id: str, db: Session = Depends(get_db),
                            current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    images = db.query(m.ProductImage).filter(m.ProductImage.inspection_id == inspection_id).all()
    if not images:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No images uploaded for this inspection yet.")

    results = []
    for image in images:
        try:
            ocr_output = ocr_service.run_ocr(image.image_path)
        except Exception as exc:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"OCR failed for image {image.id}: {exc}")

        record = m.OCRResult(
            inspection_id=inspection_id,
            image_id=image.id,
            raw_text=ocr_output.get("raw_text", ""),
            confidence=ocr_output.get("confidence"),
            bounding_boxes=ocr_output.get("bounding_boxes"),
            engine_used=ocr_output.get("engine_used"),
            is_demo_mode=ocr_output.get("is_demo_mode", False),
        )
        db.add(record)
        results.append(record)

    db.commit()
    for r in results:
        db.refresh(r)
    return results


@router.get("/{inspection_id}", response_model=List[s.OCRResultOut], summary="Get OCR results for an inspection")
def get_ocr_results(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    return db.query(m.OCRResult).filter(m.OCRResult.inspection_id == inspection_id).all()
