"""User and per-user settings models."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    repositories = relationship(
        "Repository", back_populates="user", cascade="all, delete-orphan"
    )
    settings = relationship(
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ai_base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    allow_external_code: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="settings")
