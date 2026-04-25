from api.security import create_access_token, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database.db import get_db
from database.models import User

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False

class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.strip()
    password = payload.password

    user = db.query(User).filter(
        or_(User.email == email, func.trim(User.email) == email)
    ).first()

    verify_result = verify_password(password, user.password) if user else False

    if not user or not verify_result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    
    token = create_access_token({
        "user_id": user.id,
        "role": user.roles
    })

    user.token = token
    db.commit()

    return {
        "access_token": token,
        "role": user.roles,
        "change_password": _as_bool(user.changepassword)
    }
