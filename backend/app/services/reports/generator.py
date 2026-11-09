"""Report builders (JSON, CSV, HTML) generated from stored scan records."""
from __future__ import annotations

import csv
import html
import io
import json
from collections import Counter

from app.models import Finding, Repository, Scan

try:  # PDF export is optional so the rest of the report still works without it.
    from reportlab.lib import colors as _colors
    from reportlab.lib.pagesizes import A4 as _A4
    from reportlab.lib.units import mm as _mm
    from reportlab.pdfbase.pdfmetrics import stringWidth as _string_width
    from reportlab.pdfgen import canvas as _canvas

    _PDF_AVAILABLE = True
except Exception:  # noqa: BLE001
    _PDF_AVAILABLE = False


_ORDER = ["critical", "high", "medium", "low", "informational"]


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(f.severity for f in findings)
    return {sev: counts.get(sev, 0) for sev in _ORDER}


def build_json(scan: Scan, repo: Repository, findings: list[Finding]) -> dict:
    return {
        "report": "CodeGuard AI Scan Report",
        "generated_from": "CodeGuard AI",
        "repository": {
            "full_name": repo.full_name,
            "url": repo.url,
            "language": repo.language,
            "visibility": repo.visibility,
        },
        "scan": {
            "id": scan.id,
            "branch": scan.branch,
            "commit": scan.commit_sha,
            "status": scan.status,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
            "duration_seconds": scan.duration_seconds,
            "files_scanned": scan.files_scanned,
            "tools_used": scan.tools_used or [],
            "tools_skipped": scan.tools_skipped or [],
            "languages": scan.languages or [],
        },
        "summary": {
            "total_findings": len(findings),
            "by_severity": _severity_counts(findings),
        },
        "ai_summary": scan.ai_summary,
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "category": f.category,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "tool": f.tool,
                "rule_id": f.rule_id,
                "cwe": f.cwe,
                "status": f.status,
                "description": f.description,
                "remediation": f.remediation,
                "code_excerpt": f.code_excerpt,
            }
            for f in findings
        ],
        "limitations": [
            "Static analysis cannot prove the absence of vulnerabilities.",
            "Findings from tools that were not installed during the scan are not included.",
        ]
        + ([{"skipped_tools": scan.tools_skipped}] if scan.tools_skipped else []),
    }


def build_csv(findings: list[Finding]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "severity", "category", "title", "file_path", "line", "tool", "rule_id", "cwe", "status", "remediation"]
    )
    for f in findings:
        writer.writerow(
            [f.id, f.severity, f.category, f.title, f.file_path or "", f.line_number or "",
             f.tool, f.rule_id or "", f.cwe or "", f.status, (f.remediation or "").replace("\n", " ")]
        )
    return buffer.getvalue()


def build_html(scan: Scan, repo: Repository, findings: list[Finding]) -> str:
    counts = _severity_counts(findings)
    rows = []
    for f in findings:
        rows.append(
            "<tr>"
            f"<td class='sev sev-{html.escape(f.severity)}'>{html.escape(f.severity)}</td>"
            f"<td>{html.escape(f.category)}</td>"
            f"<td>{html.escape(f.title)}</td>"
            f"<td class='mono'>{html.escape(f.file_path or '')}{':' + str(f.line_number) if f.line_number else ''}</td>"
            f"<td class='mono'>{html.escape(f.tool)}{'/' + html.escape(f.rule_id) if f.rule_id else ''}</td>"
            f"<td>{html.escape(f.status)}</td>"
            "</tr>"
        )
    summary_cards = "".join(
        f"<div class='card'><span class='k'>{sev.title()}</span><span class='v'>{counts[sev]}</span></div>"
        for sev in _ORDER
    )
    tools = ", ".join(scan.tools_used or []) or "codeguard-builtin"
    skipped = ", ".join(t.get("tool", "") for t in (scan.tools_skipped or [])) or "none"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<title>CodeGuard AI Report — {html.escape(repo.full_name)}</title>
