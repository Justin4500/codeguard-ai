"""Controlled fix generation, application and reversion.

Guarantees:
- The original repository is never modified; work happens in isolated copies.
- A patch is never applied without explicit approval via the API.
- Every applied change keeps a backup so it can be reverted.
- Nothing is pushed to GitHub automatically.
"""
from __future__ import annotations

import difflib
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import WORK_DIR, settings
from app.models import AppliedFix, Finding, FixProposal, Repository
from app.services.ai import provider
from app.services.github import git_service

logger = logging.getLogger("codeguard.fixes")

MAX_AI_FILE_BYTES = 200 * 1024


class FixError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
def _t_md5_sha1(line: str):
    new = line
    new = new.replace("hashlib.md5", "hashlib.sha256").replace("hashlib.sha1", "hashlib.sha256")
    new = re.sub(r"\bmd5\s*\(", "sha256(", new)
    new = re.sub(r"\bsha1\s*\(", "sha256(", new)
    new = new.replace("createHash('md5')", "createHash('sha256')").replace('createHash("md5")', 'createHash("sha256")')
    new = new.replace("createHash('sha1')", "createHash('sha256')").replace('createHash("sha1")', 'createHash("sha256")')
    if new == line:
        return None
    return new, "Replaced the weak MD5/SHA-1 hash with SHA-256, which is not vulnerable to practical collision attacks."


def _t_yaml_load(line: str):
    new = re.sub(r"yaml\.load\s*\(", "yaml.safe_load(", line)
    if new == line:
        return None
    return new, "Switched to yaml.safe_load() so untrusted YAML cannot instantiate arbitrary Python objects."


def _t_shell_false(line: str):
    new = re.sub(r"shell\s*=\s*True", "shell=False", line)
    if new == line:
        return None
    return new, "Disabled shell interpretation (shell=False) so arguments cannot be injected into a shell."


def _t_debug_false(line: str):
    new = re.sub(r"debug\s*=\s*True", "debug=False", line)
    if new == line:
        return None
    return new, "Disabled debug mode, which would otherwise expose an interactive debugger in production."


def _t_is_literal(line: str):
    new = re.sub(r"\bis\s+True\b", "== True", line)
    new = re.sub(r"\bis\s+False\b", "== False", new)
    new = re.sub(r"\bis\s+(\d+)\b", r"== \1", new)
    if new == line:
        return None
    return new, "Replaced identity comparison ('is') with equality comparison ('=='), which reflects the intended value check."


def _t_eval(line: str):
    new = re.sub(r"(?<![\w.])eval\s*\(", "ast.literal_eval(", line)
    if new == line:
        return None
    return (
        new,
        "Replaced eval() with ast.literal_eval(), which only parses literal values and cannot execute arbitrary code. "
        "Ensure 'import ast' is present in the module.",
    )


TEMPLATES = {
    "CG-SEC-031": _t_md5_sha1,
    "CG-SEC-033": _t_yaml_load,
    "CG-SEC-037": _t_shell_false,
    "CG-SEC-034": _t_debug_false,
    "CG-QUA-041": _t_is_literal,
    "CG-SEC-020": _t_eval,
    "CG-SEC-020b": _t_eval,
}


# --------------------------------------------------------------------------- #
# Source access
# --------------------------------------------------------------------------- #
def ensure_source(repo: Repository) -> Path:
    dest = WORK_DIR / f"repo-{repo.id}" / "source"
    if not dest.exists():
        git_service.clone_repository(
            repo.url,
            dest,
            branch=repo.default_branch,
            token=repo.access_token,
        )
    return dest


def _safe_path(root: Path, rel_path: str) -> Path:
    candidate = (root / rel_path).resolve()
    root_resolved = root.resolve()
    if not str(candidate).startswith(str(root_resolved)):
        raise FixError("Refusing to access a path outside the repository.")
    return candidate


def _line_of(finding: Finding, text: str) -> int | None:
    if finding.line_number:
        return finding.line_number
    if finding.code_excerpt:
        lines = text.splitlines()
        needle = finding.code_excerpt.strip().splitlines()[0].strip() if finding.code_excerpt.strip() else ""
        for idx, line in enumerate(lines, start=1):
            if needle and needle in line:
                return idx
    return None


# --------------------------------------------------------------------------- #
# Proposal
# --------------------------------------------------------------------------- #
def propose_fix(db: Session, finding: Finding, repo: Repository, settings_row=None) -> FixProposal:
    if not finding.file_path:
        raise FixError("This finding has no associated file and cannot be patched automatically.")

    source = ensure_source(repo)
    path = _safe_path(source, finding.file_path)
    if not path.exists():
        raise FixError("The affected file could not be found in the repository default branch.")

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    line_no = _line_of(finding, text)
    if not line_no or line_no < 1 or line_no > len(lines):
        raise FixError("The affected line could not be located; a safe fix cannot be generated.")

    original_line = lines[line_no - 1]
    template = TEMPLATES.get(finding.rule_id or "")
    proposed_line: str | None = None
    explanation: str | None = None
    generator = "template"

    if template is not None:
        result = template(original_line)
        if result is not None:
            proposed_line, explanation = result

    if proposed_line is None:
        ai_line, ai_explanation = _ai_line_fix(finding, original_line, settings_row)
        if ai_line is not None:
            proposed_line, explanation, generator = ai_line, ai_explanation, "ai"

    if proposed_line is None:
        raise FixError(
            "No safe automatic fix is available for this finding. "
            "It requires manual review (see the remediation guidance)."
        )

    original_code = original_line
    proposed_code = proposed_line
    diff = "".join(
        difflib.unified_diff(
            [original_line + "\n"],
            [proposed_line + "\n"],
            fromfile=f"a/{finding.file_path}",
            tofile=f"b/{finding.file_path}",
            lineterm="\n",
        )
    )
    # unified_diff numbers an isolated single-line change as line 1; correct the
    # hunk header so it points at the real location within the file.
    diff = diff.replace("@@ -1 +1 @@", f"@@ -{line_no} +{line_no} @@", 1)
    if not diff:
        raise FixError("The proposed change is identical to the current code; nothing to fix.")

    proposal = FixProposal(
        finding_id=finding.id,
        user_id=finding.user_id,
        file_path=finding.file_path,
        language=_lang_for(finding.file_path),
        original_code=original_code,
        proposed_code=proposed_code,
        diff=diff,
        explanation=explanation,
        generator=generator,
        status="proposed",
    )
    finding.status = "fix_proposed"
    db.add(proposal)
    db.add(finding)
    db.commit()
    db.refresh(proposal)
    return proposal


