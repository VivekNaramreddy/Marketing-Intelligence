# Marketing Intelligence · V0.1

A local, single-user marketing analysis application. Add data → analyze → understand → generate a basic report. No API keys, accounts, connectors, or external AI services are needed.

## Run locally (Windows PowerShell)

Prerequisites: Python 3.11+ and Node.js 20.19+ (or 22.12+).

From the project root, install dependencies once:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm.cmd ci
cd ..
```

Start the backend in one terminal:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm.cmd run dev
```

Open **http://127.0.0.1:5173**. API documentation: **http://127.0.0.1:8000/docs**. `npm.cmd` avoids Windows PowerShell execution-policy restrictions on `npm.ps1`. On macOS/Linux, use `.venv/bin/python` and `npm`.

Vite proxies `/api` to FastAPI. Both processes must run. `npm.cmd run build` produces the frontend bundle; deploying or serving the production bundle with an API reverse proxy is outside V0.1.

## Demo and first workflow

1. Create a workspace with a descriptive name.
2. On **Data**, choose **Load demo dataset**. This loads 21 fictional observations, selects New Haven Symphony Orchestra as primary, and selects four competitors.
3. Choose **Analyze selected brands** to open the dashboard.
4. Open **View evidence** on findings to inspect the metrics, observation IDs, dates, filenames, and source rows.
5. On **Analysis → Competitors**, inspect all brands or filter by platform.
6. On **Reports**, choose **Generate Basic Report** to render five concise sections. Reports regenerate from the current selection and are cleared from the view after data/selection changes.

Demo values are explicitly fictional, not claims about the named organizations. The clearly named file is `backend/demo/DEMO_fictional_social.csv`. Demo loading is permitted once per workspace. Create a fresh workspace to try it again.

Expected demo results: audience **18,551**, mean available engagement **2.215%** (displayed rounded), highest engagement **TikTok**, and **1 of 4** comparable platforms ranked first. Findings: Instagram engagement gap, YouTube audience lead, and qualified TikTok opportunity.

## Import contract

CSV (UTF-8) and Excel `.xlsx` are supported. Excel reads the first worksheet. Required columns: `Brand`, `Platform`, and at least one numeric metric per row. Optional: `Date`, `Followers`, `Engagement Rate`, `Views`, `Likes`, `Comments`, `Shares`, `Posts`. Manual entry uses the same normalization and validation.

```csv
Brand,Platform,Date,Followers,Engagement Rate
My brand,Instagram,2026-09-30,1200,2.4%
Competitor,Instagram,2026-09-30,1500,
```

- Blank metrics remain null, never zero. Literal `N/A`, `unknown`, or malformed numbers produce an actionable error; use blanks for missing values.
- Rates are percentage points: `2.4` and `2.4%` both mean 2.4%. Excel percentage-format cells store fractions internally; convert them to percentage points before import (0.024 is interpreted as 0.024%, not 2.4%). No unit inference occurs.
- Counts must be whole and nonnegative. Rates must be finite and between 0 and 100. Comma-separated counts are accepted; quote them in CSV.
- Dates accept `YYYY-MM-DD` or `YYYY-MM` (stored as the first day of that month). Native Excel date cells are accepted. Empty dates remain null. Align reporting periods before comparing values.
- Headers are trimmed, case-insensitive, and spaces/slashes become underscores. Aliases: `brand_name`, `follower_count`, `period`, `period_date`, `engagement_rate_%`.
- Common platform names and Twitter/X aliases are canonicalized. Brand names are trimmed but otherwise case-sensitive; review consistency before importing.
- One observation per brand/platform/date within an import. Duplicates in a batch are rejected. Later imports append source history; the latest imported observation wins when reporting dates tie.
- Upload limit is 5 MB of uploaded bytes. `.xls` is not supported. Imports validate completely before persistence; invalid batches store no observations. Unknown columns remain in raw records but are not used in calculations.

## Architecture and data flow

`CSV / Excel / manual → raw import batch → normalization → normalized observations → deterministic metrics → rule-based findings → dashboard / report`

Workspace: name, primary brand, selected competitors. Import batch: workspace ID, filename, UTC import time, original parsed rows. Observation: workspace/import IDs, source row, brand/platform/date, and nullable numeric fields. Raw spreadsheet values are retained as parsed records (dates serialized as ISO), not the original binary workbook or its formatting. Source rows count the header as row 1; manual rows follow the same convention.

SQLAlchemy isolates storage access from calculation logic. SQLite lives at `backend/data/marketing.db`. Override `DATABASE_URL` for a different SQLAlchemy database; PostgreSQL would additionally need a driver, schema migrations, and deployment configuration. It is an extension point, not a verified PostgreSQL integration. Python metrics/findings/report functions accept plain data and do not depend on FastAPI or UI components. `AIProvider` is a prose-only protocol with no active implementation.

