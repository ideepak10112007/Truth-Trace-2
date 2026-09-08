"""The canonical demonstration case (TT-2026-0818-00057).

Values here reproduce the prototype exactly. This is CONTROLLED DEMO DATA:
every section is tagged data_source so the UI can badge it. Real uploads
(P4) produce their own payloads via the analysis pipeline.
"""
from datetime import datetime

CASE_ID = "TT-2026-0818-00057"
REPORT_ID = "RPT-2026-0818-00057"

SHA256_FULL = (
    "8a7d5f2c91e37b116d4f2a8c3e9b7c149e6f91c23b771a09"
    "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
)  # 64 hex chars; first 12 groups shown in the prototype header

# ---- temporal frame-analysis series (0..12s), anomaly 3.2-4.8s ----------
TEMPORAL = [
    {"t": 0.0, "score": 0.48}, {"t": 1.0, "score": 0.40},
    {"t": 2.0, "score": 0.44}, {"t": 3.0, "score": 0.58},
    {"t": 3.2, "score": 0.66}, {"t": 4.0, "score": 0.82},
    {"t": 4.8, "score": 0.71}, {"t": 5.0, "score": 0.55},
    {"t": 6.0, "score": 0.42}, {"t": 7.0, "score": 0.47},
    {"t": 8.0, "score": 0.35}, {"t": 9.0, "score": 0.44},
    {"t": 10.0, "score": 0.40}, {"t": 11.0, "score": 0.46},
    {"t": 12.0, "score": 0.38},
]

