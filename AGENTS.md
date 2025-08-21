# Repository Guidelines

This guide helps contributors work effectively in this FastAPI-based data export and scraping project. It outlines structure, commands, style, testing, and collaboration norms specific to this repo.

## Project Structure & Module Organization
- `main.py`: FastAPI app exposing export endpoints and SSE progress.
- `download_*.py` / `scrape_*.py`: Download/scrape scripts and Excel/CSV generators.
- `supabase_database.py`: Supabase integration and save helpers.
- `templates/`: Jinja templates (e.g., `index.html`, `portfolio.html`).
- `static/`: Frontend assets (`app.css`, `app.js`).
- `_out/`: Generated outputs (e.g., `nvdr_YYYYMMDD_HHMMSS.xlsx`, `sectors_*/`).
- `requirements.txt`: Python dependencies; `.env.example` for config.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt`.
- Playwright (for Excel downloads): `pip install playwright` then `python -m playwright install chromium`.
- Run dev server: `python main.py` or `uvicorn main:app --reload --port 8000` (serves `http://localhost:8000`).
- Quick checks:
  - `python download_nvdr_excel.py --out _out/test_nvdr.xlsx`
  - `python scrape_investor_data.py --market SET --out-table _out/investor/table.csv --out-json _out/investor/chart.json --allow-missing-chart`
- Validate DB connectivity: `python -c "from supabase_database import get_proper_db; print(get_proper_db())"`.

## Coding Style & Naming Conventions
- Python, PEP 8, 4-space indents; add type hints where practical.
- Filenames/modules: `lower_snake_case.py`; functions/vars: `snake_case`; classes: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
- Output filenames timestamped: `prefix_YYYYMMDD_HHMMSS.ext`.
- Keep formatting consistent; optional Black/isort locally (avoid adding config without discussion).

## Testing Guidelines
- No formal suite yet. Prefer targeted manual checks: hit endpoints in browser or via `curl` and verify files appear in `_out/` with expected names/content.
- If adding tests: use `pytest`; place under `tests/test_*.py`. Focus on scrapers and DB helpers.
- Run tests: `pytest`.

## Commit & Pull Request Guidelines
- Commits: imperative mood, optional scope. Examples: `feat(api): add sector constituents endpoint`, `fix: handle Playwright timeout`.
- PRs: include purpose and changes summary, linked issues, and screenshots/GIFs for UI changes. Add repro steps and expected outputs (paths under `_out/`). Note any env var or migration impacts.

## Security & Configuration Tips
- Create `.env` from `.env.example`; never commit secrets.
- Required: `SUPABASE_URL`, `SUPABASE_KEY`. Optional: `HEADFUL=1`, `NO_SANDBOX=1` for browser behavior.
- Validate credentials before running exports; avoid logging sensitive values.

