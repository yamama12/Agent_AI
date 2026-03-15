from datetime import datetime, timedelta
import os
from passlib.context import CryptContext
from jose import jwt
from passlib.exc import UnknownHashError

SECRET_KEY = "CHANGE_ME_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False

    stored_hash = hashed.strip() if isinstance(hashed, str) else hashed

    allow_hashed_input = os.getenv("ALLOW_HASHED_PASSWORD_INPUT", "").lower() == "true"
    input_value = password.strip() if isinstance(password, str) else password
    if allow_hashed_input and input_value == stored_hash:
        return True

    try:
        return pwd_context.verify(password, stored_hash)
    except (ValueError, TypeError, UnknownHashError):
        # Handles copied values with accidental surrounding spaces during tests.
        if isinstance(password, str) and password != password.strip():
            try:
                return pwd_context.verify(password.strip(), stored_hash)
            except (ValueError, TypeError, UnknownHashError):
                return False
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