def _ai_line_fix(finding: Finding, line: str, settings_row=None):
    config = provider.resolve_config(settings_row)
    if config is None:
        return None, None
    if settings_row is not None and not settings_row.allow_external_code:
        return None, None
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior security engineer. Return ONLY the corrected version of the "
                "single line of code, with no explanation, no markdown fences and no extra text."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Issue: {finding.title}\nCategory: {finding.category}\nSeverity: {finding.severity}\n"
                f"File: {finding.file_path}\nLine:\n{line}"
            ),
        },
    ]
    try:
        result = provider.chat(messages, config, max_tokens=200)
    except provider.AIError as exc:
        logger.info("AI fix generation unavailable: %s", exc)
        return None, None
    cleaned = result.strip().strip("`").strip()
    if cleaned.startswith(("python", "js", "javascript", "ts")):
        cleaned = cleaned.split("\n", 1)[-1].strip()
    if not cleaned or "\n" in cleaned:
        return None, None
    return cleaned, "AI-generated correction for the flagged line."


# --------------------------------------------------------------------------- #
# Apply / revert
# --------------------------------------------------------------------------- #
def apply_fix(db: Session, proposal: FixProposal, repo: Repository) -> tuple[AppliedFix, str]:
    source = ensure_source(repo)
    src_file = _safe_path(source, proposal.file_path)

    if proposal.applied is not None and proposal.applied.reverted == 0:
        raise FixError("This fix has already been applied.")

    work = WORK_DIR / f"fix-{proposal.id}"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    target = _safe_path(work, proposal.file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    original_text = src_file.read_text(encoding="utf-8", errors="replace") if src_file.exists() else ""
    backup = target.with_suffix(target.suffix + ".codeguard.bak")
    backup.write_text(original_text, encoding="utf-8")

    if proposal.original_code not in original_text:
        raise FixError("The original code no longer matches the repository; the fix must be regenerated.")

    updated = original_text.replace(proposal.original_code, proposal.proposed_code, 1)
    target.write_text(updated, encoding="utf-8")

    validation = validate_file(target, proposal.file_path)

    applied = AppliedFix(
        fix_proposal_id=proposal.id,
        finding_id=proposal.finding_id,
        user_id=proposal.user_id,
        file_path=proposal.file_path,
        backup_path=str(backup),
        validation_output=validation,
        reverted=0,
    )
    proposal.status = "approved"
    proposal.validation_output = validation
    from app.database.base import utcnow

    proposal.applied_at = utcnow()
    finding = db.get(Finding, proposal.finding_id)
    if finding is not None:
        finding.status = "fixed"
        db.add(finding)
    db.add(applied)
    db.add(proposal)
    db.commit()
    db.refresh(applied)
    return applied, validation


def revert_fix(db: Session, applied: AppliedFix) -> str:
    if applied.reverted:
        raise FixError("This change has already been reverted.")
    backup = Path(applied.backup_path) if applied.backup_path else None
    target = WORK_DIR / f"fix-{applied.fix_proposal_id}" / applied.file_path
    message = "Reverted to the original file contents."
    if backup and backup.exists() and target.parent.exists():
        target.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        message = validate_file(target, applied.file_path)
    from app.database.base import utcnow

    applied.reverted = 1
    applied.reverted_at = utcnow()
    proposal = db.get(FixProposal, applied.fix_proposal_id)
    if proposal is not None:
        proposal.status = "reverted"
        db.add(proposal)
    finding = db.get(Finding, applied.finding_id)
    if finding is not None:
        finding.status = "confirmed"
        db.add(finding)
    db.add(applied)
    db.commit()
    return message


def validate_file(path: Path, rel_path: str) -> str:
    """Run a lightweight syntax validation on the patched file."""
    suffix = Path(rel_path).suffix.lower()
    try:
        if suffix in {".py", ".pyi"}:
            proc = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True, text=True, timeout=30,
            )
            return "Python syntax check passed." if proc.returncode == 0 else f"Python syntax error:\n{proc.stderr[:800]}"
        if suffix in {".js", ".mjs", ".cjs"}:
            proc = subprocess.run(
                ["node", "--check", str(path)],
                capture_output=True, text=True, timeout=30, shell=False,
            )
            return "Node syntax check passed." if proc.returncode == 0 else f"Node syntax error:\n{proc.stderr[:800]}"
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        return f"Validation tool unavailable: {exc}"
    return "No automated validator is available for this file type; review the diff manually."


def _lang_for(rel_path: str) -> str | None:
    from app.services.scanning.languages import language_for

    return language_for(Path(rel_path))
