"""Finding model."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # critical | high | medium | low | informational
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    # bug | security | quality | performance | dependency | lint
    category: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(600), nullable=True, index=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool: Mapped[str] = mapped_column(String(60), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cwe: Mapped[str | None] = mapped_column(String(40), nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # open | confirmed | false_positive | fix_proposed | fixed | ignored
    status: Mapped[str] = mapped_column(String(20), default="open", index=True, nullable=False)
    # scanner | ai_suggestion
    kind: Mapped[str] = mapped_column(String(20), default="scanner", nullable=False)

    scan = relationship("Scan", back_populates="findings")
    repository = relationship("Repository", back_populates="findings")
    fixes = relationship(
        "FixProposal", back_populates="finding", cascade="all, delete-orphan", order_by="FixProposal.id.desc()"
    )
