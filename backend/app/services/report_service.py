"""
Generates the PDF compliance report using reportlab.
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)

from app.core.config import settings
from app.models import models as m


def _style_sheet():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CFTitle", fontSize=20, leading=24, spaceAfter=4,
                               textColor=colors.HexColor("#1E3A5F"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="CFSubtitle", fontSize=11, textColor=colors.HexColor("#5A6B7A"),
                               spaceAfter=14))
    styles.add(ParagraphStyle(name="CFSection", fontSize=13, spaceBefore=14, spaceAfter=6,
                               textColor=colors.HexColor("#1E3A5F"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="CFBody", fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name="CFNote", fontSize=8.5, leading=12, textColor=colors.HexColor("#8A8A8A")))
    return styles


def generate_pdf_report(db_session, inspection: m.Inspection) -> str:
    styles = _style_sheet()
    out_dir = settings.REPORTS_DIR
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, f"CivicFlow_Report_{inspection.id}.pdf")

    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    story.append(Paragraph("CivicFlow", styles["CFTitle"]))
    story.append(Paragraph(
        "Smart India Hackathon 2026 &nbsp;|&nbsp; Problem Statement SIH26034<br/>"
        "Preliminary Packaged Commodity Compliance Assessment",
        styles["CFSubtitle"],
    ))

    product = inspection.product
    meta_rows = [
        ["Inspection ID", inspection.id],
        ["Date", inspection.created_at.strftime("%d %b %Y, %H:%M") if inspection.created_at else "-"],
        ["Inspector", inspection.inspector.full_name if inspection.inspector else "-"],
        ["Product", product.product_name if product and product.product_name else "Unspecified"],
        ["Category", product.category if product and product.category else "Unspecified"],
    ]
    meta_table = Table(meta_rows, colWidths=[110, 360])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5A6B7A")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)

    if product:
        story.append(Paragraph("Extracted Product Declarations", styles["CFSection"]))
        field_rows = [["Field", "Value"]]
        for label, value in [
            ("Brand", product.brand), ("Net Quantity", product.net_quantity), ("MRP", product.mrp),
            ("Manufacturer", product.manufacturer), ("Packer", product.packer),
            ("Importer", product.importer), ("Address", product.address),
            ("Country of Origin", product.country_of_origin), ("Batch Number", product.batch_number),
            ("Manufacturing Date", product.manufacturing_date), ("Expiry Date", product.expiry_date),
            ("Consumer Care", product.consumer_care_details),
        ]:
            field_rows.append([label, value or "Not detected"])
        field_table = Table(field_rows, colWidths=[150, 320])
        field_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F9")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(field_table)

    story.append(Paragraph("Compliance Checks", styles["CFSection"]))
    checks = inspection.compliance_checks
    if checks:
        check_rows = [["Rule", "Status", "Explanation"]]
        for c in checks:
            rule_name = c.rule.rule_name if c.rule else "-"
            check_rows.append([rule_name, c.status.value, Paragraph(c.explanation or "", styles["CFBody"])])
        check_table = Table(check_rows, colWidths=[110, 60, 300])
        check_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7F9")]),
        ]))
        story.append(check_table)
    else:
        story.append(Paragraph("No compliance checks have been run yet.", styles["CFBody"]))

    story.append(Paragraph("Violations", styles["CFSection"]))
    violations = inspection.violations
    if violations:
        v_rows = [["Field", "Severity", "Status", "Description"]]
        for v in violations:
            v_rows.append([
                v.field or "-", v.severity.value, v.status.value,
                Paragraph(v.description or "", styles["CFBody"]),
            ])
        v_table = Table(v_rows, colWidths=[80, 60, 70, 260])
        v_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B23A3A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF0F0")]),
        ]))
        story.append(v_table)
    else:
        story.append(Paragraph("No violations detected.", styles["CFBody"]))

    story.append(Paragraph("Preliminary Compliance Score &amp; Risk", styles["CFSection"]))
    score = inspection.compliance_score if inspection.compliance_score is not None else 0
    risk = inspection.risk_level.value if inspection.risk_level else "UNSCORED"
    story.append(Paragraph(
        f"<b>Preliminary Compliance Assessment Score:</b> {score}/100<br/>"
        f"<b>Risk Level:</b> {risk}<br/>"
        f"<b>Status:</b> {inspection.status.value}",
        styles["CFBody"],
    ))

    story.append(Paragraph("Manual Verification Notes &amp; Final Assessment", styles["CFSection"]))
    story.append(Paragraph(inspection.notes or "No manual notes recorded.", styles["CFBody"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(inspection.final_assessment or "No final assessment recorded yet.", styles["CFBody"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "This is a preliminary, AI-assisted assessment generated by CivicFlow for Smart India "
        "Hackathon 2026 demonstration purposes. It is not a legally binding determination of "
        "compliance under the Legal Metrology (Packaged Commodities) Rules, 2011. Findings "
        "requiring manual review must be verified by an authorized Legal Metrology inspector "
        "before any enforcement action.",
        styles["CFNote"],
    ))

    doc.build(story)
    return file_path
