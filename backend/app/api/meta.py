from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.config import settings
from app.db.database import get_db
from app.models.models import IndexedMedia
from app.schemas.case import IndexedMediaOut

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@router.get("/config")
def config():
    """Branding + the integrity disclaimer surfaced in the UI."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "org_name": settings.ORG_NAME,
        "org_unit": settings.ORG_UNIT,
        "default_case_id": "TT-2026-0818-00057",
        "disclaimer": (
            "Prototype. Detection and manipulation results shown for demo/"
            "indexed evidence are simulated and pluggable. Hashing, metadata "
            "and perceptual-fingerprint matching are real. Not a live social-"
            "media feed and not legally conclusive forensic evidence."
        ),
    }


@router.get("/indexed-media", response_model=list[IndexedMediaOut])
def list_indexed_media(db: Session = Depends(get_db), _officer=Depends(require_auth)):
    """Read-only view of the local indexed evidence library used for
    fingerprint matching. Not a live social-media database."""
    items = db.query(IndexedMedia).all()
    return [
        IndexedMediaOut(
            id=i.id, label=i.label, source_handle=i.source_handle,
            platform=i.platform, phash=i.phash,
            has_frame_phashes=bool(i.frame_phashes),
            frame_count=len(i.frame_phashes) if i.frame_phashes else None,
            sha256=i.sha256, url=i.url, first_seen_at=i.first_seen_at,
        )
        for i in items
    ]
