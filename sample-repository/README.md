# CodeGuard AI — Demonstration Repository

> **DEMONSTRATION DATA.** This folder is a deliberately vulnerable sample used to
> test the CodeGuard AI scanning engine. It contains **intentionally insecure
> code** and must never be deployed or executed in production.

The files here are harmless: they are never executed by CodeGuard AI (the platform
only performs static analysis and never runs repository code).

Expected findings (used as a test fixture):

| File | Issue |
|------|-------|
| `demo_vulnerable.py` | hardcoded AWS key, hardcoded password, `os.system`, `subprocess shell=True`, `eval`, MD5 hashing, bare `except` |
| `demo_script.js` | `innerHTML` assignment (XSS), `eval`, `document.write` |
| `config.yaml` | inline database password |

## Running the built-in analyzer against this folder

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.services.scanning import builtin; from pathlib import Path; import json; t=Path('../sample-repository/demo_vulnerable.py').read_text(); print(len(builtin.scan_text('demo_vulnerable.py', t, 'Python')), 'findings')"
```
