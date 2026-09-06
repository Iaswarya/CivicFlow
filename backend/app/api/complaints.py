"""
Consumer-facing complaints (referenced by the project's suggested API surface).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("", response_model=s.ComplaintOut, status_code=status.HTTP_201_CREATED, summary="File a complaint")
def create_complaint(payload: s.ComplaintCreate, db: Session = Depends(get_db),
                      current_user: m.User = Depends(get_current_user)):
    complaint = m.Complaint(submitted_by_id=current_user.id, **payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("", response_model=List[s.ComplaintOut], summary="List complaints")
def list_complaints(status_filter: Optional[str] = None, db: Session = Depends(get_db),
                     current_user: m.User = Depends(get_current_user)):
    q = db.query(m.Complaint)
    if status_filter:
        q = q.filter(m.Complaint.status == status_filter)
    return q.order_by(m.Complaint.created_at.desc()).all()


@router.put("/{complaint_id}", response_model=s.ComplaintOut, summary="Update complaint status")
def update_complaint(complaint_id: str, new_status: str, db: Session = Depends(get_db),
                      current_user: m.User = Depends(get_current_user)):
    complaint = db.query(m.Complaint).get(complaint_id)
    if not complaint:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found.")
    complaint.status = new_status
    db.commit()
    db.refresh(complaint)
    return complaint
