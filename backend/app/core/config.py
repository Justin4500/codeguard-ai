"""Application configuration loaded from environment variables / .env files."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # repo root
STORAGE_DIR = BASE_DIR / "storage"
CLONE_DIR = STORAGE_DIR / "repos"
WORK_DIR = STORAGE_DIR / "work"
REPORT_DIR = STORAGE_DIR / "reports"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "CodeGuard AI"
    api_prefix: str = "/api"
    debug: bool = False

    # Auth
    secret_key: str = "change-me-in-production-please-set-a-real-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Database
    database_url: str = f"sqlite:///{(STORAGE_DIR / 'codeguard.db').as_posix()}"

    # CORS
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # AI provider (optional). OpenAI-compatible endpoint.
    ai_provider: str = ""            # e.g. deepseek | qwen | siliconflow | openai | gemini
    ai_base_url: str = ""            # e.g. https://api.deepseek.com/v1
    ai_api_key: str = ""
    ai_model: str = ""               # e.g. deepseek-chat

    # Scanning limits (tuned for low-resource machines)
    max_repo_size_mb: int = 200
    max_files: int = 2500
    max_file_size_kb: int = 512
    clone_timeout_seconds: int = 180
    tool_timeout_seconds: int = 180
    max_concurrent_scans: int = 2

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_api_key and self.ai_base_url and self.ai_model)


settings = Settings()

for _d in (STORAGE_DIR, CLONE_DIR, WORK_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
