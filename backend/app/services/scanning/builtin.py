"""Built-in static analysis engine.

This runs without any external dependency and always produces real findings,
so the platform remains useful even when external scanners are not installed.
It combines regex-based secret/security rules with Python AST checks.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from app.services.scanning.normalized import RawFinding, excerpt_for

TOOL = "codeguard-builtin"

# (rule_id, title, severity, category, cwe, regex, remediation)
SecretRule = tuple[str, str, str, str, str | None, re.Pattern, str]

_SECRET_RULES: list[SecretRule] = [
    (
        "CG-SEC-001", "Possible hardcoded AWS access key", "critical", "security", "CWE-798",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "Remove the credential from source, rotate it immediately, and load it from a secret manager or environment variable.",
    ),
    (
        "CG-SEC-002", "Possible hardcoded private key", "critical", "security", "CWE-798",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
        "Never commit private keys. Revoke the key and store it in a secure secret store.",
    ),
    (
        "CG-SEC-003", "Possible hardcoded API key or secret", "high", "security", "CWE-798",
        re.compile(
            r"(?i)\b(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b\s*[:=]\s*[\"'][A-Za-z0-9_\-./+]{12,}[\"']"
        ),
        "Move the secret to an environment variable or secret manager and rotate the exposed value.",
    ),
    (
        "CG-SEC-004", "Possible hardcoded password", "high", "security", "CWE-798",
        re.compile(r"(?i)\b(password|passwd|pwd|passphrase)\b\s*[:=]\s*[\"'][^\"']{6,}[\"']"),
        "Do not hardcode passwords. Use environment variables or a secrets manager.",
    ),
    (
        "CG-SEC-005", "GitHub token detected in source", "critical", "security", "CWE-798",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        "Revoke the token on GitHub and load it from a secure environment variable.",
    ),
    (
        "CG-SEC-006", "Google API key detected in source", "high", "security", "CWE-798",
        re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
        "Restrict and rotate the Google API key; do not embed it in source code.",
    ),
    (
        "CG-SEC-007", "Slack token detected in source", "high", "security", "CWE-798",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
        "Rotate the Slack token and store it in a secret manager.",
    ),
    (
        "CG-SEC-008", "Stripe secret key detected in source", "critical", "security", "CWE-798",
        re.compile(r"\bsk_live_[0-9A-Za-z]{20,}\b"),
        "Rotate the Stripe key immediately and keep it server-side only.",
    ),
    (
        "CG-SEC-009", "Database URL contains an inline password", "high", "security", "CWE-798",
        re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:@/]+:[^\s@/]+@"),
        "Move database credentials out of connection strings and into environment configuration.",
    ),
    (
        "CG-SEC-010", "JWT token hardcoded in source", "medium", "security", "CWE-798",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}\b"),
        "Do not hardcode JWTs; obtain them at runtime and never commit them.",
    ),
]

# Language-agnostic dangerous-API rules.
_CODE_RULES: list[tuple] = [
    (
        "CG-SEC-020", "Use of eval() can enable code injection", "high", "security", "CWE-95",
        re.compile(r"(?<![\w.])eval\s*\("),
        {"JavaScript", "TypeScript"},
        "Avoid eval(); use a safe parser (e.g. JSON.parse) instead.",
    ),
    (
        "CG-SEC-021", "Dynamic code execution via new Function()", "high", "security", "CWE-95",
        re.compile(r"\bnew\s+Function\s*\("),
        {"JavaScript", "TypeScript"},
        "Avoid constructing functions from strings; prefer static code paths.",
    ),
    (
        "CG-SEC-022", "Unsafe innerHTML assignment (XSS risk)", "high", "security", "CWE-79",
        re.compile(r"\.innerHTML\s*="),
        {"JavaScript", "TypeScript"},
        "Use textContent or a sanitizer such as DOMPurify before inserting HTML.",
    ),
    (
        "CG-SEC-023", "dangerouslySetInnerHTML usage (XSS risk)", "medium", "security", "CWE-79",
        re.compile(r"dangerouslySetInnerHTML"),
        {"JavaScript", "TypeScript"},
        "Sanitize the HTML payload before rendering and avoid untrusted input here.",
    ),
    (
        "CG-SEC-024", "Use of document.write()", "medium", "security", "CWE-79",
        re.compile(r"\bdocument\.write\s*\("),
        {"JavaScript", "TypeScript"},
        "Manipulate the DOM with safe APIs instead of document.write().",
    ),
    (
        "CG-SEC-025", "Command execution via child_process", "high", "security", "CWE-78",
        re.compile(r"child_process|execSync\s*\(|spawnSync\s*\("),
        {"JavaScript", "TypeScript"},
        "Avoid shelling out; if required, use execFile with fixed arguments and validate input.",
    ),
    (
        "CG-SEC-031", "Weak hash algorithm (MD5/SHA1)", "medium", "security", "CWE-327",
        re.compile(r"(?i)\b(?:hashlib\.)?(?:md5|sha1)\b|createHash\(\s*[\"'](?:md5|sha1)[\"']"),
        {"Python", "JavaScript", "TypeScript"},
        "Use a strong hash such as SHA-256, or a password KDF (bcrypt/argon2) for passwords.",
    ),
    (
        "CG-SEC-032", "Insecure deserialization (pickle/marshal)", "critical", "security", "CWE-502",
        re.compile(r"\b(?:pickle|cPickle|marshal)\.loads?\s*\("),
        {"Python"},
        "Never unpickle untrusted data; use JSON or a safe format.",
    ),
    (
        "CG-SEC-033", "yaml.load without SafeLoader", "high", "security", "CWE-502",
        re.compile(r"yaml\.load\s*\((?![^)]*SafeLoader)"),
        {"Python"},
        "Use yaml.safe_load() or pass Loader=yaml.SafeLoader.",
    ),
    (
        "CG-SEC-034", "Flask application running with debug=True", "medium", "security", "CWE-489",
        re.compile(r"debug\s*=\s*True"),
        {"Python"},
        "Disable debug mode in production; it enables an interactive debugger.",
    ),
    (
        "CG-SEC-035", "Permissive CORS configuration", "medium", "security", "CWE-942",
        re.compile(r"allow_origins\s*=\s*\[\s*[\"']\*[\"']"),
        {"Python", "JavaScript", "TypeScript"},
        "Restrict allowed origins to trusted domains instead of '*'.",
    ),
    (
        "CG-SEC-036", "SQL query built with string concatenation", "high", "security", "CWE-89",
        re.compile(r"(?i)execute\s*\(\s*[\"'][^\"']*(?:\+|%s|\{)[^\"']*[\"']\s*(?:%|\+|\.format|\+\s*)"),
        {"Python"},
        "Use parameterized queries instead of concatenating user input into SQL.",
    ),
]

_PY_AST_TOOL = TOOL


def scan_text(path: str, text: str, language: str | None) -> list[RawFinding]:
    findings: list[RawFinding] = []
    findings.extend(_scan_lines(path, text, language))
    if language == "Python":
        findings.extend(_scan_python_ast(path, text))
    return findings


def _scan_lines(path: str, text: str, language: str | None) -> list[RawFinding]:
    results: list[RawFinding] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # skip obvious comments for secret heuristics to reduce noise
        for rule_id, title, severity, category, cwe, pattern, remediation in _SECRET_RULES:
            if pattern.search(line):
                if stripped.startswith(("#", "//", "*", "/*")):
                    continue
                results.append(
                    RawFinding(
                        title=title,
                        severity=severity,
                        category=category,
                        tool=TOOL,
                        description=f"{title} detected in {path} at line {idx}.",
                        file_path=path,
                        line_number=idx,
                        code_excerpt=excerpt_for(text, idx),
                        rule_id=rule_id,
                        cwe=cwe,
                        remediation=remediation,
                        confidence=0.8 if severity in {"critical", "high"} else 0.6,
                    )
                )
        for rule_id, title, severity, category, cwe, pattern, langs, remediation in _CODE_RULES:
            if language and langs and language not in langs:
                continue
            if stripped.startswith(("#", "//", "*", "/*")):
                continue
            if pattern.search(line):
                results.append(
                    RawFinding(
                        title=title,
                        severity=severity,
                        category=category,
                        tool=TOOL,
                        description=f"{title} in {path} at line {idx}.",
                        file_path=path,
                        line_number=idx,
                        code_excerpt=excerpt_for(text, idx),
                        rule_id=rule_id,
                        cwe=cwe,
                        remediation=remediation,
                        confidence=0.65,
                    )
                )
    return results


def _scan_python_ast(path: str, text: str) -> list[RawFinding]:
    results: list[RawFinding] = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [
            RawFinding(
                title="Python syntax error prevents analysis",
                severity="high",
                category="bug",
                tool=TOOL,
                description=f"{path} could not be parsed by the Python AST: {exc.msg}",
                file_path=path,
                line_number=exc.lineno,
                code_excerpt=excerpt_for(text, exc.lineno),
                rule_id="CG-BUG-001",
                remediation="Fix the syntax error so the file can be analyzed and executed.",
                confidence=0.9,
            )
        ]

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = _call_name(func)
            lineno = getattr(node, "lineno", None)
            if name in {"eval", "exec"}:
                results.append(_mk(path, text, "CG-SEC-020b", f"Use of {name}() enables code injection",
                                   "high", "security", lineno, "CWE-95",
                                   f"Avoid {name}(); use safer alternatives like ast.literal_eval."))
            elif name in {"os.system"}:
                results.append(_mk(path, text, "CG-QUA-030b", "os.system() command injection risk",
                                   "high", "security", lineno, "CWE-78",
                                   "Use subprocess.run with an argument list and shell=False."))
            elif name in {"pickle.loads", "cPickle.loads", "marshal.loads"}:
                results.append(_mk(path, text, "CG-SEC-032b", "Insecure deserialization",
                                   "critical", "security", lineno, "CWE-502",
                                   "Avoid deserializing untrusted data with pickle/marshal."))
            elif name in {"subprocess.call", "subprocess.run", "subprocess.Popen", "subprocess.check_output"}:
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        results.append(_mk(path, text, "CG-SEC-037", "subprocess called with shell=True",
                                           "high", "security", lineno, "CWE-78",
                                           "Pass an argument list and set shell=False to avoid command injection."))
            elif name in {"tempfile.mktemp"}:
                results.append(_mk(path, text, "CG-SEC-038", "Insecure temporary file creation",
                                   "medium", "security", lineno, "CWE-377",
                                   "Use tempfile.mkstemp or NamedTemporaryFile instead of mktemp."))
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            results.append(_mk(path, text, "CG-QUA-040", "Bare except clause",
                               "low", "quality", getattr(node, "lineno", None), None,
                               "Catch specific exception types so failures are not silently swallowed."))
        elif isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, ast.Is) and isinstance(comparator, ast.Constant) and comparator.value is not None:
                    results.append(_mk(path, text, "CG-QUA-041", "Value compared with 'is' to a literal",
                                       "low", "bug", getattr(node, "lineno", None), None,
                                       "Use '==' for value comparison; 'is' compares identity."))
                    break
    return results


def _mk(path, text, rule_id, title, severity, category, line, cwe, remediation) -> RawFinding:
    return RawFinding(
        title=title,
        severity=severity,
        category=category,
        tool=_PY_AST_TOOL,
        description=f"{title} in {path}" + (f" at line {line}." if line else "."),
        file_path=path,
        line_number=line,
        code_excerpt=excerpt_for(text, line),
        rule_id=rule_id,
        cwe=cwe,
        remediation=remediation,
        confidence=0.75,
    )


def _call_name(func: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))
