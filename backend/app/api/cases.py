from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.db.database import get_db
from app.models.models import Case
from app.schemas.case import CaseDetail, CaseSummary
from app.services.report import build_report_pdf
from app.services.serialize import case_detail, case_summary

router = APIRouter(prefix="/api/cases", tags=["cases"], dependencies=[Depends(require_auth)])


@router.get("", response_model=list[CaseSummary])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [case_summary(c) for c in cases]


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case or not case.evidence:
        raise HTTPException(status_code=404, detail="Case not found")
    return case_detail(case)


@router.get("/{case_id}/report.pdf")
def get_report_pdf(case_id: str, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case or not case.evidence:
        raise HTTPException(status_code=404, detail="Case not found")
    detail = case_detail(case)
    pdf_bytes = build_report_pdf(detail)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{case_id}_report.pdf"'},
    )
