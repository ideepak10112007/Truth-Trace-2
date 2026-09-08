"""Assemble the typed CaseDetail / CaseSummary payloads from ORM rows."""
from __future__ import annotations

from app.core.hashing import format_hash_groups
from app.models.models import Case, Evidence
from app.schemas.case import (
    CaseDetail, CaseSummary, EvidenceOut,
)


def _evidence_out(ev: Evidence) -> EvidenceOut:
    return EvidenceOut(
        id=ev.id,
        filename=ev.filename,
        file_type=ev.file_type,
        media_kind=ev.media_kind,
        uploaded_by=ev.uploaded_by,
        uploaded_at=ev.uploaded_at,
        duration=ev.duration,
        resolution=ev.resolution,
        size_label=ev.size_label,
        sha256=ev.sha256,
        sha256_display=format_hash_groups(ev.sha256) if ev.sha256 else None,
        thumbnail_url=f"/api/evidence/{ev.id}/thumbnail" if ev.thumbnail_path else None,
        media_url=f"/api/evidence/{ev.id}/media" if ev.storage_path else None,
        data_source=ev.data_source,
    )


def case_summary(case: Case) -> CaseSummary:
    ev = case.evidence[0] if case.evidence else None
    return CaseSummary(
        id=case.id, status=case.status, officer_name=case.officer_name,
        title=case.title, forensic_score=case.forensic_score,
        confidence_label=case.confidence_label,
        filename=ev.filename if ev else None,
        created_at=case.created_at, data_source=case.data_source,
    )


def case_detail(case: Case) -> CaseDetail:
    ev = case.evidence[0]
    payload = ev.analysis.payload if ev.analysis else {}
    report = {
        "id": case.report_id,
        "status": case.report_status,
        "includes": payload.get("report_includes", [
            "Executive Summary", "Analysis Details", "Evidence Findings",
            "Origin & Path Details", "Confidence Scores", "Screenshots & Graphs",
        ]),
    }
    return CaseDetail(
        id=case.id, status=case.status, officer_name=case.officer_name,
        title=case.title, forensic_score=case.forensic_score,
        confidence_label=case.confidence_label, created_at=case.created_at,
        data_source=case.data_source,
        evidence=_evidence_out(ev),
        ai_detection=payload["ai_detection"],
        manipulation=payload["manipulation"],
        originality=payload["originality"],
        fingerprint=payload["fingerprint"],
        provenance=payload["provenance"],
        explainability=payload["explainability"],
        tracing=payload["tracing"],
        report=report,
    )
