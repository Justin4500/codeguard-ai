"""Language detection and source-file selection helpers."""
from __future__ import annotations

from pathlib import Path

EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".go": "Go",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
}

PYTHON_EXTS = {".py", ".pyi"}
JS_EXTS = {".js", ".jsx", ".mjs", ".cjs"}
TS_EXTS = {".ts", ".tsx"}

EXCLUDED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", ".env", "__pycache__",
    "dist", "build", "out", "target", ".next", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "vendor", "bower_components", ".idea", ".vscode",
    "site-packages", "eggs", ".eggs", ".tox", "bin", "obj",
}

EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z", ".exe", ".dll", ".so",
    ".dylib", ".bin", ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4",
    ".mov", ".avi", ".class", ".pyc", ".pyo", ".o", ".a", ".lock", ".map",
    ".min.js", ".min.css",
}


def language_for(path: Path) -> str | None:
    return EXTENSION_LANGUAGE.get(path.suffix.lower())


def is_supported_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in EXCLUDED_EXTENSIONS:
        return False
    name = path.name.lower()
    if name.endswith(".min.js") or name.endswith(".min.css") or name.endswith(".lock"):
        return False
    return suffix in EXTENSION_LANGUAGE


def collect_source_files(
    root: Path, max_files: int, max_file_size_kb: int
) -> tuple[list[Path], dict[str, int]]:
    """Walk a repository and return supported files plus a language histogram."""
    files: list[Path] = []
    language_counts: dict[str, int] = {}
    max_bytes = max_file_size_kb * 1024

    for path in root.rglob("*"):
        if len(files) >= max_files:
            break
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not is_supported_file(path):
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        files.append(path)
        lang = language_for(path)
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    return files, language_counts


def read_text(path: Path, limit_lines: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if limit_lines is not None:
        return "\n".join(text.splitlines()[:limit_lines])
    return text
