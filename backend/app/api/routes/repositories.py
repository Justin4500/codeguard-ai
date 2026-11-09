"""Repository management routes."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Finding, Repository, Scan, User
from app.schemas.core import RepositoryCreate, RepositoryOut
from app.services.github import git_service

router = APIRouter(prefix="/repositories", tags=["repositories"])


def repo_to_out(db: Session, repo: Repository) -> RepositoryOut:
    scan_count = db.query(func.count(Scan.id)).filter(Scan.repository_id == repo.id).scalar() or 0
    finding_count = db.query(func.count(Finding.id)).filter(Finding.repository_id == repo.id).scalar() or 0
    critical = (
        db.query(func.count(Finding.id))
        .filter(Finding.repository_id == repo.id, Finding.severity == "critical")
        .scalar()
        or 0
    )
    last_scan = (
        db.query(Scan).filter(Scan.repository_id == repo.id).order_by(Scan.id.desc()).first()
    )
    out = RepositoryOut.model_validate(repo)
    out.scan_count = scan_count
    out.finding_count = finding_count
    out.critical_count = critical
    out.last_scan_status = last_scan.status if last_scan else None
    return out


def _get_owned(db: Session, repo_id: int, user: User) -> Repository:
    repo = db.get(Repository, repo_id)
    if repo is None or repo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    return repo


@router.post("", response_model=RepositoryOut, status_code=status.HTTP_201_CREATED)
def add_repository(
    payload: RepositoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RepositoryOut:
    try:
        owner, name = git_service.parse_github_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    token = (payload.access_token or "").strip() or None
    try:
        info = git_service.fetch_metadata(owner, name, token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    existing = (
        db.query(Repository)
        .filter(Repository.user_id == user.id, Repository.full_name == info.full_name)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This repository has already been added.")

    repo = Repository(
        user_id=user.id,
        url=info.url,
        full_name=info.full_name,
        owner=info.owner,
        name=info.name,
        description=info.description,
        language=info.language,
        default_branch=payload.branch or info.default_branch or "main",
        visibility=info.visibility,
        access_token=token,
        stars=info.stars,
        size_kb=info.size_kb,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo_to_out(db, repo)


@router.get("", response_model=list[RepositoryOut])
def list_repositories(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RepositoryOut]:
    repos = (
        db.query(Repository)
        .filter(Repository.user_id == user.id)
        .order_by(Repository.id.desc())
        .all()
    )
    return [repo_to_out(db, r) for r in repos]


@router.get("/{repo_id}", response_model=RepositoryOut)
def get_repository(
    repo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> RepositoryOut:
    return repo_to_out(db, _get_owned(db, repo_id, user))


@router.get("/{repo_id}/branches")
def list_branches(
    repo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    repo = _get_owned(db, repo_id, user)
    branches: list[str] = []
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CodeGuard-AI"}
    if repo.access_token:
        headers["Authorization"] = f"Bearer {repo.access_token}"
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(
                f"https://api.github.com/repos/{repo.full_name}/branches",
                headers=headers,
                params={"per_page": 100},
            )
        if resp.status_code == 200:
            branches = [b.get("name") for b in resp.json() if b.get("name")]
    except httpx.HTTPError:
        branches = []
    if not branches and repo.default_branch:
        branches = [repo.default_branch]
    return {"branches": branches, "default_branch": repo.default_branch}


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repo_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    repo = _get_owned(db, repo_id, user)
    db.delete(repo)
    db.commit()
