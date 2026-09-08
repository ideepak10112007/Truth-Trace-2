"""Analysis pipeline: Upload -> Metadata -> SHA-256 -> Fingerprint ->
Media Analysis -> Manipulation Analysis -> Originality/Matching ->
Provenance -> Forensic Score -> Report payload.

The AI-detection / manipulation-type stage is a DETERMINISTIC, CLEARLY
LABELED SIMULATION (data_source="demo") behind `run_detector`, so a real
model can be swapped in later without touching callers. Hashing, metadata,
and pHash/Hamming similarity matching are genuinely real (data_source
"live"/"indexed").
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.hashing import format_hash_groups, phash_image, sha256_file
from app.core.metadata import extract_metadata, media_kind
from app.core.video import extract_frames, ffmpeg_available
from app.services.matching import match_phash, match_video_frames

MANIPULATION_TYPES = ["Face Swap", "AI Generation", "Traditionally Edited", "Splicing"]

# Fixed classification taxonomy (Phase 5). Keys are stable identifiers used
# in the API; `label` is the short display string reused by existing
# dashboard components via ManipulationAnalysis.type.
CLASSIFICATIONS = {
    "ai_generated": "AI Generation",
    "ai_face_swap": "Face Swap",
    "classic_editing": "Traditionally Edited",
    "copy_move": "Copy-Move Manipulation",
    "metadata_tampering": "Metadata Tampering",
    "recompression": "Recompression / Re-encoding",
    "none_detected": "No Significant Manipulation Detected",
    "suspicious_unknown": "Suspicious / Unknown",
}


def classify_manipulation(
    sha256: str, kind: str, ai_score: float, signals: list[dict],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Deterministic, clearly-labeled heuristic classifier over the fixed
    taxonomy above. This is NOT a trained ML model — it maps existing
    heuristic signals (ai_score, per-signal scores, provenance flags) onto
    one of the defined categories, with confidence + evidence bullets, so
    the result is transparent and auditable rather than presented as a
    genuine classifier verdict.
    """
    sig = {s["name"]: s["score"] for s in signals}
    evidence: list[str] = []
    key: str
    confidence: float

    # Ordered rule chain: most specific / highest-uplift signal wins.
    if ai_score < 35:
        key = "none_detected"
        confidence = 100 - ai_score
        evidence.append(f"Overall AI-manipulation indicator low ({ai_score:.0f}%)")
    elif sig.get("Eye Blink Inconsistency", 0) >= 0.7 and sig.get("Boundary Artifacts", 0) >= 0.65:
        key = "ai_face_swap"
        confidence = min(97, (sig["Eye Blink Inconsistency"] + sig["Boundary Artifacts"]) / 2 * 100 + ai_score * 0.15)
        evidence.append(f"Eye-blink inconsistency score {sig['Eye Blink Inconsistency']:.2f}")
        evidence.append(f"Facial boundary artifacts score {sig['Boundary Artifacts']:.2f}")
    elif ai_score >= 80 and sig.get("Lighting Inconsistency", 0) >= 0.75:
        key = "ai_generated"
        confidence = min(97, ai_score * 0.7 + sig["Lighting Inconsistency"] * 30)
        evidence.append(f"High AI-generation indicator ({ai_score:.0f}%)")
        evidence.append(f"Lighting inconsistency score {sig['Lighting Inconsistency']:.2f}")
    elif sig.get("Compression Ghosting", 0) >= 0.75 and provenance.get("metadata") == "Inconsistent":
        key = "recompression"
        confidence = sig["Compression Ghosting"] * 100
        evidence.append(f"Compression ghosting artifacts score {sig['Compression Ghosting']:.2f}")
        evidence.append("Inconsistent embedded metadata suggests re-encoding")
    elif provenance.get("c2pa") == "Not Found" and provenance.get("metadata") == "Inconsistent" and ai_score < 55:
        key = "metadata_tampering"
        confidence = 60 + (55 - ai_score) * 0.5
        evidence.append("No valid content-provenance (C2PA) record")
        evidence.append("Embedded metadata inconsistent with expected structure")
    elif sig.get("Color Tone Mismatch", 0) >= 0.65:
        key = "copy_move" if kind == "image" else "classic_editing"
        confidence = sig["Color Tone Mismatch"] * 100
        evidence.append(f"Color/tone mismatch across regions score {sig['Color Tone Mismatch']:.2f}")
    elif ai_score >= 45:
        key = "classic_editing"
        confidence = ai_score * 0.8
        evidence.append(f"Moderate manipulation indicators present ({ai_score:.0f}%)")
    else:
        key = "suspicious_unknown"
        confidence = 50.0
        evidence.append("Signals present but do not clearly match a known manipulation pattern")

    return {
        "classification": key,
        "label": CLASSIFICATIONS[key],
        "confidence": round(max(0.0, min(100.0, confidence)), 1),
        "evidence": evidence,
        "method": "heuristic_demo",
    }


