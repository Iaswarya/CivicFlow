"""
Admin-only user management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=List[s.UserOut], summary="List users (admin only)")
def list_users(db: Session = Depends(get_db), current_user: m.User = Depends(require_roles("ADMIN"))):
    return db.query(m.User).all()


@router.put("/{user_id}/deactivate", response_model=s.UserOut, summary="Deactivate a user (admin only)")
def deactivate_user(user_id: str, db: Session = Depends(get_db), current_user: m.User = Depends(require_roles("ADMIN"))):
    user = db.query(m.User).get(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
