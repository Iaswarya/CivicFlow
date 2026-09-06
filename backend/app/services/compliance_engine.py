"""
The compliance rule engine -- the core value of CivicFlow.

Takes extracted fields for an inspection, loads the *configurable* rules applicable to
the product's category from the database, evaluates each rule, and produces:
  - a ComplianceCheck row per rule (PASS/FAIL/WARNING/NOT_APPLICABLE/MANUAL_REVIEW)
  - a Violation row for every FAIL/WARNING/MANUAL_REVIEW, with an explanation
  - an overall preliminary compliance score and risk level

IMPORTANT (per project constraints): this engine does NOT hard-code Legal Metrology
law, section numbers, or penalties anywhere. Rules live in the `rules` table and are
meant to be populated/edited by someone who has verified them against the actual
Legal Metrology (Packaged Commodities) Rules, 2011 and any amendments -- seed_rules.py
ships a small illustrative starter set clearly marked as such. Where a rule's
validation_type is MANUAL_VERIFICATION, or where extraction confidence is too low to
trust, the engine always defers to a human via MANUAL_REVIEW rather than guessing.
"""
import re
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import models as m

LOW_CONFIDENCE_THRESHOLD = 0.5


def _evaluate_rule(rule: m.Rule, field_value: Optional[str], confidence: Optional[float]) -> Dict:
    """Returns { status, explanation, confidence } for one rule against one extracted value."""

    if rule.validation_type == m.ValidationType.MANUAL_VERIFICATION:
        return {
            "status": m.CheckStatus.MANUAL_REVIEW,
            "explanation": (
                f"'{rule.field_to_check}' requires human verification by design "
                f"(rule: {rule.rule_name}) -- this cannot be confidently automated."
            ),
            "confidence": None,
        }

    if field_value is None or field_value == "":
        return {
            "status": m.CheckStatus.FAIL if rule.validation_type == m.ValidationType.REQUIRED_FIELD
            else m.CheckStatus.MANUAL_REVIEW,
            "explanation": (
                f"Required declaration '{rule.field_to_check}' was not found in the extracted "
                f"label text. Either it is genuinely missing, or OCR/extraction could not read it -- "
                f"please verify manually against the physical label."
            ),
            "confidence": confidence,
        }

    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
        return {
            "status": m.CheckStatus.MANUAL_REVIEW,
            "explanation": (
                f"'{rule.field_to_check}' was detected as '{field_value}' but extraction confidence "
                f"({confidence:.2f}) is too low to trust automatically -- flagged for manual review."
            ),
            "confidence": confidence,
        }

    if rule.validation_type == m.ValidationType.REQUIRED_FIELD:
        return {
            "status": m.CheckStatus.PASS,
            "explanation": f"'{rule.field_to_check}' declaration is present: '{field_value}'.",
            "confidence": confidence,
        }

    if rule.validation_type == m.ValidationType.TEXT_PRESENT:
        return {
            "status": m.CheckStatus.PASS,
            "explanation": f"'{rule.field_to_check}' text was found on the label.",
            "confidence": confidence,
        }

    if rule.validation_type == m.ValidationType.PATTERN_MATCH:
        pattern = rule.expected_pattern or ""
        if pattern and re.search(pattern, field_value, re.IGNORECASE):
            return {
                "status": m.CheckStatus.PASS,
                "explanation": f"'{rule.field_to_check}' value '{field_value}' matches the expected format.",
                "confidence": confidence,
            }
        return {
            "status": m.CheckStatus.WARNING,
            "explanation": (
                f"'{rule.field_to_check}' value '{field_value}' does not match the expected pattern "
                f"configured for this rule -- please verify the declaration format manually."
            ),
            "confidence": confidence,
        }

    if rule.validation_type == m.ValidationType.NUMERIC_VALUE:
        numeric_part = re.search(r"[0-9]+(\.[0-9]+)?", field_value)
        if numeric_part:
            return {
                "status": m.CheckStatus.PASS,
                "explanation": f"'{rule.field_to_check}' contains a numeric value: '{numeric_part.group(0)}'.",
                "confidence": confidence,
            }
        return {
            "status": m.CheckStatus.WARNING,
            "explanation": f"'{rule.field_to_check}' was found ('{field_value}') but no numeric value could be parsed from it.",
            "confidence": confidence,
        }

    if rule.validation_type == m.ValidationType.READABILITY:
        # Readability is really an image-quality concern; the caller passes confidence
        # derived from OCR confidence for this field's source line, when available.
        if confidence is not None and confidence >= LOW_CONFIDENCE_THRESHOLD:
            return {
                "status": m.CheckStatus.PASS,
                "explanation": f"'{rule.field_to_check}' text appears legible in the scanned image.",
                "confidence": confidence,
            }
        return {
            "status": m.CheckStatus.MANUAL_REVIEW,
            "explanation": f"'{rule.field_to_check}' legibility could not be confidently verified from the scan.",
            "confidence": confidence,
        }

    # Fallback -- should not normally be reached.
    return {
        "status": m.CheckStatus.MANUAL_REVIEW,
        "explanation": f"Rule '{rule.rule_name}' has an unrecognized validation type; flagged for manual review.",
        "confidence": confidence,
    }


