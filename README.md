# CodeGuard AI

AI-powered GitHub repository code review and bug detection platform.

CodeGuard AI clones a real GitHub repository, runs **genuine static-analysis tooling** against it,
normalizes the results, explains each finding, and proposes **reviewable, reversible fixes**.
It never modifies your repository and never pushes to GitHub.

Everything works **without an AI key** — a built-in deterministic analyzer always produces real
results. Configuring an OpenAI-compatible provider only adds richer explanations and fix suggestions.

---

## 1. Requirements

| Tool    | Version used during development |
|---------|---------------------------------|
| Python  | 3.14.0                          |
| Node.js | v22.20.0                        |
| npm     | 10.9.3                          |
| Git     | 2.51.1                          |

The scanning tools below are **optional**. Any that are missing are detected and reported as
"skipped" in the scan result — they are never faked.

- Python: `ruff`, `bandit`, `semgrep`, `pip-audit`
- JavaScript: `eslint` (via `npx`), `npm` (for `npm audit`)

The built-in analyzer always runs and requires no extra installation.

---

## 2. Quick start (Windows PowerShell)

Open **two** PowerShell terminals.

### Terminal 1 — Backend (FastAPI)

```powershell
cd d:\CODEGUARD-AI-18\backend

# Create and activate a virtual environment (skip if .venv already exists)
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the API (http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks script activation, run once:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

You can also run without activating the environment:

```powershell
cd d:\CODEGUARD-AI-18\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

- API root: <http://127.0.0.1:8000/>
- Interactive docs (Swagger): <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/health>

### Terminal 2 — Frontend (React + Vite)

```powershell
cd d:\CODEGUARD-AI-18\frontend
npm install
npm run dev
```

Open <http://localhost:5173/> in your browser. The dev server proxies `/api` to the backend
at `http://127.0.0.1:8000`, so no CORS setup is needed in development.

### First steps in the UI

1. Create an account on **/signup** (or sign in).
2. Go to **Repositories → Add repository** and paste a GitHub URL, e.g.
   `https://github.com/psf/requests`.
   For a private repository, also paste a read-only token (`ghp_…`).
3. Click **Scan now**. The scan runs in the background; the scan page updates live.
4. Open **Findings**, click a finding, then **Review fixes** to generate and review a patch.

---

## 3. Optional: enable AI

Copy `.env.example` to `.env` in the project root and fill in a provider. Without these values the
app runs fully in offline mode.

```powershell
cd d:\CODEGUARD-AI-18
Copy-Item .env.example .env
```

Then edit `.env` (any OpenAI-compatible provider works):

```ini
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=sk-your-key-here
AI_MODEL=deepseek-chat
```

Supported examples already documented in `.env.example`: DeepSeek, Alibaba Qwen (DashScope),
SiliconFlow, and Google Gemini. API keys live **only** in the backend environment — they are never
sent to the browser. Code is only shared with a provider when you explicitly enable
**"Allow sending code to the AI provider"** in Settings.

---

## 4. Production build (frontend)

```powershell
cd d:\CODEGUARD-AI-18\frontend
npm run build      # type-checks with tsc, then builds to dist\
npm run preview    # optional: serve the production build
```

---

## 5. Features implemented

### Backend (Python / FastAPI / SQLAlchemy / SQLite / JWT)

- Email + password authentication with bcrypt hashing and JWT access tokens.
- Per-user data isolation on every endpoint.
- Repository management: add (GitHub metadata fetched via the GitHub API), list, detail,
  branches, delete.
- Real scanning pipeline:
  - Shallow `git clone` (token-injected HTTPS for private repos, `shell=False`, tokens redacted in logs).
  - Tool detection at runtime; tools that are not installed are reported as skipped.
  - Built-in analyzer: regex secret rules + Python `ast` checks (always available).
  - External tool parsers: Ruff, Bandit, Semgrep, ESLint, npm audit, pip-audit.
  - Finding normalization + deduplication.
  - Background execution with live progress, concurrency limit, and temp-directory cleanup.
- Findings: list with filters (severity, category, status, tool, repository, scan, free-text search),
  pagination, detail, status/severity updates, and explain (AI or offline).
- Controlled fixes: template/AI generation → unified diff → explicit approval → apply to an
  **isolated working copy** → syntax validation → revert. The original clone is never edited.
- Reports: HTML, JSON and CSV export.
- Dashboard stats and analytics (severity, category, language, repository distribution, trend,
  resolution rate).
- Settings + tool availability + AI status/test endpoints.

### Frontend (React + Vite + TypeScript + Tailwind + Monaco + Recharts)

15 pages:

1. Landing
2. Sign up
3. Log in
4. Dashboard (stats + charts)
5. Repositories
6. Repository detail (branches, scan history)
7. Scan results (live progress, tools used/skipped, languages, exports)
8. Findings (filters + pagination + shareable URLs)
9. Finding detail (code excerpt, triage, explain)
10. Fix suggestions
11. Patch review (side-by-side diff, approve/reject/revert, validation output)
12. Scan history
13. Analytics
14. Settings (AI toggles, provider status, scanner availability)
15. Profile

---

## 6. API overview

All routes are prefixed with `/api`.

