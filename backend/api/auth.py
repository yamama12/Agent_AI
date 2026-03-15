from api.security import create_access_token, verify_password
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from database.db import get_db
from database.models import User
from api.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentification"])

print(hash_password("test123"))

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

    # Debugging logs
    print("DEBUG INFO:")
    print("email:", repr(email))
    print("user from DB:", user)

    print("user found:", user)

    if user:
        print("HASH LENGTH:", len(user.password))
        print("HASH VALUE:", repr(user.password))

    print("VERIFY RESULT:", verify_password(password, user.password))

    if not user or not verify_password(password, user.password):
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
        "change_password": user.changepassword == "true"
    }
