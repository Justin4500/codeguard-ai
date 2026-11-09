"""Finding routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_settings
from app.database.session import get_db
from app.models import Finding, Repository, User, UserSettings
from app.schemas.core import ExplainOut, ExplainRequest, FindingListOut, FindingOut, FindingUpdate
from app.services.ai import provider

router = APIRouter(prefix="/findings", tags=["findings"])

VALID_STATUS = {"open", "confirmed", "false_positive", "fix_proposed", "fixed", "ignored"}
VALID_SEVERITY = {"critical", "high", "medium", "low", "informational"}

_SEVERITY_MEANING = {
    "critical": "exploitable now and can lead to full compromise",
    "high": "serious risk that should be addressed promptly",
    "medium": "moderate risk that should be scheduled for remediation",
    "low": "minor risk or code-health concern",
    "informational": "style or advisory note with limited direct risk",
}


@router.get("", response_model=FindingListOut)
def list_findings(
    repository_id: int | None = Query(default=None),
    scan_id: int | None = Query(default=None),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    finding_status: str | None = Query(default=None, alias="status"),
    tool: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FindingListOut:
    base = db.query(Finding).filter(Finding.user_id == user.id)
    if repository_id is not None:
        base = base.filter(Finding.repository_id == repository_id)
    if scan_id is not None:
        base = base.filter(Finding.scan_id == scan_id)
    if severity:
        base = base.filter(Finding.severity == severity)
    if category:
        base = base.filter(Finding.category == category)
    if finding_status:
        base = base.filter(Finding.status == finding_status)
    if tool:
        base = base.filter(Finding.tool == tool)
    if search:
        like = f"%{search}%"
        base = base.filter(
            or_(
                Finding.title.ilike(like),
                Finding.file_path.ilike(like),
                Finding.description.ilike(like),
                Finding.rule_id.ilike(like),
            )
        )

    total = base.count()
    items = (
        base.order_by(Finding.severity, Finding.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    counts_rows = (
        db.query(Finding.severity, func.count(Finding.id))
        .filter(Finding.user_id == user.id)
        .group_by(Finding.severity)
        .all()
    )
    severity_counts = {sev: 0 for sev in ("critical", "high", "medium", "low", "informational")}
    for sev, count in counts_rows:
        severity_counts[sev] = count

    return FindingListOut(
        items=[FindingOut.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        severity_counts=severity_counts,
    )


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(
    finding_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FindingOut:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    return FindingOut.model_validate(finding)


@router.patch("/{finding_id}", response_model=FindingOut)
def update_finding(
    finding_id: int,
    payload: FindingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FindingOut:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    if payload.status is not None:
        if payload.status not in VALID_STATUS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status value.")
        finding.status = payload.status
    if payload.severity is not None:
        if payload.severity not in VALID_SEVERITY:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid severity value.")
        finding.severity = payload.severity
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return FindingOut.model_validate(finding)


def offline_explanation(finding: Finding) -> str:
    parts = [
        f"{finding.title}",
        "",
        f"Severity: {finding.severity} ({_SEVERITY_MEANING.get(finding.severity, 'review recommended')}).",
        f"Category: {finding.category}.",
        f"Detected by: {finding.tool}" + (f" (rule {finding.rule_id})" if finding.rule_id else "") + ".",
    ]
    if finding.cwe:
        parts.append(f"Reference: {finding.cwe}.")
    if finding.file_path:
        location = finding.file_path + (f":{finding.line_number}" if finding.line_number else "")
        parts.append(f"Location: {location}.")
    if finding.description:
        parts.extend(["", "Details:", finding.description])
    if finding.code_excerpt:
        parts.extend(["", "Affected code:", "```", finding.code_excerpt, "```"])
    if finding.remediation:
        parts.extend(["", "Recommended remediation:", finding.remediation])
    parts.extend(
        [
            "",
            "Note: AI explanation is disabled, so this guidance is generated from the deterministic "
            "scanner output and rule metadata rather than a language model.",
        ]
    )
    return "\n".join(parts)


@router.post("/{finding_id}/explain", response_model=ExplainOut)
def explain_finding(
    finding_id: int,
    payload: ExplainRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings_row: UserSettings = Depends(get_user_settings),
) -> ExplainOut:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")

    config = provider.resolve_config(settings_row)
    if config is None:
        return ExplainOut(
            finding_id=finding.id,
            ai_available=False,
            provider=None,
            explanation=offline_explanation(finding),
            source="offline",
        )

    if not settings_row.allow_external_code:
        return ExplainOut(
            finding_id=finding.id,
            ai_available=True,
            provider=config.name,
            explanation=offline_explanation(finding)
            + "\n\nAI explanations are disabled until you allow sending code context externally in Settings.",
            source="offline",
        )

    question = (payload.question if payload else None) or "Explain this issue and how to fix it."
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior application security engineer embedded in a code review platform. "
                "Explain the finding concisely: what it is, why it matters, the risk, and a concrete fix. "
                "Use short paragraphs and bullet points. Do not invent line numbers or facts not provided."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Finding: {finding.title}\nSeverity: {finding.severity}\nCategory: {finding.category}\n"
                f"Tool: {finding.tool}\nRule: {finding.rule_id or 'n/a'}\nCWE: {finding.cwe or 'n/a'}\n"
                f"File: {finding.file_path or 'n/a'}:{finding.line_number or 'n/a'}\n"
                f"Scanner description: {finding.description or 'n/a'}\n"
                f"Code context:\n{finding.code_excerpt or 'n/a'}\n\n"
                f"Question: {question}"
            ),
        },
    ]
    try:
        text = provider.chat(messages, config)
    except provider.AIError as exc:
        return ExplainOut(
            finding_id=finding.id,
            ai_available=True,
            provider=config.name,
            explanation=offline_explanation(finding) + f"\n\n(AI request failed: {exc})",
            source="offline",
        )
    return ExplainOut(
        finding_id=finding.id, ai_available=True, provider=config.name, explanation=text, source="ai"
    )
