"""
Configurable rule base -- admin CRUD for the rules the compliance engine reads.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/rules", tags=["Rules"])


@router.post("", response_model=s.RuleOut, status_code=status.HTTP_201_CREATED,
             summary="Create a compliance rule",
             description="Adds a rule to the configurable rule base. Rules should be verified against the "
                         "actual Legal Metrology (Packaged Commodities) Rules, 2011 before activation.")
def create_rule(payload: s.RuleCreate, db: Session = Depends(get_db),
                 current_user: m.User = Depends(require_roles("ADMIN"))):
    rule = m.Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=List[s.RuleOut], summary="List rules")
def list_rules(category: Optional[str] = None, active_only: bool = False,
               db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    q = db.query(m.Rule)
    if category:
        q = q.filter(m.Rule.category == category)
    if active_only:
        q = q.filter(m.Rule.active == True)  # noqa: E712
    return q.all()


@router.put("/{rule_id}", response_model=s.RuleOut, summary="Update a rule")
def update_rule(rule_id: str, payload: s.RuleCreate, db: Session = Depends(get_db),
                 current_user: m.User = Depends(require_roles("ADMIN"))):
    rule = db.query(m.Rule).get(rule_id)
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found.")
    for field, value in payload.model_dump().items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a rule")
def delete_rule(rule_id: str, db: Session = Depends(get_db),
                 current_user: m.User = Depends(require_roles("ADMIN"))):
    rule = db.query(m.Rule).get(rule_id)
    if not rule:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rule not found.")
    db.delete(rule)
    db.commit()
