"""Fix proposal routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_user_settings
from app.database.session import get_db
from app.models import AppliedFix, Finding, FixProposal, Repository, User, UserSettings
from app.schemas.core import ApproveOut, FixProposalOut
from app.services.fixes import generator

router = APIRouter(tags=["fixes"])


def _owned_finding(db: Session, finding_id: int, user: User) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
    return finding


def _owned_proposal(db: Session, proposal_id: int, user: User) -> FixProposal:
    proposal = db.get(FixProposal, proposal_id)
    if proposal is None or proposal.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fix proposal not found.")
    return proposal


@router.post("/findings/{finding_id}/propose-fix", response_model=FixProposalOut)
def propose_fix(
    finding_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings_row: UserSettings = Depends(get_user_settings),
) -> FixProposalOut:
    finding = _owned_finding(db, finding_id, user)
    repo = db.get(Repository, finding.repository_id)
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    try:
        proposal = generator.propose_fix(db, finding, repo, settings_row)
    except generator.FixError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Fix generation failed: {exc}") from exc
    return FixProposalOut.model_validate(proposal)


@router.get("/findings/{finding_id}/fixes", response_model=list[FixProposalOut])
def list_proposals(
    finding_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FixProposalOut]:
    _owned_finding(db, finding_id, user)
    proposals = (
        db.query(FixProposal)
        .filter(FixProposal.finding_id == finding_id, FixProposal.user_id == user.id)
        .order_by(FixProposal.id.desc())
        .all()
    )
    return [FixProposalOut.model_validate(p) for p in proposals]


@router.get("/fixes/{proposal_id}", response_model=FixProposalOut)
def get_proposal(
    proposal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FixProposalOut:
    return FixProposalOut.model_validate(_owned_proposal(db, proposal_id, user))


@router.post("/fixes/{proposal_id}/approve", response_model=ApproveOut)
def approve_fix(
    proposal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ApproveOut:
    proposal = _owned_proposal(db, proposal_id, user)
    if proposal.status != "proposed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This proposal is '{proposal.status}' and can no longer be applied. Generate a new fix instead.",
        )
    finding = db.get(Finding, proposal.finding_id)
    repo = db.get(Repository, finding.repository_id) if finding else None
    if repo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found.")
    try:
        applied, validation = generator.apply_fix(db, proposal, repo)
    except generator.FixError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Applying the fix failed: {exc}") from exc
    db.refresh(proposal)
    return ApproveOut(
        proposal=FixProposalOut.model_validate(proposal),
        validation_output=validation,
        message="Fix applied to an isolated working copy. The original repository was not modified.",
    )


@router.post("/fixes/{proposal_id}/reject", response_model=FixProposalOut)
def reject_fix(
    proposal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FixProposalOut:
    proposal = _owned_proposal(db, proposal_id, user)
    if proposal.status == "approved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An applied fix must be reverted, not rejected.")
    proposal.status = "rejected"
    finding = db.get(Finding, proposal.finding_id)
    if finding is not None and finding.status == "fix_proposed":
        finding.status = "open"
        db.add(finding)
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return FixProposalOut.model_validate(proposal)


@router.post("/fixes/{proposal_id}/revert", response_model=FixProposalOut)
def revert_fix(
    proposal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FixProposalOut:
    proposal = _owned_proposal(db, proposal_id, user)
    applied: AppliedFix | None = proposal.applied
    if applied is None or applied.reverted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="There is no applied change to revert.")
    try:
        validation = generator.revert_fix(db, applied)
    except generator.FixError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    proposal.validation_output = validation
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return FixProposalOut.model_validate(proposal)