| Area        | Endpoints |
|-------------|-----------|
| Auth        | `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `PATCH /auth/me` |
| Repos       | `POST /repositories`, `GET /repositories`, `GET /repositories/{id}`, `GET /repositories/{id}/branches`, `DELETE /repositories/{id}` |
| Scans       | `POST /repositories/{id}/scan`, `GET /scans`, `GET /scans/{id}`, `GET /scans/{id}/status`, `POST /scans/{id}/cancel` |
| Findings    | `GET /findings`, `GET /findings/{id}`, `PATCH /findings/{id}`, `POST /findings/{id}/explain` |
| Fixes       | `POST /findings/{id}/propose-fix`, `GET /findings/{id}/fixes`, `GET /fixes/{id}`, `POST /fixes/{id}/approve`, `POST /fixes/{id}/reject`, `POST /fixes/{id}/revert` |
| Dashboard   | `GET /dashboard/stats`, `GET /dashboard/analytics` |
| Reports     | `GET /reports/{scan_id}`, `GET /reports/{scan_id}/export?format=html\|json\|csv` |
| Settings    | `GET /settings`, `PATCH /settings`, `GET /settings/ai/status`, `POST /settings/ai/test`, `GET /tools` |
| Meta        | `GET /health` |

---

## 7. Tests actually run (real results)

The following were executed against the real repository `psf/requests` on this machine.

**Backend + scanning**
- Account signup/login/`GET /auth/me` succeeded.
- Added `psf/requests` (real metadata: language `Python`, default branch `main`).
- Ran a scan → completed successfully with **34 real findings** (all produced by real tools /
  built-in rules, no fabricated data).
- `GET /dashboard/stats` → `repos=1 scans=2 findings=34 critical=14 open=34`.
- `GET /dashboard/analytics` → correct severity/category/language aggregates.
- Findings list with `severity=critical` → `total=14`, `severity_counts.critical=14`.
- `GET /settings`, `GET /settings/ai/status` (offline mode), `GET /tools`
  → `available=npm,git`, `unavailable=5` (correctly reported as skipped).
- Fix loop on a `CG-QUA-041` finding:
  - `propose-fix` → generated a template diff.
  - `approve` → `"Fix applied to an isolated working copy. The original repository was not
    modified."`, validation output `"Python syntax check passed."`
  - `revert` → validation passed and the original file was restored.
- `propose-fix` on a finding without a safe automatic fix correctly returns
  *"No safe automatic fix is available for this finding. It requires manual review."*

**Frontend**
- `npm run build` → TypeScript type-check passes; Vite production build succeeds.
- Dev server serves the app (`HTTP 200`, root element present) and the `/api` proxy returns
  `{"status":"healthy","ai_configured":false}`.

---

## 8. Project structure

```
CODEGUARD-AI-18/
├─ backend/
│  ├─ app/
│  │  ├─ api/routes/        # auth, repositories, scans, findings, fixes, dashboard, reports, settings
│  │  ├─ core/              # config, security
│  │  ├─ database/          # base, session
│  │  ├─ models/            # User, Repository, Scan, Finding, FixProposal, AppliedFix, UserSettings
│  │  ├─ schemas/           # Pydantic models
│  │  └─ services/
│  │     ├─ ai/             # OpenAI-compatible provider + offline fallback
│  │     ├─ fixes/          # fix generation, apply, revert, validation
│  │     ├─ github/         # git clone + metadata
│  │     ├─ reports/        # html/json/csv
│  │     └─ scanning/       # builtin, tools, engine, languages, normalization
│  ├─ storage/              # sqlite db, clones, work dirs (git-ignored)
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ components/        # ui primitives, layout, common
│  │  ├─ hooks/             # useAuth
│  │  ├─ layouts/           # AppLayout
│  │  ├─ lib/               # api, utils, monaco-setup
│  │  ├─ pages/             # the 15 pages
│  │  ├─ services/          # API endpoints
│  │  └─ types/
│  └─ package.json
├─ sample-repository/       # intentionally vulnerable demo files
├─ .env.example
└─ README.md
```

---

## 9. Safety properties

- The application **never executes code** from scanned repositories.
- External tools run through safe argument lists (`shell=False`) with timeouts.
- Path traversal is prevented; `.git`, `node_modules`, virtualenvs and similar directories are excluded.
- Clones and working copies live in temporary directories and are cleaned up after each scan.
- Private access tokens are stored server-side and never returned to the browser; they are redacted
  from logs.
- Fixes are applied only to an isolated working copy after explicit approval, and can be reverted.

---

## 10. Known limitations

- **No push / no pull requests.** Fixes are validated locally only; nothing is committed or opened
  as a PR on GitHub.
- **Template coverage.** Automatic fixes are available only for rule IDs that have a safe
  deterministic template (and AI fixes require a configured provider). Findings without a safe
  automated fix return a clear message and require manual review.
- **External scanner coverage depends on installation.** On the machine used for testing only
  `git` and `npm` were available, so Ruff/Bandit/Semgrep/ESLint/pip-audit were reported as skipped.
- **Large bundles.** The Monaco editor is bundled locally (for offline use) and lazy-loaded only on
  the pages that display code or diffs, so it does not affect initial page load.
- **SQLite.** Intended for single-user / small-team use. Use PostgreSQL for concurrent workloads.
- **Rate limits.** GitHub metadata and private repository reads are subject to GitHub API rate limits;
  adding a token raises the limit.
- **`SECRET_KEY`.** The default value must be changed in `.env` before any real deployment.
