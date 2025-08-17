Here’s an updated, practical README that matches your current 4-script setup and adds Windows one-click + daily automation.

---

# SET Data Export Panel

A full-stack web application that provides a floating bottom-right panel to export data from the Stock Exchange of Thailand (SET) using **DIY Python scrapers**, with optional **Supabase** storage.

## 🚀 Quick Setup Guide

### Step 1: Install Git (if not already installed)

**macOS (using Homebrew):**
```bash
# Install Homebrew first (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Git
brew install git
```

**macOS (using Xcode Command Line Tools):**
```bash
xcode-select --install
```

**Windows:**
```bash
# Download from https://git-scm.com/download/win
# Or use winget
winget install --id Git.Git -e --source winget
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install git
```

**Linux (CentOS/RHEL/Fedora):**
```bash
sudo yum install git
# or for newer versions:
sudo dnf install git
```

### Step 2: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/ppwcr/my-portfolio.git

# Navigate to the project directory
cd my-portfolio
```

### Step 3: Set Up Environment Variables

**Create your `.env` file:**
```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your actual values
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```env
# Supabase (required for saving data to database)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key

# Optional browser flags
HEADFUL=0        # Set to 1 to show browser UI
NO_SANDBOX=0     # Set to 1 if running in container
```

**How to get Supabase credentials:**
1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to Settings → API
3. Copy the "Project URL" and "service_role" key
4. Paste them in your `.env` file

### Step 4: Install Python Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install additional required packages
pip install playwright httpx beautifulsoup4 lxml pandas openpyxl

# Install Playwright browsers
python -m playwright install chromium
```

### Step 5: Verify Installation

```bash
# Test the individual scripts
python download_nvdr_excel.py --out _out/test_nvdr.xlsx
python download_short_sales_excel.py --out _out/test_short.xlsx
python scrape_investor_type_simple.py --market SET --out-table _out/investor/table_set.csv --out-json _out/investor/chart_set.json --allow-missing-chart
python scrape_set_sectors_jina.py --outdir _out/sectors_first_run
```

### Step 6: Run the Application

```bash
# Start the web application
python main.py

# Or using uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8000
```

**Open your browser and go to:** [http://localhost:8000](http://localhost:8000)

---

## 🔄 Updating the Repository

To get the latest changes:

```bash
# Pull latest changes
git pull origin main

# If you have local changes, you might need to stash them first
git stash
git pull origin main
git stash pop
```

## 🔧 Environment File Management

**Important:** The `.env` file is not tracked in git for security reasons. You need to create it manually.

**If you're setting up on a new machine:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ppwcr/my-portfolio.git
   cd my-portfolio
   ```

2. **Create your environment file:**
   ```bash
   # Copy the example
   cp .env.example .env
   
   # Edit with your actual values
   nano .env
   ```

3. **Add your Supabase credentials:**
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_service_role_key_here
   ```

**If you're updating and the .env file is missing:**
```bash
# Check if .env exists
ls -la .env

# If it doesn't exist, create it
cp .env.example .env
# Then edit with your credentials
```

---

## Features

## Features

* **Floating Panel UI** (bottom-right)
* **NVDR**: Download trading-by-stock (Excel)
* **Short Sales**: Download short sales (Excel)
* **Investor Type**: Export table (CSV) + chart payload (JSON) for **SET/MAI**
* **Sector Constituents**: Export sector lists (CSV) for 8 SET sectors
* **Database (optional)**: Save to **Supabase Postgres** (`?save=1`)
* **Error messages & logging**
* **Keyboard shortcuts**: Ctrl/Cmd + 1–4

---

## Quick Start

> **For first-time setup, see the [🚀 Quick Setup Guide](#-quick-setup-guide) above for complete installation instructions including Git installation.**

### 1) Install dependencies

```bash
pip install -r requirements.txt
pip install playwright httpx beautifulsoup4 lxml pandas openpyxl
python -m playwright install chromium
```

### 2) Environment setup

Create `.env` (based on `.env.example`):

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

Required variables:
```env
# Supabase (server-side writes use service role key)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key