def _stable_int(seed: str, lo: int, hi: int) -> int:
    """Deterministic pseudo-random int in [lo, hi] derived from a hash seed.
    Same file -> same demo result every time (no hidden randomness)."""
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    return lo + (h % (hi - lo + 1))


def run_detector(sha256: str, kind: str) -> dict[str, Any]:
    """Simulated AI/manipulation detector. Deterministic per-file, clearly
    tagged data_source='demo'. Replace with a real model call here later.
    """
    ai_score = _stable_int(sha256 + "ai", 34, 96)
    manip_score = _stable_int(sha256 + "manip", 40, 95)
    signal_names = ["Boundary Artifacts", "Color Tone Mismatch", "Lighting Inconsistency",
                    "Eye Blink Inconsistency", "Compression Ghosting"]
    signals = [
        {"name": n, "score": round(_stable_int(sha256 + n, 45, 92) / 100, 2)}
        for n in signal_names[:4]
    ]
    temporal = []
    if kind == "video":
        for i in range(13):
            t = float(i)
            base = _stable_int(sha256 + f"t{i}", 30, 55) / 100
            temporal.append({"t": t, "score": base})
        spike_idx = _stable_int(sha256 + "spike", 3, 9)
        temporal[spike_idx]["score"] = min(0.95, temporal[spike_idx]["score"] + 0.35)
        anomaly = {
            "start": float(spike_idx) - 0.3, "end": float(spike_idx) + 1.0,
            "label": "Anomaly Detected",
        }
    else:
        anomaly = None

    return {
        "ai_detection": {
            "label": "AI Manipulated" if ai_score >= 60 else "Likely Authentic",
            "score": ai_score,
            "severity": "high" if ai_score >= 75 else "medium" if ai_score >= 50 else "low",
            "data_source": "demo",
        },
        "manipulation_base": {
            "score": manip_score, "signals": signals,
            "temporal": temporal, "anomaly": anomaly,
            "heatmap_ref": "demo_face_heatmap", "data_source": "demo",
        },
        "ai_score": ai_score,
    }


def assess_originality(
    matches: list[dict], fp_method: str, provenance: dict[str, Any],
) -> dict[str, Any]:
    """Structured originality assessment grounded in REAL signals already
    computed upstream: fingerprint matches (real Hamming similarity),
    fingerprinting method used, and provenance metadata/C2PA state.

    Crucially: absence of a match in our local indexed library is evidence
    of "not found as a prior indexed copy", never proof the file is the
    absolute original — that claim is explicitly avoided.
    """
    evidence: list[str] = []
    best = matches[0] if matches else None

    if fp_method == "content_hash_fallback":
        evidence.append(
            "Perceptual fingerprinting unavailable for this file (fallback "
            "content hash only) — similarity matching is not comprehensive"
        )

    if best and best["similarity"] >= 90:
        label = "Not Original"
        score = best["similarity"]
        confidence = 85.0
        evidence.append(
            f"Near-identical match found in indexed library "
            f"({best['similarity']:.0f}% similarity, {best.get('source_handle') or best['label']})"
        )
    elif best:
        label = "Possibly Modified"
        score = best["similarity"]
        confidence = 55.0
        evidence.append(
            f"Partial similarity match found in indexed library "
            f"({best['similarity']:.0f}% similarity, {best.get('source_handle') or best['label']})"
        )
    else:
        label = "No Indexed Match Found"
        score = 0.0
        confidence = 40.0 if fp_method != "content_hash_fallback" else 20.0
        evidence.append("No matching content found in the local indexed evidence library")

    if provenance.get("c2pa") == "Not Found":
        evidence.append("No content-provenance (C2PA) record present to verify origin")
    if provenance.get("metadata") == "Inconsistent":
        evidence.append("Embedded metadata is inconsistent with an unmodified original")

    evidence.append(
        "Assessment is limited to the local indexed library, not a live "
        "or exhaustive search of all media in existence"
    )

    return {
        "label": label, "score": score, "confidence": round(confidence, 1),
        "evidence": evidence, "assessment_method": "heuristic_demo_with_real_matching",
        "data_source": "demo",
    }


