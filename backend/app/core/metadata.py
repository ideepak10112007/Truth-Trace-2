"""Real media metadata extraction with graceful degradation.

Images: dimensions via Pillow (always available).
Video: probed via ffprobe if present on PATH; otherwise fields degrade to
"Unknown"/None exactly as the prototype shows for unindexed device data.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def media_kind(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        return "image"
    return "unknown"


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} GB"


def _image_metadata(path: Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
        return {
            "resolution": f"{w}x{h}",
            "width": w,
            "height": h,
            "duration": None,
            "codec": im.format,
            "creation_time": None,
        }


def _ffprobe(path: Path) -> Optional[dict[str, Any]]:
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(path),
            ],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except Exception:
        return None


def _video_metadata(path: Path) -> dict[str, Any]:
    probe = _ffprobe(path)
    if not probe:
        return {
            "resolution": None, "width": None, "height": None,
            "duration": None, "_duration_seconds": None,
            "codec": "Unknown", "creation_time": None,
        }
    vstream = next(
        (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
        {},
    )
    w, h = vstream.get("width"), vstream.get("height")
    dur = probe.get("format", {}).get("duration")
    duration_label = None
    duration_seconds = None
    if dur:
        try:
            duration_seconds = float(dur)
        except (TypeError, ValueError):
            duration_seconds = None
        secs = int(float(dur))
        duration_label = f"{secs // 60:02d}:{secs % 60:02d}"
    return {
        "resolution": f"{w}x{h}" if w and h else None,
        "width": w, "height": h,
        "duration": duration_label,
        "_duration_seconds": duration_seconds,
        "codec": vstream.get("codec_name", "Unknown"),
        "creation_time": probe.get("format", {}).get("tags", {}).get("creation_time"),
    }


def extract_metadata(path: str | Path, filename: str) -> dict[str, Any]:
    p = Path(path)
    kind = media_kind(filename)
    base = {"media_kind": kind, "size_bytes": p.stat().st_size}
    base["size_label"] = human_size(base["size_bytes"])
    try:
        if kind == "image":
            base.update(_image_metadata(p))
        elif kind == "video":
            base.update(_video_metadata(p))
    except Exception:
        base.update({"resolution": None, "duration": None, "codec": "Unknown"})
    return base
