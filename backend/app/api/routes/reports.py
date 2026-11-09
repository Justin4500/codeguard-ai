"""Report routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Finding, Repository, Scan, User
from app.services.reports import generator

router = APIRouter(prefix="/reports", tags=["reports"])


def _load(db: Session, scan_id: int, user: User) -> tuple[Scan, Repository, list[Finding]]:
    scan = db.get(Scan, scan_id)
    if scan is None or scan.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    repo = db.get(Repository, scan.repository_id)
    findings = db.query(Finding).filter(Finding.scan_id == scan.id).order_by(Finding.id).all()
    return scan, repo, findings


@router.get("/{scan_id}")
def report_preview(
    scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    scan, repo, findings = _load(db, scan_id, user)
    return generator.build_json(scan, repo, findings)


@router.get("/{scan_id}/export")
def export_report(
    scan_id: int,
    format: str = Query(default="html", pattern="^(html|json|csv|pdf)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    scan, repo, findings = _load(db, scan_id, user)
    safe_name = repo.full_name.replace("/", "-")
    if format == "json":
        body = generator.json_dumps(generator.build_json(scan, repo, findings))
        return _file_response(body, f"codeguard-{safe_name}-scan{scan.id}.json", "application/json")
    if format == "csv":
        body = generator.build_csv(findings)
        return _file_response(body, f"codeguard-{safe_name}-scan{scan.id}.csv", "text/csv")
    if format == "pdf":
        try:
            pdf_bytes = generator.build_pdf(scan, repo, findings)
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc
        return _bytes_response(pdf_bytes, f"codeguard-{safe_name}-scan{scan.id}.pdf", "application/pdf")
    body = generator.build_html(scan, repo, findings)
    return _file_response(body, f"codeguard-{safe_name}-scan{scan.id}.html", "text/html")


def _file_response(body: str, filename: str, media_type: str) -> Response:
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _bytes_response(body: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
