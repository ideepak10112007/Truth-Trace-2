"""API schemas = the single typed contract the dashboard consumes.

Every panel in the prototype maps to a field here. `data_source` markers
("demo" | "indexed" | "live") let the UI badge simulated vs. real results.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

DataSource = Literal["demo", "indexed", "live"]
Severity = Literal["high", "medium", "low"]


# ---- building blocks ----------------------------------------------------
class Signal(BaseModel):
    name: str
    score: float  # 0..1


class TemporalPoint(BaseModel):
    t: float          # seconds
    score: float      # 0..1 manipulation score


class AnomalyBand(BaseModel):
    start: float
    end: float
    label: str = "Anomaly Detected"


class MatchItem(BaseModel):
    id: str
    label: str
    source_handle: Optional[str] = None
    platform: Optional[str] = None
    similarity: float          # 0..100
    hamming_distance: Optional[int] = None
    url: Optional[str] = None
    first_seen_at: Optional[str] = None


class PropagationNode(BaseModel):
    id: str
    handle: str
    platform: Optional[str] = None
    timestamp: str             # display, e.g. "10:12 AM"
    label: Optional[str] = None
    is_origin: bool = False
    is_group: bool = False     # e.g. "+3 More Accounts"


class PropagationEdge(BaseModel):
    source: str
    target: str


class TimelineEvent(BaseModel):
    timestamp: str
    handle: str
    action: str                # "First Seen" | "Shared" | ...


# ---- analysis sections --------------------------------------------------
class AIDetection(BaseModel):
    label: str                 # "AI Manipulated"
    score: float               # 0..100
    severity: Severity = "high"
    data_source: DataSource = "demo"


class ManipulationAnalysis(BaseModel):
    type: str                  # "Face Swap" (display label, kept for compat)
    score: float               # 0..100
    signals: list[Signal] = []
    temporal: list[TemporalPoint] = []
    anomaly: Optional[AnomalyBand] = None
    heatmap_ref: Optional[str] = None
    data_source: DataSource = "demo"
    # Structured classification (Phase 5): one of a fixed taxonomy, with
    # confidence + supporting evidence. `type` above remains the short
    # display label already used by existing dashboard components;
    # `classification` is the taxonomy key, e.g. "ai_face_swap".
    classification: Optional[str] = None
    classification_confidence: Optional[float] = None  # 0..100
    classification_evidence: list[str] = []
    classification_method: str = "heuristic_demo"  # never claims a real ML classifier


class Originality(BaseModel):
    label: str                 # "Not Original"
    score: float               # 0..100
    data_source: DataSource = "demo"
    # Structured assessment (Phase 5): confidence + evidence grounded in
    # real signals (hash/similarity/metadata/provenance) where available.
    confidence: Optional[float] = None       # 0..100
    evidence: list[str] = []
    assessment_method: str = "heuristic_demo"


class Fingerprint(BaseModel):
    phash: Optional[str] = None
    phash_display: Optional[str] = None
    matches_found: int = 0
    similarity: float = 0
    matches: list[MatchItem] = []
    data_source: DataSource = "indexed"
    # Method transparency: what kind of fingerprint this actually is.
    # "perceptual_phash" (image), "perceptual_video_frames" (real ffmpeg
    # frame sampling + pHash), or "content_hash_fallback" (ffmpeg
    # unavailable — SHA-256-derived identifier, NOT perceptually similar).
    method: str = "perceptual_phash"
    frame_count: Optional[int] = None


class Provenance(BaseModel):
    metadata: str = "Unknown"
    c2pa: str = "Not Found"
    recording_device: str = "Unknown"
    software: str = "Unknown"
    creation_time: str = "Unavailable"
    data_source: DataSource = "live"


class ConfidenceBreakdown(BaseModel):
    ai_detection: float
    manipulation: float
    provenance: float
    similarity: float
    consistency: float


class Explainability(BaseModel):
    verdict: str               # "AI Manipulated"
    reasons: list[str] = []
    confidence: ConfidenceBreakdown


class DisseminationEvent(BaseModel):
    """One hop in the dissemination path, grounded in a real match result."""
    evidence_id: str
    source_handle: Optional[str] = None
    platform: Optional[str] = None
    timestamp: Optional[str] = None
    url: Optional[str] = None
    similarity: float                 # 0..100, from real fingerprint matching
    hamming_distance: Optional[int] = None
    relationship: str = "fingerprint_match"  # how this hop was linked


class Tracing(BaseModel):
    earliest_timestamp: Optional[str] = None
    earliest_source: Optional[str] = None
    earliest_platform: Optional[str] = None
    earliest_confidence: str = "Unknown"
    # Phase 5: explicit, honest caveat — this is the earliest *indexed*
    # sighting, never asserted as the absolute original source.
    earliest_is_indexed_only: bool = True
    dissemination_path: list[DisseminationEvent] = []
    nodes: list[PropagationNode] = []
    edges: list[PropagationEdge] = []
    timeline: list[TimelineEvent] = []
    data_source: DataSource = "indexed"


# ---- evidence + case ----------------------------------------------------
class EvidenceOut(BaseModel):
    id: str
    filename: str
    file_type: str
    media_kind: str
    uploaded_by: str
    uploaded_at: datetime
    duration: Optional[str] = None
    resolution: Optional[str] = None
    size_label: Optional[str] = None
    sha256: Optional[str] = None
    sha256_display: Optional[str] = None
    thumbnail_url: Optional[str] = None
    media_url: Optional[str] = None
    data_source: DataSource = "demo"

    class Config:
        from_attributes = True


class ReportInfo(BaseModel):
    id: Optional[str] = None
    status: str = "Pending"
    includes: list[str] = []


class CaseSummary(BaseModel):
    id: str
    status: str
    officer_name: str
    title: str
    forensic_score: Optional[int] = None
    confidence_label: Optional[str] = None
    filename: Optional[str] = None
    created_at: datetime
    data_source: DataSource = "demo"

    class Config:
        from_attributes = True


class CaseDetail(BaseModel):
    """Full payload for the dashboard view of one case."""
    id: str
    status: str
    officer_name: str
    title: str
    forensic_score: Optional[int] = None
    confidence_label: Optional[str] = None
    created_at: datetime
    data_source: DataSource = "demo"

    evidence: EvidenceOut
    ai_detection: AIDetection
    manipulation: ManipulationAnalysis
    originality: Originality
    fingerprint: Fingerprint
    provenance: Provenance
    explainability: Explainability
    tracing: Tracing
    report: ReportInfo


class IndexedMediaOut(BaseModel):
    """Read-only view of the local indexed evidence library (Evidence
    Library page). Not a live social-media database."""
    id: str
    label: str
    source_handle: Optional[str] = None
    platform: Optional[str] = None
    phash: Optional[str] = None
    has_frame_phashes: bool = False
    frame_count: Optional[int] = None
    sha256: Optional[str] = None
    url: Optional[str] = None
    first_seen_at: Optional[str] = None
