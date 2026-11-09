"""Scan model."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Scan(Base, TimestampMixin):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    branch: Mapped[str | None] = mapped_column(String(150), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(60), nullable=True)
    commit_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # queued | running | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(60), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_findings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tools_used: Mapped[list | None] = mapped_column(JSON, default=list)
    tools_skipped: Mapped[list | None] = mapped_column(JSON, default=list)
    languages: Mapped[list | None] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    repository = relationship("Repository", back_populates="scans")
    findings = relationship(
        "Finding", back_populates="scan", cascade="all, delete-orphan", order_by="Finding.id"
    )
