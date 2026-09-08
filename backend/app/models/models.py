"""ORM models.

Design: normalized Case / Evidence / IndexedMedia tables, with the rich
analysis payload (detection, manipulation, provenance, tracing, explainability)
stored as JSON on the Analysis row. This keeps the schema simple for a
hackathon while remaining fully migratable to PostgreSQL (JSON -> JSONB).

`data_source` on every record makes the demo/indexed vs. live distinction
explicit end-to-end, honoring the forensic-integrity rule.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # TT-2026-...
    status: Mapped[str] = mapped_column(String, default="Processing")
    officer_name: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="")
    forensic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_label: Mapped[str | None] = mapped_column(String, nullable=True)
    report_id: Mapped[str | None] = mapped_column(String, nullable=True)
    report_status: Mapped[str] = mapped_column(String, default="Pending")
    data_source: Mapped[str] = mapped_column(String, default="demo")  # demo|live
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String, default="")
    media_kind: Mapped[str] = mapped_column(String, default="unknown")
    uploaded_by: Mapped[str] = mapped_column(String, default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    duration: Mapped[str | None] = mapped_column(String, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_label: Mapped[str | None] = mapped_column(String, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    phash: Mapped[str | None] = mapped_column(String, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String, nullable=True)
    data_source: Mapped[str] = mapped_column(String, default="demo")

    case: Mapped["Case"] = relationship(back_populates="evidence")
    analysis: Mapped["Analysis"] = relationship(
        back_populates="evidence", uselist=False, cascade="all, delete-orphan"
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id"))
    # payload: ai_detection, manipulation, originality, fingerprint,
    # provenance, explainability, tracing (see schemas.CaseDetail)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    data_source: Mapped[str] = mapped_column(String, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    evidence: Mapped["Evidence"] = relationship(back_populates="analysis")


class IndexedMedia(Base):
    """The local indexed evidence library used for REAL pHash matching and
    as the corpus for (simulated) earliest-appearance / propagation tracing.
    Not a live social-media feed.
    """
    __tablename__ = "indexed_media"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, default="")
    source_handle: Mapped[str | None] = mapped_column(String, nullable=True)
    platform: Mapped[str | None] = mapped_column(String, nullable=True)
    phash: Mapped[str | None] = mapped_column(String, nullable=True)
    # For video evidence: perceptual hashes of multiple representative frames,
    # enabling frame-level similarity matching against uploaded videos.
    # None/empty for image-only indexed items.
    frame_phashes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    first_seen_at: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Officer(Base):
    """Authenticated officer account (Phase 5.2). Password is never stored
    in plaintext — only a salted PBKDF2 hash (see app.core.auth)."""
    __tablename__ = "officers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    designation: Mapped[str] = mapped_column(String)
    # Login identifier: the officer's name, normalized (lowercase, trimmed).
    login_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuthSession(Base):
    """Opaque server-side session token issued on login. No JWT/framework —
    the token is a random string looked up on each request; logout deletes
    the row, which immediately invalidates the token."""
    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    officer_id: Mapped[int] = mapped_column(ForeignKey("officers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
