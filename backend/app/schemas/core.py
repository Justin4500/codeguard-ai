"""Repository, scan, finding and fix schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RepositoryCreate(BaseModel):
    url: str = Field(min_length=5, max_length=500)
    branch: str | None = Field(default=None, max_length=150)
    access_token: str | None = Field(default=None, max_length=300)


class RepositoryOut(BaseModel):
    id: int
    url: str
    full_name: str
    owner: str
    name: str
    description: str | None = None
    language: str | None = None
    default_branch: str | None = None
    visibility: str
    stars: int | None = None
    size_kb: int | None = None
    last_scanned_at: datetime | None = None
    created_at: datetime
    scan_count: int = 0
    finding_count: int = 0
    critical_count: int = 0
    last_scan_status: str | None = None

    model_config = {"from_attributes": True}


class ScanOut(BaseModel):
    id: int
    repository_id: int
    branch: str | None = None
    commit_sha: str | None = None
    commit_message: str | None = None
    status: str
    stage: str | None = None
    progress: int
    total_findings: int
    files_scanned: int
    tools_used: list[Any] | None = None
    tools_skipped: list[Any] | None = None
    languages: list[Any] | None = None
    error_message: str | None = None
    ai_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanSummaryOut(ScanOut):
    repository_full_name: str | None = None


class FindingOut(BaseModel):
    id: int
    scan_id: int
    repository_id: int
    title: str
    description: str | None = None
    severity: str
    category: str
    file_path: str | None = None
    line_number: int | None = None
    end_line: int | None = None
    code_excerpt: str | None = None
    tool: str
    rule_id: str | None = None
    cwe: str | None = None
    remediation: str | None = None
    confidence: float | None = None
    status: str
    kind: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingUpdate(BaseModel):
    status: str | None = Field(default=None)
    severity: str | None = None


class FindingListOut(BaseModel):
    items: list[FindingOut]
    total: int
    page: int
    page_size: int
    severity_counts: dict[str, int] = {}


class ExplainRequest(BaseModel):
    question: str | None = Field(default=None, max_length=1000)


class ExplainOut(BaseModel):
    finding_id: int
    ai_available: bool
    provider: str | None = None
    explanation: str
    source: str  # ai | offline


class FixProposalOut(BaseModel):
    id: int
    finding_id: int
    file_path: str
    language: str | None = None
    original_code: str
    proposed_code: str
    diff: str
    explanation: str | None = None
    generator: str
    status: str
    validation_output: str | None = None
    applied_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApproveOut(BaseModel):
    proposal: FixProposalOut
    validation_output: str | None = None
    message: str
