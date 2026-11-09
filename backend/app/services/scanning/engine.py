"""Repository scanning orchestration.

Runs in a background thread, updates real scan progress, executes any available
static-analysis tools plus the built-in analyzer, normalizes and deduplicates
findings, and persists everything to the database.
"""
from __future__ import annotations

import logging
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import CLONE_DIR, settings
from app.database.base import utcnow
from app.database.session import SessionLocal
from app.models import Finding, Repository, Scan
from app.services.github import git_service
from app.services.scanning import builtin, tools
from app.services.scanning.languages import collect_source_files, read_text
from app.services.scanning.normalized import RawFinding

logger = logging.getLogger("codeguard.engine")

_semaphore = threading.Semaphore(max(1, settings.max_concurrent_scans))


def _update(db: Session, scan: Scan, **fields) -> None:
    for key, value in fields.items():
        setattr(scan, key, value)
    db.add(scan)
    db.commit()


def run_scan(scan_id: int) -> None:
    """Entry point executed in a background thread."""
    acquired = _semaphore.acquire(timeout=settings.clone_timeout_seconds + settings.tool_timeout_seconds)
    db = SessionLocal()
    scan: Scan | None = None
    work_dir: Path | None = None
    try:
        scan = db.get(Scan, scan_id)
        if scan is None:
            return
        repo = db.get(Repository, scan.repository_id)
        if repo is None:
            _update(db, scan, status="failed", error_message="Repository no longer exists.")
            return

        scan.status = "running"
        scan.started_at = utcnow()
        scan.stage = "Fetching repository"
        scan.progress = 5
        db.commit()

        work_dir = CLONE_DIR / f"repo-{repo.id}" / f"scan-{scan.id}"
        git_service.clone_repository(
            repo.url,
            work_dir,
            branch=scan.branch,
            token=repo.access_token,
        )

        sha, message = git_service.get_commit_info(work_dir)
        _update(db, scan, commit_sha=sha, commit_message=message, stage="Discovering source files", progress=20)

        files, language_counts = collect_source_files(
            work_dir, settings.max_files, settings.max_file_size_kb
        )
        _update(
            db,
            scan,
            languages=[{"language": k, "files": v} for k, v in sorted(language_counts.items(), key=lambda x: -x[1])],
        )

        available = tools.detect_tools()
        tools_used: list[str] = ["codeguard-builtin"]
        tools_skipped: list[dict] = []

        raw_findings: list[RawFinding] = []
        total = max(1, len(files))

        # Built-in analyzer over every supported file.
        for index, path in enumerate(files, start=1):
            rel = str(path.relative_to(work_dir)).replace("\\", "/")
            text = read_text(path)
            if not text:
                continue
            lang = _language_for_rel(path)
            raw_findings.extend(builtin.scan_text(rel, text, lang))
            if index % 25 == 0 or index == total:
                progress = 25 + int((index / total) * 45)
                _update(db, scan, stage=f"Analyzing source files ({index}/{total})", progress=min(progress, 70))

        # External scanners (optional).
        _update(db, scan, stage="Running external scanners", progress=72)
        for name, runner in tools.RUNNERS.items():
            if not available.get(name):
                tools_skipped.append({"tool": name, "reason": "not installed", "purpose": tools.TOOL_SPECS[name]["purpose"]})
                continue
            try:
                produced = runner(work_dir)
                raw_findings.extend(produced)
                tools_used.append(name)
            except Exception as exc:  # noqa: BLE001 - one tool must not break the scan
                logger.warning("Scanner %s failed: %s", name, exc)
                tools_skipped.append({"tool": name, "reason": f"error: {exc}", "purpose": tools.TOOL_SPECS[name]["purpose"]})

        _update(db, scan, stage="Normalizing findings", progress=85)

        deduped = _dedupe(raw_findings)
        for item in deduped:
            db.add(
                Finding(
                    scan_id=scan.id,
                    repository_id=repo.id,
                    user_id=repo.user_id,
                    title=item.title[:300],
                    description=item.description,
                    severity=item.severity,
                    category=item.category,
                    file_path=item.file_path,
                    line_number=item.line_number,
                    end_line=item.end_line,
                    code_excerpt=item.code_excerpt,
                    tool=item.tool,
                    rule_id=item.rule_id,
                    cwe=item.cwe,
                    remediation=item.remediation,
                    confidence=item.confidence,
                    status="open",
                    kind=item.kind,
                )
            )

        finished = utcnow()
        started = scan.started_at
        duration = (finished - started).total_seconds() if started else None
        scan.status = "completed"
        scan.stage = "Completed"
        scan.progress = 100
        scan.total_findings = len(deduped)
        scan.files_scanned = len(files)
        scan.tools_used = tools_used
        scan.tools_skipped = tools_skipped
        scan.finished_at = finished
        scan.duration_seconds = duration
        repo.last_scanned_at = finished
        db.add(scan)
        db.add(repo)
        db.commit()
        logger.info("Scan %s completed with %s findings", scan.id, len(deduped))

    except Exception as exc:  # noqa: BLE001
        logger.exception("Scan %s failed", scan_id)
        if scan is not None:
            scan.status = "failed"
            scan.stage = "Failed"
            scan.error_message = str(exc)[:1000]
            scan.finished_at = utcnow()
            if scan.started_at:
                scan.duration_seconds = (scan.finished_at - scan.started_at).total_seconds()
            db.add(scan)
            db.commit()
    finally:
        try:
            if work_dir is not None and work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)
                parent = work_dir.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
        except OSError:
            pass
        db.close()
        if acquired:
            _semaphore.release()


def _language_for_rel(path: Path) -> str | None:
    from app.services.scanning.languages import language_for

    return language_for(path)


def _dedupe(findings: list[RawFinding]) -> list[RawFinding]:
    seen: dict[tuple, RawFinding] = {}
    for item in findings:
        key = item.dedupe_key()
        existing = seen.get(key)
        if existing is None:
            seen[key] = item
        else:
            # Prefer the higher severity / more specific description.
            from app.services.scanning.normalized import SEVERITY_ORDER

            if SEVERITY_ORDER.get(item.severity, 9) < SEVERITY_ORDER.get(existing.severity, 9):
                seen[key] = item
    return list(seen.values())
