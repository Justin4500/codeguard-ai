"""Repository model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=False)  # owner/name
    owner: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(60), nullable=True)
    default_branch: Mapped[str | None] = mapped_column(String(150), nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    # NOTE: never returned to the frontend
    access_token: Mapped[str | None] = mapped_column(String(300), nullable=True)
    stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="repositories")
    scans = relationship(
        "Scan", back_populates="repository", cascade="all, delete-orphan", order_by="Scan.id.desc()"
    )
    findings = relationship("Finding", back_populates="repository", cascade="all, delete-orphan")
