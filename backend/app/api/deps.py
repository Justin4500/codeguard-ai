"""Shared FastAPI dependencies."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import User, UserSettings

bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_ERROR
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise _CREDENTIALS_ERROR
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _CREDENTIALS_ERROR from None
    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR
    return user


def get_user_settings(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserSettings:
    row = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if row is None:
        row = UserSettings(user_id=user.id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