<style>
 :root{{color-scheme:dark}}
 body{{background:#0b0d10;color:#e5e7eb;font-family:Inter,Segoe UI,system-ui,sans-serif;margin:0;padding:40px}}
 h1,h2{{font-weight:600}} .mono{{font-family:ui-monospace,Consolas,monospace;font-size:12px}}
 .meta{{color:#9ca3af;font-size:13px;margin-bottom:24px}}
 .grid{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}}
 .card{{background:#14171c;border:1px solid #23272e;border-radius:10px;padding:14px 18px;min-width:120px}}
 .k{{display:block;color:#9ca3af;font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
 .v{{font-size:26px;font-weight:600}}
 table{{width:100%;border-collapse:collapse;margin-top:20px;font-size:13px}}
 th{{text-align:left;color:#9ca3af;border-bottom:1px solid #23272e;padding:10px;font-weight:500}}
 td{{border-bottom:1px solid #1b1f25;padding:10px}}
 .sev{{font-weight:600}}
 .sev-critical{{color:#f87171}} .sev-high{{color:#fb923c}} .sev-medium{{color:#facc15}}
 .sev-low{{color:#60a5fa}} .sev-informational{{color:#9ca3af}}
 .note{{color:#9ca3af;font-size:12px;margin-top:24px}}
</style></head><body>
<h1>CodeGuard AI — Scan Report</h1>
<div class="meta">
 Repository: <strong>{html.escape(repo.full_name)}</strong> &middot;
 Branch: {html.escape(scan.branch or '-')} &middot;
 Commit: <span class="mono">{html.escape((scan.commit_sha or '-')[:12])}</span><br/>
 Scan #{scan.id} &middot; Status: {html.escape(scan.status)} &middot;
 Files scanned: {scan.files_scanned} &middot; Duration: {round(scan.duration_seconds or 0, 2)}s<br/>
 Tools used: {html.escape(tools)} &middot; Tools skipped: {html.escape(skipped)}
</div>
<h2>Summary</h2>
<div class="grid"><div class="card"><span class="k">Total</span><span class="v">{len(findings)}</span></div>{summary_cards}</div>
<h2>Findings</h2>
<table><thead><tr><th>Severity</th><th>Category</th><th>Title</th><th>Location</th><th>Tool / Rule</th><th>Status</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan="6">No findings recorded for this scan.</td></tr>'}</tbody></table>
<p class="note">Generated by CodeGuard AI from real static-analysis output. Static analysis cannot prove the absence of vulnerabilities.
Findings from tools that were not installed are excluded and listed as skipped above.</p>
</body></html>"""


def to_bytes(content: str) -> bytes:
    return content.encode("utf-8")


def json_dumps(data: dict) -> str:
    return json.dumps(data, indent=2, default=str)


# --------------------------------------------------------------------------- #
# PDF report
# --------------------------------------------------------------------------- #
_SEV_COLOR = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
    "informational": "#64748b",
}

# Plain-language explanations so non-developers understand each issue.
# rule_id -> (what it is, why it matters, how to fix)
_PLAIN_ISSUES: dict[str, tuple[str, str, str]] = {
    "CG-SEC-001": (
        "A cloud access key appears to be written directly in the code.",
        "Anyone who can read this code could use the key to reach your cloud account.",
        "Remove the key, replace (rotate) it, and load it from a safe settings file instead.",
    ),
    "CG-SEC-002": (
        "A private encryption key is stored in the code.",
        "A leaked private key lets an attacker impersonate your server or decrypt your data.",
        "Delete the key from the code and keep it in a secure secret store.",
    ),
    "CG-SEC-003": (
        "An API key or secret is hardcoded in the code.",
        "Hardcoded secrets leak through version control and end up in the wrong hands.",
        "Move the value to an environment variable and rotate the exposed key.",
    ),
    "CG-SEC-004": (
        "A password is written directly in the code.",
        "Storing passwords in code is easy to leak and hard to change safely.",
        "Use environment variables or a secrets manager instead of hardcoding it.",
    ),
    "CG-SEC-005": (
        "A GitHub token was found in the source code.",
        "A leaked token can let someone push code or read your private repositories.",
        "Revoke the token on GitHub and load it from a secure environment variable.",
    ),
    "CG-SEC-006": (
        "A Google API key was found in the source code.",
        "Exposed keys can be abused and may cost you money or expose data.",
        "Restrict and rotate the key; never embed it in source code.",
    ),
    "CG-SEC-007": (
        "A Slack token was found in the source code.",
        "A leaked Slack token lets an attacker read or post in your workspace.",
        "Rotate the token and store it in a secret manager.",
    ),
    "CG-SEC-008": (
        "A live payment (Stripe) secret key is in the code.",
        "This key can move real money; leaking it is very serious.",
        "Rotate the key immediately and keep it server-side only.",
    ),
    "CG-SEC-009": (
        "A database connection string contains a password.",
        "Anyone with the string can connect to your database and read or change data.",
        "Move database credentials out of the code and into configuration.",
    ),
    "CG-SEC-010": (
        "A login (JWT) token is hardcoded in the code.",
        "A fixed token can be reused by an attacker until it expires.",
        "Get tokens at runtime and never commit them.",
    ),
    "CG-SEC-020": (
        "The code uses eval(), which runs text as if it were code.",
        "If any of that text comes from a user, an attacker can run their own code.",
        "Avoid eval(); use a safe parser such as JSON.parse or ast.literal_eval.",
    ),
    "CG-SEC-020b": (
        "The code uses eval() or exec(), which run text as code.",
        "Untrusted input here can turn into full code execution.",
        "Avoid eval()/exec(); use safer alternatives.",
    ),
    "CG-SEC-021": (
        "The code builds a function from a string (new Function).",
        "If the string is attacker-controlled, it can execute arbitrary code.",
        "Prefer normal, static code instead of building functions from strings.",
    ),
    "CG-SEC-022": (
        "Text is inserted into the page as raw HTML (innerHTML).",
        "This can let an attacker run scripts in your users' browsers (XSS).",
        "Use textContent, or clean the HTML with a library such as DOMPurify.",
    ),
    "CG-SEC-023": (
        "The code renders raw HTML (dangerouslySetInnerHTML).",
        "Uncleaned HTML can run attacker scripts in the browser (XSS).",
        "Sanitize the HTML before rendering and never trust user input here.",
    ),
    "CG-SEC-024": (
        "The code uses document.write().",
        "It can overwrite the page and is a common source of XSS bugs.",
        "Use safe DOM APIs instead of document.write().",
    ),
    "CG-SEC-025": (
        "The code launches a system command (child_process).",
        "If user input reaches the command, it can run any program on your machine.",
        "Use execFile with fixed arguments and validate all input.",
    ),
    "CG-SEC-030b": (
        "The code calls os.system() to run a shell command.",
        "User input reaching this call can run arbitrary commands on the server.",
        "Use subprocess.run with an argument list and shell=False.",
    ),
    "CG-SEC-031": (
        "A weak hashing algorithm (MD5 or SHA-1) is used.",
        "These algorithms are broken; attackers can forge or reverse them.",
        "Use SHA-256 for integrity, and bcrypt/argon2 for passwords.",
    ),
    "CG-SEC-032": (
        "Untrusted data is being deserialized with pickle/marshal.",
        "Loading a pickle can run arbitrary code from the data itself.",
        "Never unpickle untrusted data; use JSON or a safe format.",
    ),
    "CG-SEC-032b": (
        "Data is being loaded with pickle/marshal.",
        "If the data ever comes from an untrusted source, it can execute code.",
        "Avoid pickle for untrusted data; use JSON or a safe format.",
    ),
    "CG-SEC-033": (
        "YAML is loaded without the safe loader.",
        "Unsafe YAML can construct objects and run code while parsing.",
        "Use yaml.safe_load() or pass Loader=yaml.SafeLoader.",
    ),
    "CG-SEC-034": (
        "The application runs with debug mode switched on.",
        "Debug mode can expose an interactive console that runs code on your server.",
        "Turn debug off in production.",
    ),
    "CG-SEC-035": (
        "Cross-origin requests are allowed from any website (CORS '*').",
        "Any site can call your API on a user's behalf, which can leak data.",
        "Restrict allowed origins to the domains you trust.",
    ),
    "CG-SEC-036": (
        "A SQL query is built by joining strings together.",
        "This is the classic SQL-injection pattern; attackers can read or destroy data.",
        "Use parameterized queries instead of string concatenation.",
    ),
    "CG-SEC-037": (
        "A command is run with shell=True.",
        "Shell mode lets extra commands sneak in through user input.",
        "Pass a list of arguments and set shell=False.",
    ),
    "CG-SEC-038": (
        "A temporary file is created in an unsafe way (tempfile.mktemp).",
        "Another process can guess the file name and hijack it.",
        "Use tempfile.mkstemp or NamedTemporaryFile.",
    ),
    "CG-QUA-040": (
        "An error handler catches everything (bare except).",
        "Real problems get hidden and the program may continue in a broken state.",
        "Catch the specific exception types you expect.",
    ),
    "CG-QUA-041": (
        "A value is compared using 'is' instead of '=='.",
        "'is' checks identity, not value, so the comparison can silently be wrong.",
        "Use '==' for value comparisons.",
    ),
    "CG-BUG-001": (
        "The file could not be parsed because of a syntax error.",
        "Broken syntax means the file will not run and cannot be fully analysed.",
        "Fix the syntax error highlighted at this location.",
    ),
}


def _sanitize(text: object) -> str:
    """Make text safe for the built-in PDF fonts (latin-1)."""
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _plain_issue(finding: Finding) -> tuple[str, str, str]:
    mapped = _PLAIN_ISSUES.get(finding.rule_id or "")
    if mapped:
        return mapped
    what = finding.title or "Issue detected"
    why = finding.description or "This pattern is often associated with security or quality problems."
    fix = finding.remediation or "Review this finding and apply a safe fix."
    return what, why, fix


def _is_test_or_example(path: str | None) -> bool:
    if not path:
        return False
    parts = path.replace("\\", "/").lower().split("/")
    name = parts[-1]
    if name.startswith("test_") or name.endswith("_test.py") or name.startswith("conftest"):
        return True
    if ".test." in name or ".spec." in name:
        return True
    folders = set(parts[:-1])
    return bool(folders & {"test", "tests", "testing", "spec", "specs", "__tests__", "examples", "example", "samples"})


def _strengths(scan: Scan, repo: Repository, findings: list[Finding]) -> list[str]:
    counts = _severity_counts(findings)
    out: list[str] = []
    if scan.files_scanned:
        out.append(f"The scan analysed {scan.files_scanned} file(s) successfully without errors.")
    if counts["critical"] == 0 and counts["high"] == 0:
        out.append("No critical or high-severity issues were found.")
    secrets = [f for f in findings if (f.rule_id or "").startswith(("CG-SEC-00",))]
    if not secrets:
        out.append("No hardcoded secrets, tokens or passwords were detected in the scanned code.")
    langs = scan.languages or []
    if langs:
        top = max(langs, key=lambda item: item.get("files", 0))
        out.append(f"Primary language detected: {top.get('language')} ({top.get('files')} files).")
    if scan.tools_used:
        out.append("Automated checks that ran: " + ", ".join(str(t) for t in scan.tools_used) + ".")
    if repo.language:
        out.append(f"Repository classified as {repo.language}.")
    if not out:
        out.append("The scan completed without process errors.")
    return out


def _concerns(findings: list[Finding]) -> list[tuple[str, str]]:
    counts = _severity_counts(findings)
    out: list[tuple[str, str]] = []
    if counts["critical"]:
        out.append((f"{counts['critical']} critical issue(s) that should be fixed first.", "#dc2626"))
    if counts["high"]:
        out.append((f"{counts['high']} high-severity issue(s) that need attention soon.", "#ea580c"))
    if counts["medium"]:
        out.append((f"{counts['medium']} medium-severity issue(s) to plan for.", "#ca8a04"))
    if counts["low"]:
        out.append((f"{counts['low']} low-severity / code-quality note(s).", "#2563eb"))
    if not findings:
        out.append(("No issues were detected in this scan.", "#16a34a"))
    return out


def _verdict(findings: list[Finding]) -> tuple[str, str, str]:
    counts = _severity_counts(findings)
    if counts["critical"]:
        return ("High risk", f"{counts['critical']} critical issue(s) require immediate attention.", "#dc2626")
    if counts["high"]:
        return ("Elevated risk", f"{counts['high']} high-severity issue(s) should be reviewed soon.", "#ea580c")
    if counts["medium"]:
        return ("Moderate risk", f"{counts['medium']} medium-severity issue(s) to schedule.", "#ca8a04")
    if counts["low"] or counts["informational"]:
        return ("Low risk", "Only minor code-quality notes were found.", "#2563eb")
    return ("Clean", "No issues were detected in this scan.", "#16a34a")


class _ReportPDF:
    """A tiny flowing-layout helper around the reportlab canvas."""

    def __init__(self) -> None:
        self.buffer = io.BytesIO()
        self.c = _canvas.Canvas(self.buffer, pagesize=_A4)
        self.w, self.h = _A4
        self.m = 16 * _mm
        self.y = self.h - self.m
        self.page = 1

    def _footer(self) -> None:
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(_colors.HexColor("#94a3b8"))
        self.c.drawString(self.m, 10 * _mm, "Generated by CodeGuard AI - static analysis report")
        self.c.drawRightString(self.w - self.m, 10 * _mm, f"Page {self.page}")

    def new_page(self) -> None:
        self._footer()
        self.c.showPage()
        self.page += 1
        self.y = self.h - self.m

    def need(self, height: float) -> None:
        if self.y - height < self.m + 8 * _mm:
            self.new_page()

    def title(self, text: str) -> None:
        self.c.setFillColor(_colors.HexColor("#0f172a"))
        self.c.setFont("Helvetica-Bold", 18)
        self.c.drawString(self.m, self.y - 16, _sanitize(text))
        self.y -= 24

    def meta(self, lines: list[str]) -> None:
        self.c.setFont("Helvetica", 9)
        self.c.setFillColor(_colors.HexColor("#64748b"))
        for line in lines:
            self.c.drawString(self.m, self.y - 10, _sanitize(line))
            self.y -= 13
        self.y -= 4

    def heading(self, text: str, size: float = 12.5) -> None:
        self.need(size + 10 * _mm)
        self.y -= 3 * _mm
        self.c.setFillColor(_colors.HexColor("#0f172a"))
        self.c.setFont("Helvetica-Bold", size)
        self.c.drawString(self.m, self.y - size, _sanitize(text))
        self.y -= size + 2 * _mm

    def para(self, text: str, size: float = 9.5, color: str = "#1f2937", gap: float = 2 * _mm, indent: float = 0.0) -> None:
        wrap_width = self.w - 2 * self.m - indent
        lines: list[str] = []
        current = ""
        for word in _sanitize(text).split():
            candidate = f"{current} {word}".strip()
            if current and _string_width(candidate, "Helvetica", size) > wrap_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        self.c.setFont("Helvetica", size)
        self.c.setFillColor(_colors.HexColor(color))
        for line in lines:
            self.need(size + 4)
            self.c.drawString(self.m + indent, self.y - size, line)
            self.y -= size * 1.4
        self.y -= gap

    def bullets(self, items: list[tuple[str, str]]) -> None:
        for text, color in items:
            self.c.setFillColor(_colors.HexColor(color))
            self.c.circle(self.m + 4, self.y - 6, 1.6, stroke=0, fill=1)
            wrap_width = self.w - 2 * self.m - 12
            lines: list[str] = []
            current = ""
            for word in _sanitize(text).split():
                candidate = f"{current} {word}".strip()
                if current and _string_width(candidate, "Helvetica", 9.5) > wrap_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
            self.c.setFont("Helvetica", 9.5)
            for i, line in enumerate(lines):
                self.need(14)
                self.c.setFillColor(_colors.HexColor("#1f2937"))
                self.c.drawString(self.m + 12, self.y - 9, line)
                self.y -= 13
            self.y -= 2

    def banner(self, title: str, subtitle: str, color: str) -> None:
        box_h = 15 * _mm
        self.need(box_h + 6 * _mm)
        self.c.setFillColor(_colors.HexColor(color))
        self.c.roundRect(self.m, self.y - box_h, self.w - 2 * self.m, box_h, 2 * _mm, stroke=0, fill=1)
        self.c.setFillColor(_colors.white)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawString(self.m + 4 * _mm, self.y - 6 * _mm, _sanitize(title))
        self.c.setFont("Helvetica", 9)
        self.c.drawString(self.m + 4 * _mm, self.y - 11 * _mm, _sanitize(subtitle))
        self.y -= box_h + 4 * _mm

    def severity_chart(self, counts: dict[str, int]) -> None:
        data = [(sev, counts.get(sev, 0)) for sev in _ORDER]
        max_value = max([v for _, v in data] + [1])
        bar_h, gap = 7 * _mm, 2.5 * _mm
        self.need(len(data) * (bar_h + gap) + 6 * _mm)
        label_w, value_w = 26 * _mm, 12 * _mm
        chart_w = self.w - 2 * self.m - label_w - value_w
        for i, (sev, value) in enumerate(data):
            top = self.y - (i + 1) * (bar_h + gap)
            self.c.setFont("Helvetica", 9)
            self.c.setFillColor(_colors.HexColor("#374151"))
            self.c.drawString(self.m, top + 1.5 * _mm, sev.title())
            if value:
                width = max(2, chart_w * value / max_value)
                self.c.setFillColor(_colors.HexColor(_SEV_COLOR[sev]))
                self.c.rect(self.m + label_w, top + 1 * _mm, width, bar_h - 2 * _mm, stroke=0, fill=1)
            self.c.setFillColor(_colors.HexColor("#374151"))
            self.c.drawString(self.m + label_w + chart_w + 2 * _mm, top + 1.5 * _mm, str(value))
        self.y -= len(data) * (bar_h + gap) + 3 * _mm

    def flow(self, steps: list[str]) -> None:
        box_h, gap = 9 * _mm, 6 * _mm
        self.need(len(steps) * (box_h + gap) + 4 * _mm)
        box_w = 118 * _mm
        x = self.m + 2 * _mm
        cx = x + box_w / 2
        for i, label in enumerate(steps):
            top = self.y - (i + 1) * (box_h + gap) + gap
            self.c.setFillColor(_colors.HexColor("#eef2ff"))
            self.c.setStrokeColor(_colors.HexColor("#6366f1"))
            self.c.roundRect(x, top, box_w, box_h, 2 * _mm, stroke=1, fill=1)
            self.c.setFillColor(_colors.HexColor("#1e293b"))
            self.c.setFont("Helvetica-Bold", 9)
            self.c.drawCentredString(cx, top + box_h / 2 - 3, _sanitize(label))
            if i < len(steps) - 1:
                y0, y1 = top, top - gap
                self.c.setStrokeColor(_colors.HexColor("#6366f1"))
                self.c.setLineWidth(1)
                self.c.line(cx, y0, cx, y1 + 4)
                path = self.c.beginPath()
                path.moveTo(cx, y1)
                path.lineTo(cx - 4, y1 + 5)
                path.lineTo(cx + 4, y1 + 5)
                path.close()
                self.c.setFillColor(_colors.HexColor("#6366f1"))
                self.c.drawPath(path, stroke=0, fill=1)
        self.y -= len(steps) * (box_h + gap) + 3 * _mm

    def finding_block(self, index: int, finding: Finding) -> None:
        what, why, fix = _plain_issue(finding)
        location = (finding.file_path or "unknown") + (f":{finding.line_number}" if finding.line_number else "")
        tag_h = 7 * _mm
        # Estimate the block height so we can avoid awkward splits.
        self.need(tag_h + 30 * _mm)
        color = _SEV_COLOR.get(finding.severity, "#64748b")
        self.c.setFillColor(_colors.HexColor(color))
        self.c.roundRect(self.m, self.y - tag_h, 24 * _mm, tag_h, 1.5 * _mm, stroke=0, fill=1)
        self.c.setFillColor(_colors.white)
        self.c.setFont("Helvetica-Bold", 8)
        self.c.drawString(self.m + 2 * _mm, self.y - 4.8 * _mm, _sanitize(finding.severity.upper()))
        self.c.setFillColor(_colors.HexColor("#0f172a"))
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(self.m + 27 * _mm, self.y - 5 * _mm, _sanitize(f"{index}. {finding.title}"))
        self.y -= tag_h + 1 * _mm
        suffix = "  [in test/example code - may be intentional]" if _is_test_or_example(finding.file_path) else ""
        self.para(f"Location: {location}    Tool: {finding.tool}{'/' + finding.rule_id if finding.rule_id else ''}{'    ' + finding.cwe if finding.cwe else ''}{suffix}",
                  size=8, color="#64748b", gap=1 * _mm)
        self.para(f"What it is: {what}", size=9, gap=0.5 * _mm)
        self.para(f"Why it matters: {why}", size=9, gap=0.5 * _mm)
        self.para(f"How to fix: {fix}", size=9, gap=3 * _mm)


def build_pdf(scan: Scan, repo: Repository, findings: list[Finding]) -> bytes:
    if not _PDF_AVAILABLE:
        raise RuntimeError("PDF export requires the 'reportlab' package to be installed.")
    counts = _severity_counts(findings)
    pdf = _ReportPDF()
    pdf.title("CodeGuard AI - Scan Report")
    commit = (scan.commit_sha or "-")[:12]
    pdf.meta([
        f"Repository: {repo.full_name}",
        f"Branch: {scan.branch or '-'}    Commit: {commit}    Scan #{scan.id}",
        f"Status: {scan.status}    Files scanned: {scan.files_scanned}    Duration: {round(scan.duration_seconds or 0, 2)}s",
        f"Tools used: {', '.join(str(t) for t in (scan.tools_used or [])) or 'codeguard-builtin'}",
    ])

    verdict, verdict_note, verdict_color = _verdict(findings)
    pdf.banner(f"Overall risk: {verdict}", verdict_note, verdict_color)

    pdf.para(f"Total issues found: {len(findings)}", size=10, color="#0f172a", gap=3 * _mm)
    pdf.heading("Issues by severity")
    pdf.severity_chart(counts)

    pdf.heading("What's good (strengths)")
    pdf.bullets([(s, "#16a34a") for s in _strengths(scan, repo, findings)])

    pdf.heading("What needs attention (issues)")
    pdf.bullets(_concerns(findings))

    pdf.new_page()
    pdf.heading("How the scan works")
    pdf.flow([
        "1. Add GitHub repository (URL + optional token)",
        "2. Clone a temporary copy on the server",
        "3. Detect languages and select scanners",
        "4. Run built-in + external analyzers",
        "5. Normalise and remove duplicate findings",
        "6. Save findings to the database",
        "7. Generate fix proposals (you approve each one)",
        "8. Export this report (HTML / JSON / CSV / PDF)",
    ])

    pdf.heading(f"Findings ({len(findings)})")
    if not findings:
        pdf.para("No issues were detected in this scan.", size=10, color="#16a34a")
    else:
        for i, finding in enumerate(findings, start=1):
            pdf.finding_block(i, finding)

    pdf._footer()
    pdf.c.save()
    return pdf.buffer.getvalue()

