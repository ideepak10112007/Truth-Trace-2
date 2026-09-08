"""Real PDF forensic report generation (ReportLab)."""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.schemas.case import CaseDetail

NAVY = colors.HexColor("#0e1422")
BLUE = colors.HexColor("#4f8cff")
PURPLE = colors.HexColor("#a855f7")
MUTED = colors.HexColor("#5f6b85")


def build_report_pdf(case: CaseDetail) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"TRUTH TRACE Forensic Report — {case.id}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=NAVY, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=PURPLE, fontSize=12, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13.5)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8.5, textColor=MUTED)

    story = [
        Paragraph("TRUTH TRACE — AI Digital Forensic Report", h1),
        Paragraph("Chandigarh Police · Digital Forensics Unit", small),
        Spacer(1, 10),
        Table(
            [
                ["Case ID", case.id, "Status", case.status],
                ["Officer", case.officer_name, "Report ID", case.report.id or "—"],
            ],
            colWidths=[70, 160, 70, 160],
            style=TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
                ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]),
        ),
        Paragraph("Executive Summary", h2),
        Paragraph(
            f"Evidence <b>{case.evidence.filename}</b> was assessed with an overall forensic "
            f"score of <b>{case.forensic_score}/100</b> ({case.confidence_label or 'N/A'}). "
            f"The verdict is <b>{case.explainability.verdict}</b>, with manipulation "
            f"classified as <b>{case.manipulation.type}</b> ({case.manipulation.score}% confidence).",
            body,
        ),
        Paragraph("Analysis Details", h2),
        Table(
            [
                ["AI Media Detection", f"{case.ai_detection.label} — {case.ai_detection.score}%"],
                ["Manipulation Type", f"{case.manipulation.type} — {case.manipulation.score}%"],
                ["Originality Check", f"{case.originality.label} — {case.originality.score}%"],
                ["Digital Fingerprint", f"{case.fingerprint.matches_found} matches — {case.fingerprint.similarity}% similarity"],
            ],
            colWidths=[160, 300],
            style=TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e6ef")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Paragraph("Evidence Findings", h2),
        Paragraph(f"SHA-256: <font face='Courier'>{case.evidence.sha256}</font>", small),
        Paragraph(f"Perceptual Fingerprint (pHash): <font face='Courier'>{case.fingerprint.phash_display or '—'}</font>", small),
        Paragraph(
            f"File: {case.evidence.file_type} · {case.evidence.resolution or '—'} · "
            f"{case.evidence.duration or 'N/A'} · {case.evidence.size_label or '—'}",
            small,
        ),
        Paragraph("Origin & Path Details", h2),
        Paragraph(
            f"Earliest known appearance: <b>{case.tracing.earliest_timestamp or 'Unknown'}</b> "
            f"via <b>{case.tracing.earliest_source or 'Unknown'}</b> "
            f"({case.tracing.earliest_platform or 'N/A'}), {case.tracing.earliest_confidence}.",
            body,
        ),
        Paragraph("Provenance Overview", h2),
        Table(
            [
                ["Metadata", case.provenance.metadata],
                ["C2PA Provenance", case.provenance.c2pa],
                ["Recording Device", case.provenance.recording_device],
                ["Software Used", case.provenance.software],
                ["Creation Time", case.provenance.creation_time],
            ],
            colWidths=[160, 300],
            style=TableStyle([
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e6ef")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Paragraph("Confidence Scores", h2),
        Paragraph(
            f"AI Detection {case.explainability.confidence.ai_detection}% · "
            f"Manipulation {case.explainability.confidence.manipulation}% · "
            f"Provenance {case.explainability.confidence.provenance}% · "
            f"Similarity {case.explainability.confidence.similarity}% · "
            f"Consistency {case.explainability.confidence.consistency}%",
            body,
        ),
        Paragraph("Explainable Findings", h2),
    ]
    for r in case.explainability.reasons:
        story.append(Paragraph(f"• {r}", body))

    story += [
        Spacer(1, 16),
        Paragraph(
            "Disclaimer: This report is generated by a hackathon prototype. AI-detection "
            "and manipulation-type results are simulated/demo outputs behind a pluggable "
            "detector interface; hashing, metadata, and perceptual-fingerprint matching are "
            "genuine. Origin/path tracing runs over a local indexed corpus, not a live "
            "social-media feed. Not legally conclusive forensic evidence.",
            small,
        ),
    ]

    doc.build(story)
    return buf.getvalue()
