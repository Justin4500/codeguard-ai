"""Dashboard and settings schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    repositories: int
    scans: int
    findings: int
    critical: int
    high: int
    medium: int
    low: int
    informational: int
    resolved: int
    open: int
    recent_scans: list[Any] = []
    severity_distribution: list[dict[str, Any]] = []
    category_distribution: list[dict[str, Any]] = []
    repository_activity: list[dict[str, Any]] = []


class SettingsOut(BaseModel):
    ai_enabled: bool
    ai_provider: str | None = None
    ai_base_url: str | None = None
    ai_model: str | None = None
    allow_external_code: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    ai_enabled: bool | None = None
    ai_provider: str | None = Field(default=None, max_length=60)
    ai_base_url: str | None = Field(default=None, max_length=300)
    ai_model: str | None = Field(default=None, max_length=120)
    allow_external_code: bool | None = None


class AITestRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=500)
