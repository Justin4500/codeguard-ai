"""Detection and execution of external static-analysis tools.

Every tool is optional. Availability is probed at runtime and unavailable
tools are reported back to the UI as "skipped". Output is parsed from the
real JSON emitted by each tool - nothing is fabricated.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

from app.core.config import settings
from app.services.scanning.normalized import RawFinding, excerpt_for, normalize_severity

logger = logging.getLogger("codeguard.tools")

TOOL_SPECS = {
    "ruff": {"cmd": "ruff", "purpose": "Python linting"},
    "bandit": {"cmd": "bandit", "purpose": "Python security analysis"},
    "semgrep": {"cmd": "semgrep", "purpose": "Multi-language security patterns"},
    "eslint": {"cmd": "eslint", "purpose": "JavaScript / TypeScript linting"},
    "npm": {"cmd": "npm", "purpose": "JavaScript dependency audit"},
    "pip-audit": {"cmd": "pip-audit", "purpose": "Python dependency audit"},
    "git": {"cmd": "git", "purpose": "Repository retrieval"},
}


def detect_tools() -> dict[str, str | None]:
    """Return a mapping of tool name -> resolved executable path (or None)."""
    return {name: shutil.which(spec["cmd"]) for name, spec in TOOL_SPECS.items()}


def _run(args: list[str], cwd: Path, timeout: int | None = None) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout or settings.tool_timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except FileNotFoundError:
        return 127, "", "not found"
    except OSError as exc:  # pragma: no cover
        return 1, "", str(exc)


def _rel(path: str, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except (ValueError, OSError):
        return str(path).replace("\\", "/")


def _excerpt(root: Path, rel_path: str, line: int | None) -> str | None:
    try:
        text = (root / rel_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return excerpt_for(text, line)


# --------------------------------------------------------------------------- #
# Individual tool runners
# --------------------------------------------------------------------------- #
def run_ruff(root: Path) -> list[RawFinding]:
    code, out, err = _run(["ruff", "check", "--output-format", "json", "--exit-zero", "."], root)
    if not out.strip():
        if err:
            logger.debug("ruff produced no output: %s", err[:200])
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    findings: list[RawFinding] = []
    for item in data:
        rule = item.get("code") or "ruff"
        loc = item.get("location") or {}
        end = item.get("end_location") or {}
        rel = _rel(item.get("filename", ""), root)
        findings.append(
            RawFinding(
                title=f"{rule}: {item.get('message', 'lint issue')}",
                severity=_ruff_severity(rule),
                category="security" if rule.startswith("S") else "lint",
                tool="ruff",
                description=item.get("message"),
                file_path=rel,
                line_number=loc.get("row"),
                end_line=end.get("row"),
                code_excerpt=_excerpt(root, rel, loc.get("row")),
                rule_id=rule,
                remediation="Run 'ruff check --fix' locally and address the reported issue.",
                confidence=0.8,
            )
        )
    return findings


def _ruff_severity(code: str) -> str:
    if code.startswith("S"):
        return "high"
    if code.startswith(("E9", "F")):
        return "medium"
    if code.startswith(("E", "W")):
        return "low"
    return "informational"


def run_bandit(root: Path) -> list[RawFinding]:
    code, out, err = _run(["bandit", "-r", ".", "-f", "json", "-q"], root)
    if not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    findings: list[RawFinding] = []
    for item in data.get("results", []):
        rel = _rel(item.get("filename", ""), root)
        line = item.get("line_number")
        cwe = item.get("issue_cwe") or {}
        cwe_id = f"CWE-{cwe.get('id')}" if cwe.get("id") else None
        findings.append(
            RawFinding(
                title=f"{item.get('test_id', 'B')}: {item.get('issue_text', 'security issue')}",
                severity=normalize_severity(item.get("issue_severity")),
                category="security",
                tool="bandit",
                description=item.get("issue_text"),
                file_path=rel,
                line_number=line,
                code_excerpt=item.get("code") or _excerpt(root, rel, line),
                rule_id=item.get("test_id"),
                cwe=cwe_id,
                remediation=item.get("more_info")
                or "Review the flagged code and remove the insecure pattern.",
                confidence={"HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.5}.get(
                    item.get("issue_confidence", ""), 0.6
                ),
            )
        )
    return findings


def run_semgrep(root: Path) -> list[RawFinding]:
    code, out, err = _run(
        [
            "semgrep", "scan", "--json", "--config=auto", "--metrics=off",
            "--timeout", "60", "--max-target-bytes", "500000", "--quiet",
        ],
        root,
        timeout=settings.tool_timeout_seconds,
    )
    if not out.strip():
        if err:
            logger.info("semgrep did not return JSON output (offline or error): %s", err[:200])
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    findings: list[RawFinding] = []
    for item in data.get("results", []):
        extra = item.get("extra", {}) or {}
        metadata = extra.get("metadata", {}) or {}
        rel = _rel(item.get("path", ""), root)
        start = (item.get("start") or {}).get("line")
        cwe = metadata.get("cwe")
        if isinstance(cwe, list):
            cwe = cwe[0] if cwe else None
        findings.append(
            RawFinding(
                title=f"{item.get('check_id', 'semgrep')}: {extra.get('message', 'pattern match')}",
                severity=normalize_severity(extra.get("severity")),
                category="security",
                tool="semgrep",
                description=extra.get("message"),
                file_path=rel,
                line_number=start,
                code_excerpt=extra.get("lines") or _excerpt(root, rel, start),
                rule_id=item.get("check_id"),
                cwe=str(cwe) if cwe else None,
                remediation=metadata.get("fix")
                or "Review the matched pattern and follow the rule guidance.",
                confidence=0.7,
            )
        )
    return findings


def run_eslint(root: Path) -> list[RawFinding]:
    if not (root / "node_modules").exists() and not (root / "package.json").exists():
        return []
    code, out, err = _run(["eslint", ".", "--format", "json", "--no-error-on-unmatched-pattern"], root)
    if not out.strip().startswith("["):
        logger.info("eslint unavailable or not configured: %s", (err or out)[:200])
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    findings: list[RawFinding] = []
    for file_result in data:
        rel = _rel(file_result.get("filePath", ""), root)
        for msg in file_result.get("messages", []):
            if not msg.get("ruleId"):
                continue
            findings.append(
                RawFinding(
                    title=f"{msg.get('ruleId')}: {msg.get('message', 'lint issue')}",
                    severity=normalize_severity(_eslint_severity(msg.get("severity"))),
                    category="lint",
                    tool="eslint",
                    description=msg.get("message"),
                    file_path=rel,
                    line_number=msg.get("line"),
                    end_line=msg.get("endLine"),
                    code_excerpt=_excerpt(root, rel, msg.get("line")),
                    rule_id=msg.get("ruleId"),
                    remediation="Fix the reported lint violation.",
                    confidence=0.75,
                )
            )
    return findings


def _eslint_severity(value) -> str:
    return "high" if value == 2 else "low"


def run_npm_audit(root: Path) -> list[RawFinding]:
    if not (root / "package-lock.json").exists():
        return []
    code, out, err = _run(["npm", "audit", "--json"], root)
    if not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    findings: list[RawFinding] = []
    vulnerabilities = data.get("vulnerabilities", {})
    for name, info in vulnerabilities.items():
        findings.append(
            RawFinding(
                title=f"Vulnerable dependency: {name}",
                severity=normalize_severity(info.get("severity")),
                category="dependency",
                tool="npm-audit",
                description=f"{name} has a known vulnerability. {info.get('via', '')}",
                file_path="package.json",
                line_number=None,
                rule_id=f"npm:{name}",
                remediation=info.get("fixAvailable")
                and "Run 'npm audit fix' to update the affected package."
                or "Update or replace the affected dependency.",
                confidence=0.9,
            )
        )
    return findings


def run_pip_audit(root: Path) -> list[RawFinding]:
    req = root / "requirements.txt"
    if not req.exists():
        return []
    code, out, err = _run(["pip-audit", "-r", "requirements.txt", "--format", "json"], root)
    if not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []
    dependencies = data.get("dependencies", data if isinstance(data, list) else [])
    findings: list[RawFinding] = []
    for dep in dependencies:
        for vuln in dep.get("vulns", []):
            findings.append(
                RawFinding(
                    title=f"Vulnerable dependency: {dep.get('name')} {dep.get('version')}",
                    severity="high",
                    category="dependency",
                    tool="pip-audit",
                    description=f"{vuln.get('id')}: {vuln.get('description', 'known vulnerability')}",
                    file_path="requirements.txt",
                    rule_id=vuln.get("id"),
                    remediation=f"Upgrade to a fixed version: {', '.join(vuln.get('fix_versions', [])) or 'latest'}",
                    confidence=0.9,
                )
            )
    return findings


RUNNERS = {
    "ruff": run_ruff,
    "bandit": run_bandit,
    "semgrep": run_semgrep,
    "eslint": run_eslint,
    "npm": run_npm_audit,
    "pip-audit": run_pip_audit,
}