SEVERITY_WEIGHT = {m.Severity.HIGH: 25, m.Severity.MEDIUM: 12, m.Severity.LOW: 5}


def run_compliance_check(db: Session, inspection: m.Inspection, category: str) -> Dict:
    """
    Runs every active rule for `category` against the inspection's latest extracted
    fields. Persists ComplianceCheck + Violation rows. Returns a summary dict.
    """
    # Wipe any previous run for this inspection so re-running compliance is idempotent.
    db.query(m.ComplianceCheck).filter(m.ComplianceCheck.inspection_id == inspection.id).delete()
    db.query(m.Violation).filter(m.Violation.inspection_id == inspection.id).delete()

    fields_by_name: Dict[str, m.ExtractedField] = {}
    for f in db.query(m.ExtractedField).filter(m.ExtractedField.inspection_id == inspection.id).all():
        fields_by_name[f.field_name] = f

    rules: List[m.Rule] = (
        db.query(m.Rule)
        .filter(m.Rule.active == True)  # noqa: E712
        .filter((m.Rule.category == category) | (m.Rule.category == "ALL"))
        .all()
    )

    checks_created: List[m.ComplianceCheck] = []
    violations_created: List[m.Violation] = []
    score = 100.0

    if not rules:
        # No configured rules for this category -- everything needs manual review rather
        # than silently reporting "compliant" with zero checks performed.
        placeholder = m.ComplianceCheck(
            inspection_id=inspection.id,
            rule_id=None,
            status=m.CheckStatus.MANUAL_REVIEW,
            explanation=(
                f"No active compliance rules are configured for category '{category}' yet. "
                f"An admin should add rules for this category before this result can be trusted."
            ),
            confidence=None,
        )
        # rule_id is NOT NULL in the schema, so we skip persisting a check with no rule
        # and instead surface this as the overall result directly.
        return {
            "overall_result": m.OverallResult.NEEDS_MANUAL_REVIEW,
            "compliance_score": 0.0,
            "risk_level": m.RiskLevel.HIGH,
            "checks": [],
            "violations": [],
            "note": placeholder.explanation,
        }

    any_fail = False
    any_manual = False

    for rule in rules:
        extracted = fields_by_name.get(rule.field_to_check)
        field_value = extracted.field_value if extracted else None
        confidence = extracted.confidence if extracted else None

        outcome = _evaluate_rule(rule, field_value, confidence)

        check = m.ComplianceCheck(
            inspection_id=inspection.id,
            rule_id=rule.id,
            status=outcome["status"],
            explanation=outcome["explanation"],
            confidence=outcome["confidence"],
        )
        db.add(check)
        checks_created.append(check)

        if outcome["status"] == m.CheckStatus.FAIL:
            any_fail = True
            score -= SEVERITY_WEIGHT.get(rule.severity, 10)
        elif outcome["status"] == m.CheckStatus.WARNING:
            score -= SEVERITY_WEIGHT.get(rule.severity, 10) / 2
        elif outcome["status"] == m.CheckStatus.MANUAL_REVIEW:
            any_manual = True
            score -= 3  # small deduction: unverifiable items shouldn't score as perfect

        if outcome["status"] in (m.CheckStatus.FAIL, m.CheckStatus.WARNING, m.CheckStatus.MANUAL_REVIEW):
            violation = m.Violation(
                inspection_id=inspection.id,
                rule_id=rule.id,
                field=rule.field_to_check,
                severity=rule.severity,
                description=outcome["explanation"],
                detected_value=field_value,
                expected_condition=rule.description or rule.rule_name,
                confidence=outcome["confidence"],
                status=outcome["status"],
                evidence_ocr_id=extracted.ocr_result_id if extracted else None,
            )
            db.add(violation)
            violations_created.append(violation)

    score = max(0.0, min(100.0, round(score, 1)))

    if any_fail:
        overall = m.OverallResult.NON_COMPLIANT
    elif any_manual:
        overall = m.OverallResult.NEEDS_MANUAL_REVIEW
    else:
        overall = m.OverallResult.COMPLIANT

    if score >= 80 and overall == m.OverallResult.COMPLIANT:
        risk = m.RiskLevel.LOW
    elif score >= 55:
        risk = m.RiskLevel.MEDIUM
    else:
        risk = m.RiskLevel.HIGH

    inspection.compliance_score = score
    inspection.risk_level = risk
    if overall == m.OverallResult.COMPLIANT:
        inspection.status = m.InspectionStatus.PASS
    elif overall == m.OverallResult.NON_COMPLIANT:
        inspection.status = m.InspectionStatus.FAIL
    else:
        inspection.status = m.InspectionStatus.NEEDS_MANUAL_REVIEW

    db.commit()
    for c in checks_created:
        db.refresh(c)
    for v in violations_created:
        db.refresh(v)

    return {
        "overall_result": overall,
        "compliance_score": score,
        "risk_level": risk,
        "checks": checks_created,
        "violations": violations_created,
        "note": None,
    }
