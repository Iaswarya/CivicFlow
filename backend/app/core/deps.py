"""
Shared FastAPI dependencies: current-user resolution + role guards.
"""
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import models as m

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> m.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception
    user = db.query(m.User).filter(m.User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*roles: str):
    def checker(user: m.User = Depends(get_current_user)) -> m.User:
        if user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(roles)}.",
            )
        return user
    return checker
