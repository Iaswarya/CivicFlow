"""
Inspection lifecycle CRUD.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


@router.post("", response_model=s.InspectionOut, status_code=status.HTTP_201_CREATED,
             summary="Create an inspection", description="Starts a new inspection, optionally linked to an existing product.")
def create_inspection(payload: s.InspectionCreate, db: Session = Depends(get_db),
                       current_user: m.User = Depends(require_roles("ADMIN", "INSPECTOR"))):
    inspection = m.Inspection(inspector_id=current_user.id, **payload.model_dump())
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("", response_model=List[s.InspectionOut], summary="List / search inspections")
def list_inspections(
    status_filter: Optional[str] = None, risk_level: Optional[str] = None,
    category: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None,
    db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user),
):
    q = db.query(m.Inspection)
    if status_filter:
        q = q.filter(m.Inspection.status == status_filter)
    if risk_level:
        q = q.filter(m.Inspection.risk_level == risk_level)
    if category:
        q = q.join(m.Product).filter(m.Product.category == category)
    if date_from:
        q = q.filter(m.Inspection.created_at >= date_from)
    if date_to:
        q = q.filter(m.Inspection.created_at <= date_to)
    return q.order_by(m.Inspection.created_at.desc()).all()


@router.get("/{inspection_id}", response_model=s.InspectionOut, summary="Get an inspection")
def get_inspection(inspection_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")
    return inspection


@router.put("/{inspection_id}", response_model=s.InspectionOut, summary="Update an inspection")
def update_inspection(inspection_id: str, payload: s.InspectionUpdate, db: Session = Depends(get_db),
                       current_user: m.User = Depends(require_roles("ADMIN", "INSPECTOR"))):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inspection, field, value)
    db.commit()
    db.refresh(inspection)

    db.add(m.AuditLog(user_id=current_user.id, inspection_id=inspection.id,
                       action="UPDATE_INSPECTION", details=payload.model_dump(exclude_unset=True)))
    db.commit()
    return inspection


@router.delete("/{inspection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an inspection")
def delete_inspection(inspection_id: str, db: Session = Depends(get_db),
                       current_user: m.User = Depends(require_roles("ADMIN"))):
    inspection = db.query(m.Inspection).get(inspection_id)
    if not inspection:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inspection not found.")
    db.delete(inspection)
    db.commit()