Metrics select the latest **dated** observation for each brand/platform, using import observation ID to break same-date ties. Undated observations are used only when no dated observation exists. Missing values on the latest row do not borrow older values. Snapshot rows may have different dates; those dates are visible and findings with multiple dates have limited confidence.

Audience sums available platform followers and is not a count of unique people. Engagement is an unweighted arithmetic mean across available platform rates. Highest engagement uses available rates, with alphabetical platform order breaking ties. Competitor averages exclude missing values and the primary brand. Platform ranks use competition ranking (e.g. 1, 1, 3) and require at least one measured competitor. Total audiences across brands are shown with coverage counts and **are not ranked as comparable totals**.

Finding rules: engagement at least 20% below a positive competitor mean → Weakness; follower rank 1 and strictly above the competitor mean → Strength; positive audience with no measured competitor follower counts → Opportunity with an explicit data-coverage qualification. One finding per platform, weakness prioritized, maximum five. Confidence labels describe limited dataset coverage, not statistical significance. Numeric evidence and source IDs accompany every finding. Reports reuse these calculated values and findings without an LLM.

## Major files

| File | Purpose |
| --- | --- |
| `backend/requirements.txt`, `requirements-dev.txt`, `requirements.lock.txt` | Runtime/test dependencies, optional browser tooling, verified Python environment |
| `backend/app/main.py` | Workspace, selection, data, import, analysis, raw evidence, and report API routes |
| `backend/app/storage.py` | Engine, sessions, database configuration |
| `backend/app/models.py` | Workspace, raw import batch, normalized observation models |
| `backend/app/normalization.py` | CSV/Excel input adapters, canonicalization, validation |
| `backend/app/metrics.py` | Latest snapshots, averages, ranks, relative and rate differences |
| `backend/app/findings.py` | Evidence-backed deterministic rules |
| `backend/app/reports.py` | Five-section report generation |
| `backend/app/ai.py` | Future optional explanation-provider protocol |
| `backend/demo/DEMO_fictional_social.csv` | Clearly marked fictional sample dataset |
| `backend/tests/test_core.py`, `test_api.py` | Import, normalization, metrics, findings, reports, isolation, and API workflow tests |
| `frontend/package.json`, `package-lock.json` | Frontend dependencies and exact dependency resolution |
| `frontend/index.html`, `tsconfig.json`, `vite.config.ts` | HTML entry, TypeScript, Vite/Tailwind, development API proxy |
| `frontend/src/main.tsx`, `App.tsx` | React entry, app shell, workspace state and navigation |
| `frontend/src/types.ts`, `services/api.ts` | Shared types and API client/error handling |
| `frontend/src/components/Intelligence.tsx` | Summary metrics, evidence cards, audience comparison chart |
| `frontend/src/pages/DataPage.tsx` | File/manual imports, demo, selection, history, raw records |
| `frontend/src/pages/AnalysisPage.tsx` | Overview, comparison table/filter, Content foundation |
| `frontend/src/pages/ReportsPage.tsx` | Generate and render a basic report |
| `frontend/src/style.css` | Responsive desktop/tablet/mobile interface |
| `scripts/browser_smoke.py` | Optional browser workflow and responsive checks |
| `.gitignore`, `README.md` | Generated/local file exclusions and operating documentation |

## Verification

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest tests -q
cd ../frontend
npm.cmd run build
```

The API tests use a disposable in-memory SQLite database. Optional browser check: install `backend/requirements-dev.txt`, start the backend with `DATABASE_URL` pointing at a **disposable database**, start Vite, and run `.\.venv\Scripts\python.exe scripts/browser_smoke.py` from the root. It uses installed Chrome by default; set `BROWSER_EXECUTABLE` to your browser executable if needed. The browser script creates test records in a new workspace. Screenshots are written under ignored `artifacts/`.

## Working scope and V0.1 limitations

Working: persistent workspace creation/selection, CSV/Excel/manual import, demo loading, raw/normalized separation, validation, selection of any imported brands, calculated dashboard, evidence-backed findings, comparison table and one chart, and an in-app report. State survives server restarts in SQLite; generated reports themselves are not persisted.

Limitations: no authentication or multi-user boundaries (use on localhost only), import editing/deletion/undo, arbitrary column-mapping interface, aligned time-series growth analysis, weighted engagement, unique-audience deduplication, post-level content analysis, saved report snapshots, or PDF export. Imported views/likes/comments/shares/posts are stored for traceability but do not drive new V0.1 metrics. All records are loaded at once; this foundation targets small spreadsheets. There is no database migration framework yet. No external APIs, scraping, CRM, publishing, scheduling, notifications, payments, or automation are implemented. `AIProvider` is only an extension point.

## Next logical V0.2 work (not implemented)

1. Add import preview, explicit column/unit mapping, and reversible batch removal.
2. Add aligned reporting-period selection and tested historical growth comparisons, with coverage warnings.
3. Save immutable report snapshots with source provenance; consider simple PDF export after the report format is validated.