def build_provenance(meta: dict[str, Any]) -> dict[str, Any]:
    """Provenance is REAL to the extent the file actually carries it; fields
    the file doesn't provide are reported as Unknown/Not Found, same as the
    prototype — never fabricated as "found"."""
    return {
        "metadata": "Present" if meta.get("creation_time") else "Inconsistent",
        "c2pa": "Not Found",  # no C2PA parser wired up in this prototype
        "recording_device": "Unknown",
        "software": meta.get("codec") or "Unknown",
        "creation_time": meta.get("creation_time") or "Unavailable",
        "data_source": "live",
    }


def build_explainability(ai: dict, manip: dict, prov: dict, fp: dict) -> dict[str, Any]:
    reasons = []
    if ai["score"] >= 60:
        reasons.append(f"{manip['type']} pattern detected with {'high' if ai['score'] >= 80 else 'moderate'} confidence")
    if manip["anomaly"]:
        reasons.append("Temporal inconsistency in facial movements")
    for s in manip["signals"][:2]:
        reasons.append(f"{s['name']} detected" if s["score"] >= 0.6 else f"Minor {s['name'].lower()} observed")
    if prov["c2pa"] == "Not Found":
        reasons.append("No valid C2PA provenance found")
    if fp["matches_found"] > 0:
        reasons.append("Matches found with earlier known media instances")
    consistency = round(100 - (manip["score"] * 0.3 + (100 - ai["score"]) * 0.2))
    return {
        "verdict": ai["label"],
        "reasons": reasons,
        "confidence": {
            "ai_detection": ai["score"], "manipulation": manip["score"],
            "provenance": 35 if prov["c2pa"] == "Not Found" else 80,
            "similarity": fp["similarity"], "consistency": max(0, min(100, consistency)),
        },
    }


def build_tracing(matches: list[dict]) -> dict[str, Any]:
    """Simulated propagation graph built from real match results — earliest
    timestamp comes from the (indexed, non-live) match with the earliest
    first_seen_at. Not a live social-media crawl."""
    if not matches:
        return {
            "earliest_timestamp": None, "earliest_source": None, "earliest_platform": None,
            "earliest_confidence": "Unknown", "earliest_is_indexed_only": True,
            "dissemination_path": [], "nodes": [], "edges": [], "timeline": [],
            "data_source": "indexed",
        }
    ordered = sorted(matches, key=lambda m: m.get("first_seen_at") or "")
    nodes, edges, timeline = [], [], []
    prev_id = None
    for i, m in enumerate(ordered):
        nid = f"n{i+1}"
        is_group = i >= 4
        if is_group and i == 4:
            remaining = len(ordered) - 4
            nodes.append({
                "id": nid, "handle": f"+{remaining} More Accounts", "platform": None,
                "timestamp": m.get("first_seen_at", "").split(", ")[-1] if m.get("first_seen_at") else "",
                "is_origin": False, "is_group": True,
            })
            edges.append({"source": prev_id, "target": nid})
            break
        nodes.append({
            "id": nid, "handle": m.get("source_handle") or m["label"],
            "platform": m.get("platform"),
            "timestamp": (m.get("first_seen_at", "").split(", ")[-1] if m.get("first_seen_at") else ""),
            "is_origin": i == 0, "is_group": False,
        })
        timeline.append({
            "timestamp": (m.get("first_seen_at", "").split(", ")[-1] if m.get("first_seen_at") else ""),
            "handle": m.get("source_handle") or m["label"],
            "action": "First Seen" if i == 0 else "Shared",
        })
        if prev_id:
            edges.append({"source": prev_id, "target": nid})
        prev_id = nid

    earliest = ordered[0]

    # Dissemination path: chronological hops grounded directly in real match
    # results (source/platform -> timestamp -> evidence id/url -> similarity).
    dissemination_path = [
        {
            "evidence_id": m["id"],
            "source_handle": m.get("source_handle"),
            "platform": m.get("platform"),
            "timestamp": m.get("first_seen_at"),
            "url": m.get("url"),
            "similarity": m["similarity"],
            "hamming_distance": m.get("hamming_distance"),
            "relationship": "fingerprint_match",
        }
        for m in ordered
    ]

    return {
        "earliest_timestamp": earliest.get("first_seen_at"),
        "earliest_source": earliest.get("source_handle"),
        "earliest_platform": earliest.get("platform"),
        "earliest_confidence": "High Confidence" if earliest["similarity"] >= 90 else "Medium Confidence",
        # Honest caveat: this is the earliest sighting within our local
        # indexed corpus, never asserted as the absolute original source.
        "earliest_is_indexed_only": True,
        "dissemination_path": dissemination_path,
        "nodes": nodes, "edges": edges, "timeline": timeline,
        "data_source": "indexed",
    }


