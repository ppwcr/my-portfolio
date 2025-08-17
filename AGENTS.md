# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: FastAPI app exposing export endpoints and SSE progress.
- `download_*.py` / `scrape_*.py`: Data scrapers and Excel/CSV generators.
- `supabase_database.py`: Supabase integration and save helpers.
- `templates/`: Jinja templates (e.g., `index.html`, `portfolio.html`).
- `static/`: Frontend assets (`app.css`, `app.js`).
- `_out/`: Generated outputs (e.g., `nvdr_YYYYMMDD_HHMMSS.xlsx`, `sectors_*/`).
- `requirements.txt`: Python dependencies; `.env.example` for config.

## Build, Test, and Development Commands
- Install deps: `pip install -r requirements.txt`
- Playwright (required for Excel downloads):
  - `pip install playwright`
  - `python -m playwright install chromium`
- Run server (dev): `python main.py` (serves on `http://localhost:8000`).
- Alt run: `uvicorn main:app --reload --port 8000`.
- Quick script checks:
  - `python download_nvdr_excel.py --out _out/test_nvdr.xlsx`
  - `python scrape_investor_data.py --market SET --out-table _out/investor/table.csv --out-json _out/investor/chart.json --allow-missing-chart`

## Coding Style & Naming Conventions
- Python, PEP 8, 4‑space indents, type hints where practical.
- Filenames/modules: `lower_snake_case.py`; functions/vars: `snake_case`; classes: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
- Response files: timestamped via `prefix_YYYYMMDD_HHMMSS.ext`.
- No linter is enforced; keep code formatted consistently (black/isort optional, avoid adding configs without discussion).

## Testing Guidelines
- No formal test suite yet. Prefer targeted, manual checks:
  - Hit endpoints in browser or via `curl`/HTTP client.
  - Verify files appear in `_out/` with expected names/content.
- Proposed tests (if adding): `pytest` with `tests/test_*.py`; aim for coverage on scrapers and DB helpers.

## Commit & Pull Request Guidelines
- Current history uses short, lowercase summaries. Improve by using imperative mood and scope when helpful:
  - Example: `feat(api): add sector constituents endpoint` or `fix: handle Playwright timeout`.
- Pull Requests should include:
  - Purpose and changes summary, linked issues, and screenshots/GIFs for UI changes.
  - Repro steps and expected outputs (paths under `_out/`).
  - Notes on env vars or migration impacts.

## Security & Configuration Tips
- Create `.env` from `.env.example`; do not commit secrets.
- Required: `SUPABASE_URL`, `SUPABASE_KEY`. Optional: `HEADFUL=1`, `NO_SANDBOX=1`.
- Validate DB connectivity: `python -c "from supabase_database import get_proper_db; print(get_proper_db())"`.

