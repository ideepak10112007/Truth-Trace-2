import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.config import settings
from app.core.metadata import IMAGE_EXTS, VIDEO_EXTS, media_kind
from app.db.database import get_db
from app.models.models import Analysis, Case, Evidence
from app.schemas.case import CaseDetail
from app.services.pipeline import analyze_file
from app.services.serialize import case_detail

router = APIRouter(prefix="/api", tags=["analyze"], dependencies=[Depends(require_auth)])

ALLOWED_EXTS = IMAGE_EXTS | VIDEO_EXTS
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200MB


def _next_case_id(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    seq = db.query(Case).count() + 1
    return f"TT-{today[:4]}-{today[4:]}-{seq:05d}"


@router.post("/analyze", response_model=CaseDetail)
async def analyze(
    file: UploadFile = File(...),
    officer_name: str = Form("Inspector Arjun Singh"),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTS))}",
        )

    case_id = _next_case_id(db)
    evidence_id = f"EV-{uuid.uuid4().hex[:10]}"
    dest_dir = settings.STORAGE_DIR / case_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / (file.filename or f"{evidence_id}{ext}")

    size = 0
    try:
        with open(dest_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="File exceeds 200MB limit")
                out.write(chunk)
    except HTTPException:
        dest_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    if size == 0:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = analyze_file(db, dest_path, file.filename or dest_path.name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

    meta = result["meta"]
    case = Case(
        id=case_id, status="Completed", officer_name=officer_name,
        title=file.filename or dest_path.name,
        forensic_score=result["forensic_score"], confidence_label=result["confidence_label"],
        report_id=f"RPT-{case_id[3:]}", report_status="Ready", data_source="live",
    )
    evidence = Evidence(
        id=evidence_id, case_id=case_id, filename=file.filename or dest_path.name,
        file_type=ext.lstrip(".").upper(), media_kind=media_kind(file.filename or ""),
        uploaded_by=officer_name, uploaded_at=datetime.utcnow(),
        duration=meta.get("duration"), resolution=meta.get("resolution"),
        size_bytes=meta.get("size_bytes"), size_label=meta.get("size_label"),
        sha256=result["sha256"], phash=result["fingerprint"]["phash"],
        storage_path=str(dest_path), data_source="live",
    )
    payload = {
        "ai_detection": result["ai_detection"],
        "manipulation": result["manipulation"],
        "originality": result["originality"],
        "fingerprint": result["fingerprint"],
        "provenance": result["provenance"],
        "explainability": result["explainability"],
        "tracing": result["tracing"],
    }
    analysis = Analysis(evidence_id=evidence_id, payload=payload, data_source="live")

    db.add_all([case, evidence, analysis])
    db.commit()
    db.refresh(case)
    return case_detail(case)


@router.get("/evidence/{evidence_id}/media")
def get_media(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.get(Evidence, evidence_id)
    if not ev or not ev.storage_path or not Path(ev.storage_path).exists():
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(ev.storage_path, filename=ev.filename)
