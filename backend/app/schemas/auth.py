from pydantic import BaseModel


class LoginRequest(BaseModel):
    officer_name: str
    designation: str
    password: str


class OfficerOut(BaseModel):
    name: str
    designation: str
    # Deliberately no id/password/password_hash exposed.


class LoginResponse(BaseModel):
    token: str
    officer: OfficerOut
