"""Scan routes."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Repository, Scan, User
from app.schemas.core import ScanOut, ScanSummaryOut
from app.services.scanning.engine import run_scan

router = APIRouter(tags=["scans"])


def _scan_out(scan: Scan, repo: Repository | None = None) -> ScanSummaryOut:
    out = ScanSummaryOut.model_validate(scan)
    if repo is not None:
        out.repository_full_name = repo.full_name
    return out


@router.post("/repositories/{repo_id}/scan", response_model=ScanOut, status_code=status.HTTP_202_ACCEPTED)
def start_scan(
    repo_id: int,
    background_tasks: BackgroundTasks,
    branch: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScanOut:
    repo = db.get(Repository, repo_id)
    if repo is None or repo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")

    running = (
        db.query(Scan)
        .filter(Scan.repository_id == repo.id, Scan.status.in_(("queued", "running")))
        .first()
    )
    if running is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A scan is already in progress for this repository.")

    scan = Scan(
        repository_id=repo.id,
        user_id=user.id,
        branch=branch or repo.default_branch,
        status="queued",
        stage="Queued",
        progress=0,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(run_scan, scan.id)
    return ScanOut.model_validate(scan)


@router.get("/scans", response_model=list[ScanSummaryOut])
def list_scans(
    repository_id: int | None = Query(default=None),
    scan_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ScanSummaryOut]:
    query = db.query(Scan, Repository).join(Repository, Scan.repository_id == Repository.id).filter(Scan.user_id == user.id)
    if repository_id is not None:
        query = query.filter(Scan.repository_id == repository_id)
    if scan_status:
        query = query.filter(Scan.status == scan_status)
    rows = query.order_by(Scan.id.desc()).limit(limit).all()
    return [_scan_out(scan, repo) for scan, repo in rows]


@router.get("/scans/{scan_id}", response_model=ScanSummaryOut)
def get_scan(
    scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ScanSummaryOut:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    repo = db.get(Repository, scan.repository_id)
    return _scan_out(scan, repo)


@router.get("/scans/{scan_id}/status")
def scan_status(
    scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    return {
        "id": scan.id,
        "status": scan.status,
        "stage": scan.stage,
        "progress": scan.progress,
        "total_findings": scan.total_findings,
        "files_scanned": scan.files_scanned,
        "error_message": scan.error_message,
    }


@router.post("/scans/{scan_id}/cancel", response_model=ScanOut)
def cancel_scan(
    scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ScanOut:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    if scan.status in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This scan has already finished.")
    scan.status = "cancelled"
    scan.stage = "Cancelled"
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return ScanOut.model_validate(scan)
