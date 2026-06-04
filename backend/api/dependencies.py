import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from api.security import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

ALLOWED_ROLES = ["ROLE_SUPER_ADMIN", "ROLE_ADMIN"]


def _normalize_roles(raw_roles) -> list[str]:
    if raw_roles is None:
        return []
    if isinstance(raw_roles, list):
        return [str(role) for role in raw_roles]
    if isinstance(raw_roles, str):
        value = raw_roles.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(role) for role in parsed]
            return [str(parsed)]
        except json.JSONDecodeError:
            return [value]
    return [str(raw_roles)]


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        roles = _normalize_roles(payload.get("role"))
        if not any(role in ALLOWED_ROLES for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acces interdit",
            )

        payload["roles"] = roles
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire",
        )
