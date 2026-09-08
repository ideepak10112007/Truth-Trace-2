"""Deterministic representative-frame extraction from video files, using
ffmpeg when available. This is the basis for REAL video perceptual
fingerprinting: each extracted frame gets a genuine pHash (see
core/hashing.phash_image), and the set of frame hashes is compared against
indexed video frame-hashes for genuine frame-level similarity matching.

If ffmpeg is not on PATH, `ffmpeg_available()` returns False and callers
MUST fall back to a clearly-labeled non-perceptual method (see
services/pipeline.py) rather than pretending a substitute is a real pHash.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_frames(
    video_path: str | Path,
    duration_seconds: float | None,
    max_frames: int = 5,
) -> list[Path]:
    """Extract up to `max_frames` frames at deterministic positions
    (evenly spaced fractions of the video's duration) into a temp directory.
    Returns the list of extracted frame file paths (may be shorter than
    `max_frames` if the video is very short or extraction partially fails).
    Caller is responsible for cleaning up the parent temp directory.
    """
    if not ffmpeg_available():
        return []

    video_path = Path(video_path)
    # Deterministic sample points: fixed fractions of duration, not random.
    # Avoids the very first/last frame (often black/transition frames).
    fractions = [0.1, 0.3, 0.5, 0.7, 0.9][:max_frames]

    if not duration_seconds or duration_seconds <= 0:
        duration_seconds = 10.0  # safe assumption if probing failed

    out_dir = Path(tempfile.mkdtemp(prefix="tt_frames_"))
    frames: list[Path] = []
    for i, frac in enumerate(fractions):
        ts = round(duration_seconds * frac, 2)
        out_path = out_dir / f"frame_{i}.jpg"
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(ts), "-i", str(video_path),
                    "-frames:v", "1", "-q:v", "3", str(out_path),
                ],
                capture_output=True, timeout=20,
            )
            if result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 0:
                frames.append(out_path)
        except Exception:
            continue
    return frames