def compute_forensic_score(ai: dict, manip: dict, orig: dict, fp: dict) -> int:
    score = (
        ai["score"] * 0.4 + manip["score"] * 0.25
        + orig["score"] * 0.2 + fp["similarity"] * 0.15
    )
    return round(max(0, min(100, score)))


def analyze_file(db: Session, path: Path, filename: str) -> dict[str, Any]:
    """Runs the full pipeline on a saved file and returns the payload shape
    expected by app.data.demo_case / schemas.case.CaseDetail (minus id/case
    wrapper, which the caller/route assembles)."""
    kind = media_kind(filename)
    meta = extract_metadata(path, filename)
    sha256 = sha256_file(path)

    query_phash = None
    frame_phashes: list[str] = []
    fp_method = "perceptual_phash"

    if kind == "image":
        query_phash = phash_image(path)
        matches = match_phash(db, query_phash) if query_phash else []
        fp_method = "perceptual_phash"

    elif kind == "video":
        if ffmpeg_available():
            duration_seconds = meta.get("_duration_seconds")
            frame_paths = extract_frames(path, duration_seconds, max_frames=5)
            for fp_path in frame_paths:
                h = phash_image(fp_path)
                if h:
                    frame_phashes.append(h)
            if frame_paths:
                import shutil as _shutil
                _shutil.rmtree(frame_paths[0].parent, ignore_errors=True)

            if frame_phashes:
                query_phash = frame_phashes[0]  # representative hash for display
                matches = match_video_frames(db, frame_phashes)
                fp_method = "perceptual_video_frames"
            else:
                # ffmpeg present but couldn't decode any frame (corrupt/unsupported
                # codec) — honest fallback, not a perceptual hash.
                query_phash = hashlib.sha256(sha256.encode()).hexdigest()[:16]
                matches = []
                fp_method = "content_hash_fallback"
        else:
            # No ffmpeg on this system: cannot sample real frames, so we do
            # NOT fabricate a perceptual hash. Use a clearly-labeled
            # content-identity hash (SHA-256 derived) that only detects
            # byte-identical re-uploads, not visual similarity.
            query_phash = hashlib.sha256(sha256.encode()).hexdigest()[:16]
            matches = []
            fp_method = "content_hash_fallback"
    else:
        matches = []

    fingerprint = {
        "phash": query_phash,
        "phash_display": format_hash_groups(query_phash, group=4, upper=False) if query_phash else None,
        "matches_found": len(matches),
        "similarity": matches[0]["similarity"] if matches else 0,
        "matches": matches,
        "data_source": "indexed",
        "method": fp_method,
        "frame_count": len(frame_phashes) if frame_phashes else None,
    }
    provenance = build_provenance(meta)
    detector = run_detector(sha256, kind)

    classification = classify_manipulation(
        sha256, kind, detector["ai_score"], detector["manipulation_base"]["signals"], provenance,
    )
    manipulation = {
        **detector["manipulation_base"],
        "type": classification["label"],  # short display label (backward-compatible)
        "classification": classification["classification"],
        "classification_confidence": classification["confidence"],
        "classification_evidence": classification["evidence"],
        "classification_method": classification["method"],
    }

    originality = assess_originality(matches, fp_method, provenance)

    explainability = build_explainability(detector["ai_detection"], manipulation, provenance, fingerprint)
    tracing = build_tracing(matches)
    forensic_score = compute_forensic_score(detector["ai_detection"], manipulation, originality, fingerprint)
    confidence_label = (
        "HIGH CONFIDENCE" if forensic_score >= 75
        else "MEDIUM CONFIDENCE" if forensic_score >= 45
        else "LOW CONFIDENCE"
    )

    return {
        "meta": meta,
        "sha256": sha256,
        "forensic_score": forensic_score,
        "confidence_label": confidence_label,
        "ai_detection": detector["ai_detection"],
        "manipulation": manipulation,
        "originality": originality,
        "fingerprint": fingerprint,
        "provenance": provenance,
        "explainability": explainability,
        "tracing": tracing,
    }
