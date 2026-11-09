"""Authentication schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=120)
    full_name: str | None = Field(default=None, max_length=200)
