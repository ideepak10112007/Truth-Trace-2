"""Minimal auth primitives: PBKDF2 password hashing + opaque session tokens.

No new dependencies — uses Python's stdlib `hashlib`/`secrets` only, per the
constraint against adding auth frameworks for a single-officer-role login.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import AuthSession, Officer

PBKDF2_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Returns 'pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>'."""
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations_s, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def require_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Officer:
    """FastAPI dependency: rejects unauthenticated requests server-side.
    Expects 'Authorization: Bearer <token>'. Looks the token up against the
    AuthSession table on every request — logout deletes the row, which
    immediately invalidates the token (no client-only trust).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = db.get(AuthSession, token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    officer = db.get(Officer, session.officer_id)
    if not officer:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return officer
