"""GitHub repository validation, metadata and cloning via the Git CLI.

Safety rules enforced here:
- Only github.com URLs are accepted.
- Subprocess calls use argument lists (never shell strings).
- Access tokens are never logged and never returned to the frontend.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger("codeguard.git")

_GITHUB_URL_RE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class GitError(Exception):
    """Raised when a git operation fails."""


@dataclass
class RepoInfo:
    owner: str
    name: str
    full_name: str
    url: str
    description: str | None = None
    language: str | None = None
    default_branch: str | None = None
    visibility: str = "public"
    stars: int | None = None
    size_kb: int | None = None


def parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo) for a GitHub URL, raising ValueError otherwise."""
    match = _GITHUB_URL_RE.match(url.strip())
    if not match:
        raise ValueError(
            "Invalid GitHub repository URL. Expected https://github.com/owner/repo"
        )
    owner, repo = match.group("owner"), match.group("repo")
    if repo.lower() in {"", "."} or owner.lower() in {"", "."}:
        raise ValueError("Invalid GitHub repository URL.")
    return owner, repo


def _api_headers(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CodeGuard-AI"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_metadata(owner: str, name: str, token: str | None = None) -> RepoInfo:
    """Fetch repository metadata from the GitHub REST API."""
    url = f"https://api.github.com/repos/{owner}/{name}"
    info = RepoInfo(
        owner=owner,
        name=name,
        full_name=f"{owner}/{name}",
        url=f"https://github.com/{owner}/{name}",
    )
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, headers=_api_headers(token))
        if resp.status_code == 200:
            data = resp.json()
            info.description = data.get("description")
            info.language = data.get("language")
            info.default_branch = data.get("default_branch") or "main"
            info.visibility = "private" if data.get("private") else "public"
            info.stars = data.get("stargazers_count")
            info.size_kb = data.get("size")
        elif resp.status_code == 404:
            raise ValueError("Repository not found or is private. Provide an access token for private repositories.")
        elif resp.status_code == 403:
            logger.warning("GitHub API rate limited while fetching metadata for %s", info.full_name)
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("GitHub metadata request failed: %s", exc)
    return info


def _auth_url(url: str, token: str | None) -> str:
    if not token:
        return url
    # Token-injected HTTPS URL for private repositories.
    return url.replace("https://", f"https://x-access-token:{token}@", 1)


def clone_repository(
    url: str,
    dest: Path,
    branch: str | None = None,
    token: str | None = None,
    depth: int = 1,
) -> None:
    """Shallow-clone a repository into dest using the Git CLI."""
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.parent.mkdir(parents=True, exist_ok=True)

    clone_url = _auth_url(url, token)
    args = ["git", "clone", "--depth", str(depth), "--no-tags"]
    if branch:
        args += ["--branch", branch]
    args += [clone_url, str(dest)]

    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "echo",
        "GCM_INTERACTIVE": "never",
    }
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=settings.clone_timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitError("Repository clone timed out.") from exc
    except FileNotFoundError as exc:
        raise GitError("Git is not installed or not available on PATH.") from exc

    if proc.returncode != 0:
        stderr = _redact(proc.stderr or "", token)
        raise GitError(f"Failed to clone repository: {stderr.strip()[:400]}")


def get_commit_info(repo_dir: Path) -> tuple[str | None, str | None]:
    """Return (commit_sha, commit_message) for the checked-out HEAD."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
        msg = subprocess.run(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
        return (sha or None, msg or None)
    except (subprocess.SubprocessError, FileNotFoundError) as exc:  # pragma: no cover
        logger.warning("Failed to read commit info: %s", exc)
        return (None, None)


def _redact(text: str, token: str | None) -> str:
    if token and token in text:
        return text.replace(token, "***")
    return text