# Optional browser flags
HEADFUL=0
NO_SANDBOX=0
```

### 3) Verify scripts (run once)

```bash
python download_nvdr_excel.py --out _out/test_nvdr.xlsx
python download_short_sales_excel.py --out _out/test_short.xlsx
python scrape_investor_type_simple.py --market SET --out-table _out/investor/table_set.csv --out-json _out/investor/chart_set.json --allow-missing-chart
python scrape_set_sectors_jina.py --outdir _out/sectors_first_run
```

### 4) Run the app

```bash
python main.py
# or:
uvicorn main:app --host 127.0.0.1 --port 8000
```

Open: **[http://localhost:8000](http://localhost:8000)**

---

## Windows: easiest way

Use the included batch files (no copy-paste needed).

- `setup.bat` (run once): creates venv, installs deps, installs Playwright.
- `start.bat` (every time): starts the server and opens the app URL.
- `register_update_task.bat` (optional, run once): schedules daily weekday auto-update.

If you don't see these files, pull latest or copy from this README snippets.

---

## API Endpoints

> Add `?save=1` to any endpoint below to **save rows to Supabase** after file generation.

### NVDR Excel

* **GET** `/api/nvdr/export.xlsx[?save=1]`
* Returns: `nvdr_trading_by_stock.xlsx`

### Short Sales Excel

* **GET** `/api/short-sales/export.xlsx[?save=1]`
* Returns: `short_sales_data.xlsx`

### Investor Type — Table

* **GET** `/api/investor/table.csv?market=SET|MAI[&save=1]`
* Returns: `investor_table_<market>.csv`

### Investor Type — Chart

* **GET** `/api/investor/chart.json?market=SET|MAI[&save=1]`
* Returns: `investor_chart_<market>.json`

### Sector Constituents

* **GET** `/api/sector/constituents.csv?slug=agro|consump|fincial|indus|propcon|resourc|service|tech[&save=1]`
* Returns: `<slug>.constituents.csv`

> (If you implemented SSE progress endpoints, keep them; otherwise you can remove that section.)

---

## Daily Automation (Windows)

**Keep the app running** as a background service (NSSM):

```bat
cd /d C:\path\to\project
nssm install set_quick_export "%cd%\.venv\Scripts\uvicorn.exe" main:app --host 127.0.0.1 --port 8000
nssm set set_quick_export AppDirectory "%cd%"
nssm start set_quick_export
```

**Schedule daily database update** (Task Scheduler) — skips weekends

```bat
@echo off
cd /d "%~dp0"

:: Skip weekends (Saturday/Sunday)
for /f %%D in ('powershell -NoProfile -Command "(Get-Date).DayOfWeek"') do set DOW=%%D
if /I "%DOW%"=="Saturday" exit /b 0
if /I "%DOW%"=="Sunday" exit /b 0

set URL=http://127.0.0.1:8000

:: Trigger a single consolidated update (investor, sectors, NVDR, short sales)
curl -fsS -X POST "%URL%/api/save-to-database" -H "Content-Type: application/json" -o NUL

if errorlevel 1 (
  echo [%date% %time%] Update failed >> update_log.txt
  exit /b 1
) else (
  echo [%date% %time%] Update succeeded >> update_log.txt
)
```

Option A (one click): run `register_update_task.bat` to auto-create a weekday task (default 18:05). Edit inside to change time.

Option B (manual): Create a **Basic Task** → *Start a program* → `update_database_daily.bat` at your desired time.

Note: The update calls the running API at `http://127.0.0.1:8000`. Ensure the server is running at the scheduled time (use `start.bat` or run as a background service via NSSM as below).

---

## Environment Variables

```env
# Supabase (required for saving)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key

# Playwright options
HEADFUL=0        # 1 = show browser UI
NO_SANDBOX=0     # 1 = needed in some containers
```

**SSH tunnel (optional)**

```bash
ssh -L 8000:127.0.0.1:8000 user@remote
# then open http://localhost:8000
```

---

## Project Structure

```
set-data-export-panel/
├─ main.py                          # FastAPI app (endpoints, optional DB save)
├─ requirements.txt
├─ supabase_database.py             # Supabase helpers (server-side)
├─ templates/
│  └─ index.html                    # Floating panel UI
├─ static/
│  ├─ app.css
│  └─ app.js
├─ _out/                            # Generated files
│  ├─ investor/
│  └─ sectors_YYYYMMDD_HHMMSS/
├─ download_nvdr_excel.py
├─ download_short_sales_excel.py
├─ scrape_investor_type_simple.py
├─ scrape_set_sectors_jina.py
├─ .env.example
├─ setup.bat                        # (optional helper)
└─ start.bat                        # (optional helper)
```

---

## Database (Supabase) – overview

* Supabase is **managed Postgres**. Use the **service role key** on the server to insert/update.
* Typical tables:

  * `nvdr_rows` (asof\_date, symbol, buy/sell/total/net/pct…)
  * `short_sales_rows`
  * `investor_rows` (market + label rows)
  * `sector_constituents` (slug + symbol rows)
* Your app can **upsert** on `(date, key)` to avoid duplicates.

---

## Keyboard Shortcuts

* **Ctrl/Cmd + 1** — NVDR Excel
* **Ctrl/Cmd + 2** — Short Sales Excel
* **Ctrl/Cmd + 3** — Investor Table CSV
* **Ctrl/Cmd + 4** — Sector Constituents CSV

---

## Troubleshooting

**Playwright**

```bash
python -m playwright install --force
set NO_SANDBOX=1 & python main.py
```

**Supabase**

```bash
python -c "from supabase_database import get_proper_db; print(get_proper_db())"
echo %SUPABASE_URL% & echo %SUPABASE_KEY%
```

**Scripts**

```bash
python download_nvdr_excel.py --out _out/test_nvdr.xlsx
python scrape_investor_type_simple.py --market SET --out-table _out/inv.csv --out-json _out/inv.json --allow-missing-chart
```

**Files**

* Outputs appear under `_out/`. Check there if downloads fail.

---

## Development

* Add an endpoint in `main.py` → add a button in `templates/index.html` → wire handler in `static/app.js`.
* For new DB saves, extend `supabase_database.py` with an upsert that preserves text formatting.

---

## License

For educational/research use. Respect SET’s terms of service when scraping.
