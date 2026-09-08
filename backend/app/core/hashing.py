"""Real cryptographic + perceptual hashing utilities.

SHA-256 is genuine content integrity. pHash is a genuine perceptual
fingerprint used for similarity matching against the indexed library.
Neither of these is simulated.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional


def sha256_file(path: str | Path, chunk_size: int = 65536) -> str:
    """Compute SHA-256 of a file, streamed. Returns lowercase hex."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_hash_groups(hexhash: str, group: int = 4, upper: bool = True) -> str:
    """Format a hex hash into spaced groups, matching the prototype display."""
    s = hexhash.upper() if upper else hexhash
    return " ".join(s[i : i + group] for i in range(0, len(s), group))


def phash_image(path: str | Path) -> Optional[str]:
    """Perceptual hash (pHash) of an image. Returns 16-char hex or None.

    Videos are handled upstream by extracting a representative frame.
    """
    try:
        import imagehash
        from PIL import Image

        with Image.open(path) as im:
            return str(imagehash.phash(im))
    except Exception:
        return None


def hamming_distance(a: str, b: str) -> Optional[int]:
    """Hamming distance between two hex phash strings (bit differences)."""
    try:
        ia, ib = int(a, 16), int(b, 16)
        return bin(ia ^ ib).count("1")
    except (ValueError, TypeError):
        return None


def similarity_percent(distance: int, bits: int = 64) -> float:
    """Convert a Hamming distance to a 0-100 similarity score."""
    return round(max(0.0, (1 - distance / bits)) * 100, 1)
