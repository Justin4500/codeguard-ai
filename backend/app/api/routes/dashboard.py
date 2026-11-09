"""Dashboard analytics routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Finding, Repository, Scan, User
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SEVERITIES = ["critical", "high", "medium", "low", "informational"]


@router.get("/stats", response_model=DashboardStats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardStats:
    repo_count = db.query(func.count(Repository.id)).filter(Repository.user_id == user.id).scalar() or 0
    scan_count = db.query(func.count(Scan.id)).filter(Scan.user_id == user.id).scalar() or 0
    finding_count = db.query(func.count(Finding.id)).filter(Finding.user_id == user.id).scalar() or 0

    sev_rows = (
        db.query(Finding.severity, func.count(Finding.id))
        .filter(Finding.user_id == user.id)
        .group_by(Finding.severity)
        .all()
    )
    sev_counts = {s: 0 for s in SEVERITIES}
    for sev, count in sev_rows:
        sev_counts[sev] = count

    resolved = (
        db.query(func.count(Finding.id))
        .filter(Finding.user_id == user.id, Finding.status == "fixed")
        .scalar()
        or 0
    )
    open_count = (
        db.query(func.count(Finding.id))
        .filter(Finding.user_id == user.id, Finding.status.in_(("open", "confirmed", "fix_proposed")))
        .scalar()
        or 0
    )

    recent = (
        db.query(Scan, Repository)
        .join(Repository, Scan.repository_id == Repository.id)
        .filter(Scan.user_id == user.id)
        .order_by(Scan.id.desc())
        .limit(8)
        .all()
    )
    recent_scans = [
        {
            "id": scan.id,
            "repository_id": scan.repository_id,
            "repository": repo.full_name,
            "branch": scan.branch,
            "status": scan.status,
            "stage": scan.stage,
            "progress": scan.progress,
            "total_findings": scan.total_findings,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
        }
        for scan, repo in recent
    ]

    cat_rows = (
        db.query(Finding.category, func.count(Finding.id))
        .filter(Finding.user_id == user.id)
        .group_by(Finding.category)
        .all()
    )
    category_distribution = [{"category": c, "count": n} for c, n in cat_rows]

    activity_rows = (
        db.query(Repository.id, Repository.full_name, func.count(Finding.id))
        .outerjoin(Finding, Finding.repository_id == Repository.id)
        .filter(Repository.user_id == user.id)
        .group_by(Repository.id)
        .all()
    )
    repository_activity = [
        {"repository_id": rid, "repository": name, "findings": count}
        for rid, name, count in activity_rows
    ]

    return DashboardStats(
        repositories=repo_count,
        scans=scan_count,
        findings=finding_count,
        critical=sev_counts["critical"],
        high=sev_counts["high"],
        medium=sev_counts["medium"],
        low=sev_counts["low"],
        informational=sev_counts["informational"],
        resolved=resolved,
        open=open_count,
        recent_scans=recent_scans,
        severity_distribution=[{"severity": s, "count": sev_counts[s]} for s in SEVERITIES],
        category_distribution=category_distribution,
        repository_activity=repository_activity,
    )


@router.get("/analytics")
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Chart-ready aggregates built entirely from stored records."""
    by_language = (
        db.query(Repository.language, func.count(Finding.id))
        .join(Finding, Finding.repository_id == Repository.id)
        .filter(Repository.user_id == user.id, Repository.language.isnot(None))
        .group_by(Repository.language)
        .all()
    )
    by_severity = (
        db.query(Finding.severity, func.count(Finding.id))
        .filter(Finding.user_id == user.id)
        .group_by(Finding.severity)
        .all()
    )
    by_category = (
        db.query(Finding.category, func.count(Finding.id))
        .filter(Finding.user_id == user.id)
        .group_by(Finding.category)
        .all()
    )
    by_repo = (
        db.query(Repository.full_name, func.count(Finding.id))
        .join(Finding, Finding.repository_id == Repository.id)
        .filter(Repository.user_id == user.id)
        .group_by(Repository.id)
        .all()
    )
    trend_rows = (
        db.query(func.date(Scan.created_at), func.count(Finding.id))
        .join(Finding, Finding.scan_id == Scan.id)
        .filter(Scan.user_id == user.id)
        .group_by(func.date(Scan.created_at))
        .order_by(func.date(Scan.created_at))
        .all()
    )
    total = db.query(func.count(Finding.id)).filter(Finding.user_id == user.id).scalar() or 0
    fixed = (
        db.query(func.count(Finding.id))
        .filter(Finding.user_id == user.id, Finding.status == "fixed")
        .scalar()
        or 0
    )
    return {
        "by_severity": [{"severity": s, "count": c} for s, c in by_severity],
        "by_category": [{"category": c, "count": n} for c, n in by_category],
        "by_language": [{"language": l, "count": c} for l, c in by_language],
        "by_repository": [{"repository": r, "count": c} for r, c in by_repo],
        "trend": [{"date": str(d), "count": c} for d, c in trend_rows],
        "resolution_rate": round((fixed / total) * 100, 1) if total else 0.0,
        "total_findings": total,
        "resolved_findings": fixed,
    }
