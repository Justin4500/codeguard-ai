"""Settings, profile and scanner-availability routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_settings
from app.core.config import settings as app_settings
from app.database.session import get_db
from app.models import User, UserSettings
from app.schemas.dashboard import AITestRequest, SettingsOut, SettingsUpdate
from app.services.ai import provider
from app.services.scanning import tools

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsOut)
def get_settings(settings_row: UserSettings = Depends(get_user_settings)) -> SettingsOut:
    return SettingsOut.model_validate(settings_row)


@router.patch("/settings", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    settings_row: UserSettings = Depends(get_user_settings),
    db: Session = Depends(get_db),
) -> SettingsOut:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings_row, key, value)
    db.add(settings_row)
    db.commit()
    db.refresh(settings_row)
    return SettingsOut.model_validate(settings_row)


@router.get("/settings/ai/status")
def ai_status(settings_row: UserSettings = Depends(get_user_settings)) -> dict:
    config = provider.resolve_config(settings_row)
    return {
        "ai_configured": config is not None,
        "ai_enabled": settings_row.ai_enabled,
        "provider": config.name if config else None,
        "model": config.model if config else None,
        "base_url": config.base_url if config else None,
        "note": None
        if config
        else "No AI provider is configured. CodeGuard AI runs fully in offline mode using deterministic static analysis.",
    }


@router.post("/settings/ai/test")
def test_ai(
    payload: AITestRequest | None = None,
    settings_row: UserSettings = Depends(get_user_settings),
) -> dict:
    config = provider.resolve_config(settings_row)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI provider is configured in the backend environment.",
        )
    try:
        reply = provider.test_provider(config)
    except provider.AIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {"ok": True, "provider": config.name, "model": config.model, "reply": reply}


@router.get("/tools")
def scanner_tools() -> dict:
    detected = tools.detect_tools()
    available = [name for name, path in detected.items() if path]
    unavailable = [
        {"tool": name, "purpose": spec["purpose"]}
        for name, spec in tools.TOOL_SPECS.items()
        if not detected.get(name)
    ]
    return {
        "builtin": {"tool": "codeguard-builtin", "available": True, "purpose": "Built-in pattern and AST analysis"},
        "available": available,
        "unavailable": unavailable,
    }
