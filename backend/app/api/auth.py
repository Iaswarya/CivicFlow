"""
Authentication: register, login, current-user lookup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.database.session import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=s.Token, status_code=status.HTTP_201_CREATED,
    summary="Register a new user", description="Creates a user account (ADMIN, INSPECTOR, or CONSUMER) and returns a JWT.",
)
def register(payload: s.UserRegister, db: Session = Depends(get_db)):
    if db.query(m.User).filter(m.User.email == payload.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "An account with this email already exists.")

    user = m.User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return s.Token(access_token=token, user=s.UserOut.model_validate(user))


@router.post(
    "/login", response_model=s.Token,
    summary="Log in", description="Exchanges email + password for a JWT access token.",
)
def login(payload: s.UserLogin, db: Session = Depends(get_db)):
    user = db.query(m.User).filter(m.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")

    token = create_access_token(subject=user.id, role=user.role.value)
    return s.Token(access_token=token, user=s.UserOut.model_validate(user))


@router.get(
    "/me", response_model=s.UserOut,
    summary="Get the current user", description="Returns the profile of the currently authenticated user.",
)
def me(current_user: m.User = Depends(get_current_user)):
    return current_user