DEMO_CASE = {
    "id": CASE_ID,
    "status": "Completed",
    "officer_name": "Inspector Arjun Singh",
    "title": "evidence_video_01.mp4",
    "forensic_score": 91,
    "confidence_label": "HIGH CONFIDENCE",
    "report_id": REPORT_ID,
    "report_status": "Ready",
    "data_source": "demo",
    "evidence": {
        "id": "EV-0818-00057-01",
        "filename": "evidence_video_01.mp4",
        "file_type": "MP4",
        "media_kind": "video",
        "uploaded_by": "Inspector Arjun Singh",
        "uploaded_at": datetime(2026, 8, 18, 14, 45),
        "duration": "00:12",
        "resolution": "1920x1080",
        "size_bytes": 5054464,
        "size_label": "4.82 MB",
        "sha256": SHA256_FULL,
        "phash": "9d7f3ac1b2e87f91",
        "data_source": "demo",
    },
    "analysis": {
        "ai_detection": {
            "label": "AI Manipulated", "score": 91,
            "severity": "high", "data_source": "demo",
        },
        "manipulation": {
            "type": "Face Swap", "score": 87,
            "signals": [
                {"name": "Face Swap", "score": 0.87},
                {"name": "Eye Blink Inconsistency", "score": 0.76},
                {"name": "Boundary Artifacts", "score": 0.82},
                {"name": "Color Tone Mismatch", "score": 0.71},
                {"name": "Lighting Inconsistency", "score": 0.88},
            ],
            "temporal": TEMPORAL,
            "anomaly": {"start": 3.2, "end": 4.8, "label": "Anomaly Detected"},
            "heatmap_ref": "demo_face_heatmap",
            "data_source": "demo",
        },
        "originality": {
            "label": "Not Original", "score": 86, "data_source": "demo",
        },
        "fingerprint": {
            "phash": "9d7f3ac1b2e87f91",
            "phash_display": "9d7f 3ac1 b2e8 7f91",
            "matches_found": 5,
            "similarity": 94,
            "matches": [
                {"id": "IM-01", "label": "NewsFlash India post",
                 "source_handle": "@NewsFlash_India", "platform": "Twitter",
                 "similarity": 94, "hamming_distance": 4,
                 "first_seen_at": "18 Aug 2026, 10:12 AM"},
                {"id": "IM-02", "label": "CitizenVoice repost",
                 "source_handle": "@CitizenVoice", "platform": "Twitter",
                 "similarity": 91, "hamming_distance": 6,
                 "first_seen_at": "18 Aug 2026, 10:47 AM"},
                {"id": "IM-03", "label": "PunjabUpdates repost",
                 "source_handle": "@PunjabUpdates", "platform": "Facebook",
                 "similarity": 89, "hamming_distance": 7,
                 "first_seen_at": "18 Aug 2026, 11:02 AM"},
                {"id": "IM-04", "label": "TrueFacts share",
                 "source_handle": "@TrueFacts", "platform": "Telegram",
                 "similarity": 88, "hamming_distance": 8,
                 "first_seen_at": "18 Aug 2026, 11:43 AM"},
                {"id": "IM-05", "label": "Mirror upload",
                 "source_handle": "@ViralClipz", "platform": "Instagram",
                 "similarity": 85, "hamming_distance": 10,
                 "first_seen_at": "18 Aug 2026, 12:16 PM"},
            ],
            "data_source": "indexed",
        },
        "provenance": {
            "metadata": "Inconsistent",
            "c2pa": "Not Found",
            "recording_device": "Unknown",
            "software": "Unknown",
            "creation_time": "Unavailable",
            "data_source": "live",
        },
        "explainability": {
            "verdict": "AI Manipulated",
            "reasons": [
                "Face swap pattern detected with high confidence",
                "Temporal inconsistency in facial movements",
                "Boundary artifacts around facial region",
                "Color tone and lighting mismatch detected",
                "No valid C2PA provenance found",
                "Matches found with earlier known media instances",
            ],
            "confidence": {
                "ai_detection": 91, "manipulation": 87,
                "provenance": 35, "similarity": 94, "consistency": 58,
            },
        },
        "tracing": {
            "earliest_timestamp": "18 Aug 2026, 10:12 AM",
            "earliest_source": "@NewsFlash_India",
            "earliest_platform": "Twitter",
            "earliest_confidence": "High Confidence",
            "nodes": [
                {"id": "n1", "handle": "@NewsFlash_India", "platform": "Twitter",
                 "timestamp": "10:12 AM", "is_origin": True},
                {"id": "n2", "handle": "@CitizenVoice", "platform": "Twitter",
                 "timestamp": "10:47 AM"},
                {"id": "n3", "handle": "@PunjabUpdates", "platform": "Facebook",
                 "timestamp": "11:02 AM"},
                {"id": "n4", "handle": "@TrueFacts", "platform": "Telegram",
                 "timestamp": "11:43 AM"},
                {"id": "n5", "handle": "+3 More Accounts", "platform": None,
                 "timestamp": "12:16 PM", "is_group": True},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n1", "target": "n3"},
                {"source": "n2", "target": "n4"},
                {"source": "n3", "target": "n4"},
                {"source": "n4", "target": "n5"},
            ],
            "timeline": [
                {"timestamp": "10:12 AM", "handle": "@NewsFlash_India", "action": "First Seen"},
                {"timestamp": "10:47 AM", "handle": "@CitizenVoice", "action": "Shared"},
                {"timestamp": "11:02 AM", "handle": "@PunjabUpdates", "action": "Shared"},
                {"timestamp": "11:43 AM", "handle": "@TrueFacts", "action": "Shared"},
                {"timestamp": "12:16 PM", "handle": "+3 Accounts", "action": "Further Spread"},
            ],
            "data_source": "indexed",
        },
    },
    "report": {
        "id": REPORT_ID,
        "status": "Ready",
        "includes": [
            "Executive Summary", "Analysis Details", "Evidence Findings",
            "Origin & Path Details", "Confidence Scores", "Screenshots & Graphs",
        ],
    },
}

# Small indexed library (the local corpus real pHash matching runs against).
INDEXED_LIBRARY = [
    {"id": "IM-01", "label": "NewsFlash India post", "source_handle": "@NewsFlash_India",
     "platform": "Twitter", "phash": "9d7f3ac1b2e87f91", "first_seen_at": "18 Aug 2026, 10:12 AM"},
    {"id": "IM-02", "label": "CitizenVoice repost", "source_handle": "@CitizenVoice",
     "platform": "Twitter", "phash": "9d7f3ac1b2e87fb1", "first_seen_at": "18 Aug 2026, 10:47 AM"},
    {"id": "IM-03", "label": "PunjabUpdates repost", "source_handle": "@PunjabUpdates",
     "platform": "Facebook", "phash": "9d7f3ac1b2e83f91", "first_seen_at": "18 Aug 2026, 11:02 AM"},
    {"id": "IM-04", "label": "TrueFacts share", "source_handle": "@TrueFacts",
     "platform": "Telegram", "phash": "9d7f3ac1b2687f91", "first_seen_at": "18 Aug 2026, 11:43 AM"},
    {"id": "IM-05", "label": "Mirror upload", "source_handle": "@ViralClipz",
     "platform": "Instagram", "phash": "9d7f3ec1b2e87f91", "first_seen_at": "18 Aug 2026, 12:16 PM"},
]
