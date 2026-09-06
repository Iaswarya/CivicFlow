"""
Dashboard analytics -- real aggregate queries over inspection data (no static/fake numbers).
"""
from collections import defaultdict
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=s.AnalyticsOverview, summary="Dashboard overview stats")
def overview(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspections = db.query(m.Inspection).all()
    total = len(inspections)
    compliant = sum(1 for i in inspections if i.status == m.InspectionStatus.PASS)
    non_compliant = sum(1 for i in inspections if i.status == m.InspectionStatus.FAIL)
    manual_review = sum(1 for i in inspections if i.status == m.InspectionStatus.NEEDS_MANUAL_REVIEW)
    scored = [i.compliance_score for i in inspections if i.compliance_score is not None]
    avg_score = round(sum(scored) / len(scored), 1) if scored else 0.0

    by_risk = defaultdict(int)
    for i in inspections:
        if i.risk_level:
            by_risk[i.risk_level.value] += 1

    return s.AnalyticsOverview(
        total_inspections=total, compliant=compliant, non_compliant=non_compliant,
        manual_review=manual_review, average_score=avg_score, by_risk_level=dict(by_risk),
    )


@router.get("/violations", response_model=List[s.AnalyticsViolationStat], summary="Most common violations")
def violations(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    all_violations = db.query(m.Violation).all()
    by_field: dict = defaultdict(lambda: {"count": 0, "severity": defaultdict(int)})
    for v in all_violations:
        key = v.field or "Unknown"
        by_field[key]["count"] += 1
        by_field[key]["severity"][v.severity.value] += 1

    return [
        s.AnalyticsViolationStat(field=field, count=data["count"], severity_breakdown=dict(data["severity"]))
        for field, data in sorted(by_field.items(), key=lambda kv: kv[1]["count"], reverse=True)
    ]


@router.get("/trends", response_model=List[s.AnalyticsTrendPoint], summary="Inspection trends over time")
def trends(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    inspections = db.query(m.Inspection).order_by(m.Inspection.created_at.asc()).all()
    by_day: dict = defaultdict(lambda: {"total": 0, "compliant": 0, "non_compliant": 0})
    for i in inspections:
        if not i.created_at:
            continue
        day = i.created_at.strftime("%Y-%m-%d")
        by_day[day]["total"] += 1
        if i.status == m.InspectionStatus.PASS:
            by_day[day]["compliant"] += 1
        elif i.status == m.InspectionStatus.FAIL:
            by_day[day]["non_compliant"] += 1

    return [
        s.AnalyticsTrendPoint(date=day, total=v["total"], compliant=v["compliant"], non_compliant=v["non_compliant"])
        for day, v in sorted(by_day.items())
    ]


@router.get("/categories", response_model=List[s.AnalyticsCategoryStat], summary="Stats by product category")
def categories(db: Session = Depends(get_db), current_user: m.User = Depends(get_current_user)):
    rows = (
        db.query(m.Product.category, func.count(m.Inspection.id), func.avg(m.Inspection.compliance_score))
        .join(m.Inspection, m.Inspection.product_id == m.Product.id)
        .group_by(m.Product.category)
        .all()
    )
    return [
        s.AnalyticsCategoryStat(category=cat or "Uncategorized", total=count, average_score=round(avg or 0.0, 1))
        for cat, count, avg in rows
    ]
