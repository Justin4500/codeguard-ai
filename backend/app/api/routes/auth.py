"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models import User, UserSettings
from app.schemas.auth import LoginRequest, ProfileUpdate, SignupRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = User(
        email=email,
        username=payload.username.strip(),
        full_name=(payload.full_name or "").strip() or None,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(UserSettings(user_id=user.id))
    db.commit()

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if payload.username is not None:
        user.username = payload.username.strip()
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or None
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
