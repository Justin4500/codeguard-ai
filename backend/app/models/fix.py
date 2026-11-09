"""Fix proposal and applied-fix models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class FixProposal(Base, TimestampMixin):
    __tablename__ = "fix_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(600), nullable=False)
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    original_code: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_code: Mapped[str] = mapped_column(Text, nullable=False)
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # template | ai
    generator: Mapped[str] = mapped_column(String(20), default="template", nullable=False)
    # proposed | approved | rejected | reverted | failed
    status: Mapped[str] = mapped_column(String(20), default="proposed", index=True, nullable=False)
    validation_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    finding = relationship("Finding", back_populates="fixes")
    applied = relationship(
        "AppliedFix", back_populates="proposal", uselist=False, cascade="all, delete-orphan"
    )


class AppliedFix(Base, TimestampMixin):
    __tablename__ = "applied_fixes"

    id: Mapped[int] = mapped_column(primary_key=True)
    fix_proposal_id: Mapped[int] = mapped_column(
        ForeignKey("fix_proposals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(600), nullable=False)
    backup_path: Mapped[str | None] = mapped_column(String(700), nullable=True)
    validation_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    reverted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    proposal = relationship("FixProposal", back_populates="applied")
