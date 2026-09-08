"""Create tables and seed the demonstration case + indexed library.

Idempotent: safe to re-run. `python -m app.data.seed` from backend/.
"""
from __future__ import annotations

from app.core.auth import hash_password
from app.data.demo_case import DEMO_CASE, INDEXED_LIBRARY
from app.db.database import Base, SessionLocal, engine
from app.models.models import Analysis, Case, Evidence, IndexedMedia, Officer

DEMO_OFFICER_NAME = "Arjun Singh"
DEMO_OFFICER_DESIGNATION = "Cyber Crime Officer"
DEMO_OFFICER_PASSWORD = "TruthTrace@2026"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        # ---- demo case ----
        if not db.get(Case, DEMO_CASE["id"]):
            c = DEMO_CASE
            ev = c["evidence"]
            case = Case(
                id=c["id"], status=c["status"], officer_name=c["officer_name"],
                title=c["title"], forensic_score=c["forensic_score"],
                confidence_label=c["confidence_label"], report_id=c["report_id"],
                report_status=c["report_status"], data_source=c["data_source"],
            )
            evidence = Evidence(
                id=ev["id"], case_id=c["id"], filename=ev["filename"],
                file_type=ev["file_type"], media_kind=ev["media_kind"],
                uploaded_by=ev["uploaded_by"], uploaded_at=ev["uploaded_at"],
                duration=ev["duration"], resolution=ev["resolution"],
                size_bytes=ev["size_bytes"], size_label=ev["size_label"],
                sha256=ev["sha256"], phash=ev["phash"], data_source=ev["data_source"],
            )
            analysis = Analysis(
                evidence_id=ev["id"], payload=c["analysis"],
                data_source=c["data_source"],
            )
            db.add_all([case, evidence, analysis])
            print(f"Seeded demo case {c['id']}")
        else:
            print("Demo case already present; skipping.")

        # ---- indexed library ----
        for item in INDEXED_LIBRARY:
            if not db.get(IndexedMedia, item["id"]):
                db.add(IndexedMedia(**item))
        db.commit()
        print(f"Indexed library: {db.query(IndexedMedia).count()} items")

        # ---- demo officer account (Phase 5.2) ----
        login_key = DEMO_OFFICER_NAME.strip().lower()
        if not db.query(Officer).filter(Officer.login_key == login_key).first():
            db.add(Officer(
                name=DEMO_OFFICER_NAME,
                designation=DEMO_OFFICER_DESIGNATION,
                login_key=login_key,
                password_hash=hash_password(DEMO_OFFICER_PASSWORD),
            ))
            db.commit()
            print(f"Seeded demo officer: {DEMO_OFFICER_NAME}")
        else:
            print("Demo officer already present; skipping.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
