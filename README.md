# EDA Pipeline

Lightweight, no-signup web app for exploratory data analysis and data-quality checks. Upload a CSV/Excel/JSON/Feather file (up to 500 MB), get instant profiling, charts, and a remediation checklist you can share with teammates.

## Features
- Drag-and-drop upload with in-browser caching (Flask sessions on disk).
- Supports CSV, XLS/XLSX, JSON, and Feather.
- Automatic type detection (numeric/boolean/datetime/timeseries) with per-column stats, skew/kurtosis, and Z-score outlier counts (3σ/4σ/5σ).
- Dataset overview: shape, column list, missingness totals, duplicate rows, constant/low-variance columns, cardinality flags.
- Data quality checklist: missing-data breakdowns, constant columns, duplicate guidance, and recommendations.
- Visuals: distribution and outlier plots rendered server-side with matplotlib/seaborn and delivered as base64 images.
- Background janitor: APScheduler cleans uploaded files and session caches (older than 60 minutes).
- Optional Supabase/Postgres logging for uploads and user feedback (see `db.py`).

## Architecture (tl;dr)
- `app.py` – Flask app, routing, session caching, upload handling, sitemap/robots, APScheduler startup.
- `data_quality.py` – Profiling engine (type detection, stats, outliers, skew/kurtosis, missingness, checklist generator, plotting helpers).
- `templates/` – Jinja pages (`landing.html`, `upload.html`, `index.html`, `datatype_analysis.html`, `data_quality_checklist.html`, etc.).
- `static/` – CSS/JS/assets; `uploads/` – runtime upload storage (git-ignored).
- `maintenance.py` – numpy/pandas → JSON converters; safe folder wipes.
- `scheduler.py` – hourly cleanup job; `preview.py` / `static.py` – small demo runners.
- Served via Waitress (Docker) or Flask dev server; session files live under `flask_files/flask_session`.

## Quickstart (local)
1) Install Python 3.11+.  
2) Create a venv and install deps:
```bash
python -m venv .venv
. .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
3) Set environment variables (example):
```bash
set SECRET_KEY=dev-secret
set DATABASE_URL=postgresql://user:pass@host:5432/dbname   # optional, for logging
```
4) Run the dev server (auto-reload):
```bash
python -m flask --app app run --debug --port 8000
```
5) Open http://127.0.0.1:8000/app, upload a file, then explore:
- Overview: `/overview`
- Data type analysis: `/datatype-analysis`
- Checklist: `/data-quality-checklist`

## Docker / Compose
```bash
docker build -t eda-pipeline .
docker run -p 8000:8000 -e SECRET_KEY=change-me -e DATABASE_URL=... eda-pipeline
# or
docker-compose up --build
```
Waitress listens on `8000`. Adjust env vars in `docker-compose.yml` for your DB/secrets.

## Configuration
- `SECRET_KEY` (required) – Flask sessions.
- `DATABASE_URL` (optional) – Postgres/Supabase URL for upload + feedback logging. If unset, logging is skipped but the app still works.
- `MAX_CONTENT_LENGTH` – defaults to 500 MB in `app.py`; change if you need larger uploads.

## Data handling & privacy
- Files are stored temporarily in `uploads/` and cleaned by the scheduler (age > 60 min) or on startup.
- Sessions are filesystem-backed; clear via `/clear` endpoint if needed.
- No data leaves the server unless `DATABASE_URL` is provided for logging.

## Repo layout (high level)
- `app.py`, `data_quality.py`, `maintenance.py`, `scheduler.py`, `db.py`
- `templates/` and `static/` for the UI
- `uploads/`, `flask_files/` (runtime)
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`

## Common tasks
- Change upload limit: edit `max_file_size` in `app.py`.
- Disable background cleanup: remove the APScheduler job in `app.py`.
- Serve behind a proxy: `ProxyFix` is already applied; set `X-Forwarded-*` headers correctly.

## Roadmap ideas
- Add profiling summaries export (PDF/HTML).
- Correlation heatmaps and VIF report download.
- Auth + per-tenant storage backends (S3/Supabase Storage).
- Frontend polish and dark mode toggle.

