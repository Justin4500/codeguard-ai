"""Normalized finding representation shared by all scanners."""
from __future__ import annotations

from dataclasses import dataclass, field

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}

CATEGORIES = {"bug", "security", "quality", "performance", "dependency", "lint"}

_SEVERITY_MAP = {
    "blocker": "critical",
    "critical": "critical",
    "error": "high",
    "high": "high",
    "warning": "medium",
    "warn": "medium",
    "moderate": "medium",
    "medium": "medium",
    "minor": "low",
    "low": "low",
    "note": "informational",
    "info": "informational",
    "informational": "informational",
    "style": "informational",
    "convention": "low",
    "refactor": "low",
}


def normalize_severity(value: str | None) -> str:
    if not value:
        return "medium"
    return _SEVERITY_MAP.get(str(value).strip().lower(), "medium")


@dataclass
class RawFinding:
    title: str
    severity: str
    category: str
    tool: str
    description: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    end_line: int | None = None
    code_excerpt: str | None = None
    rule_id: str | None = None
    cwe: str | None = None
    remediation: str | None = None
    confidence: float | None = None
    kind: str = "scanner"
    extra: dict = field(default_factory=dict)

    def dedupe_key(self) -> tuple:
        return (
            self.tool,
            self.rule_id or self.title,
            self.file_path,
            self.line_number,
        )


def excerpt_for(text: str, line: int | None, context: int = 2) -> str | None:
    if line is None:
        return None
    lines = text.splitlines()
    if not lines:
        return None
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    return "\n".join(lines[start:end])
