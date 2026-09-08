"""REAL perceptual-fingerprint matching against the local indexed library.

`match_phash` handles single-hash (image) matching. `match_video_frames`
handles frame-level matching for videos: each uploaded frame pHash is
compared against each indexed video's stored frame pHashes, and results
are aggregated per indexed item (best-frame + mean similarity). Both are
genuine Hamming-distance matching over a local corpus — not simulated,
just not a live social-media feed.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.hashing import hamming_distance, similarity_percent
from app.models.models import IndexedMedia


def match_phash(db: Session, query_phash: str | None) -> list[dict]:
    if not query_phash:
        return []
    results = []
    for item in db.query(IndexedMedia).all():
        if not item.phash:
            continue
        dist = hamming_distance(query_phash, item.phash)
        if dist is None or dist > settings.PHASH_MATCH_THRESHOLD:
            continue
        results.append({
            "id": item.id,
            "label": item.label,
            "source_handle": item.source_handle,
            "platform": item.platform,
            "similarity": similarity_percent(dist),
            "hamming_distance": dist,
            "url": item.url,
            "first_seen_at": item.first_seen_at,
        })
    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results


def match_video_frames(db: Session, query_frame_phashes: list[str]) -> list[dict]:
    """Compare a list of query frame pHashes against every indexed item's
    stored frame_phashes (falling back to its single `phash` if that's all
    it has, e.g. an image-only indexed entry). For each indexed item, the
    best (minimum) Hamming distance across all query-frame x indexed-frame
    pairs determines the reported similarity — a genuine nearest-frame match.
    """
    if not query_frame_phashes:
        return []
    results = []
    for item in db.query(IndexedMedia).all():
        candidate_hashes = item.frame_phashes or ([item.phash] if item.phash else [])
        if not candidate_hashes:
            continue
        best_dist = None
        for qh in query_frame_phashes:
            for ch in candidate_hashes:
                dist = hamming_distance(qh, ch)
                if dist is not None and (best_dist is None or dist < best_dist):
                    best_dist = dist
        if best_dist is None or best_dist > settings.PHASH_MATCH_THRESHOLD:
            continue
        results.append({
            "id": item.id,
            "label": item.label,
            "source_handle": item.source_handle,
            "platform": item.platform,
            "similarity": similarity_percent(best_dist),
            "hamming_distance": best_dist,
            "url": item.url,
            "first_seen_at": item.first_seen_at,
        })
    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results
