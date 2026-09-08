from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import generate_session_token, require_auth, verify_password
from app.db.database import get_db
from app.models.models import AuthSession, Officer
from app.schemas.auth import LoginRequest, LoginResponse, OfficerOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalize(name: str) -> str:
    return name.strip().lower()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    officer = db.query(Officer).filter(
        Officer.login_key == _normalize(payload.officer_name)
    ).first()

    # Constant-shape failure: wrong name, wrong designation, or wrong
    # password all return the same generic error — never reveal which
    # field was wrong, and never leak whether an account exists.
    if (
        not officer
        or officer.designation.strip().lower() != payload.designation.strip().lower()
        or not verify_password(payload.password, officer.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Authentication Failed — Invalid officer credentials.",
        )

    token = generate_session_token()
    db.add(AuthSession(token=token, officer_id=officer.id))
    db.commit()

    return LoginResponse(
        token=token,
        officer=OfficerOut(name=officer.name, designation=officer.designation),
    )


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        session = db.get(AuthSession, token)
        if session:
            db.delete(session)
            db.commit()
    return {"status": "logged_out"}


@router.get("/me", response_model=OfficerOut)
def me(officer: Officer = Depends(require_auth)):
    return OfficerOut(name=officer.name, designation=officer.designation)
