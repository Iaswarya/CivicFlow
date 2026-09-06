"""
PDF compliance report generation + download.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get(
    "/{inspection_id}/pdf",
    summary="Download the PDF compliance report",
    description="Generates (or regenerates) and returns the inspection's PDF compliance report.",
)
def get_pdf_report(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")

    try:
        file_path = report_service.generate_pdf_report(db, inspection)
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to generate PDF report: {exc}")

    db.add(m.Report(inspection_id=inspection_id, file_path=file_path))
    db.commit()

    return FileResponse(
        file_path, media_type="application/pdf",
        filename=f"CivicFlow_Report_{inspection_id[:8]}.pdf",
    )
