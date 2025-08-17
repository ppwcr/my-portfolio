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

## 🖥️ Windows: Easiest Way (Using .bat Files)

The project includes Windows batch files for easy automation. These are the **simplest way** to use the application on Windows.

### 📁 Available .bat Files:

- **`setup.bat`** (run once): Creates virtual environment, installs dependencies, and sets up Playwright
- **`start.bat`** (every time): Starts the server and opens the app in your browser
- **`update_database_daily.bat`** (manual): Triggers a database update (server must be running)
- **`register_update_task.bat`** (optional, run once): Schedules automatic daily weekday updates

### 🚀 **Step-by-Step Windows Setup:**

#### **Step 1: Initial Setup (One-time)**
```bash
# Right-click Command Prompt → "Run as administrator"
# Navigate to your project folder
cd C:\path\to\my-portfolio

# Run the setup script
setup.bat
```

**What setup.bat does:**
- Creates Python virtual environment (`.venv`)
- Installs all required packages from `requirements.txt`
- Installs Playwright and Chromium browser
- Sets up everything needed to run the application

#### **Step 2: Create Environment File**
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your Supabase credentials
notepad .env
```

**Add your Supabase credentials to .env:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

#### **Step 3: Start the Application**
```bash
# Double-click start.bat or run in Command Prompt:
start.bat
```

**What start.bat does:**
- Activates the virtual environment
- Opens your browser to `http://localhost:8000`
- Starts the FastAPI server with uvicorn

### ⏰ **Setting Up Automatic Updates:**

#### **Option A: One-Click Setup (Recommended)**
```bash
# Run as Administrator
register_update_task.bat
```

**What register_update_task.bat does:**
- Creates a Windows Scheduled Task named "SET_UpdateDatabase"
- Runs automatically on weekdays (Monday-Friday) at 18:05 (6:05 PM)
- Skips weekends automatically
- Requires Administrator privileges

#### **Option B: Manual Task Creation**
1. Open **Task Scheduler** (search in Start menu)
2. Click **"Create Basic Task"**
3. Name: `SET_UpdateDatabase`
4. Trigger: **Daily** at 18:05
5. Action: **Start a program**
6. Program: `C:\path\to\my-portfolio\update_database_daily.bat`
7. Check **"Run whether user is logged on or not"**

### 🔄 **Manual Database Updates:**

If you want to manually trigger a database update:

```bash
# Make sure the server is running first (start.bat)
# Then run:
update_database_daily.bat
```

**What update_database_daily.bat does:**
- Skips weekends (Saturday/Sunday)
- Calls the API endpoint to update Supabase database
- Logs success/failure to `update_log.txt`

### 📋 **Daily Workflow:**

1. **Start the application:**
   ```bash
   start.bat
   ```

2. **Use the web interface:**
   - Browser opens automatically to `http://localhost:8000`
   - Use the floating panel to export data

3. **Close when done:**
   - Press `Ctrl+C` in the Command Prompt window
   - Or close the Command Prompt window

### ⚠️ **Important Notes:**

- **Administrator Rights:** `register_update_task.bat` needs Administrator privileges
- **Server Must Be Running:** Automatic updates only work if the server is running
- **Python Required:** Make sure Python 3.10+ is installed
- **Environment File:** Don't forget to create your `.env` file
- **Weekend Skip:** Automatic updates skip Saturdays and Sundays

### 🔧 **Troubleshooting Windows .bat Files:**

**If setup.bat fails:**
```bash
# Check Python installation
python --version

# Install Python 3.10+ from python.org if needed
# Then run setup.bat again
```

**If start.bat doesn't work:**
```bash
# Check if virtual environment exists
dir .venv

# If missing, run setup.bat again
setup.bat
```

**If automatic updates don't work:**
```bash
# Check if task was created
schtasks /query /tn SET_UpdateDatabase

# Check if server is running
curl http://localhost:8000

# Check update logs
type update_log.txt
```

**If you get permission errors:**
- Right-click Command Prompt → "Run as administrator"
- Make sure you're in the correct project directory

### 🎯 **Quick Commands Reference:**

```bash
# First time setup
setup.bat

# Start the application
start.bat

# Manual database update (server must be running)
update_database_daily.bat

# Schedule automatic updates (run as Administrator)
register_update_task.bat

# Check scheduled tasks
schtasks /query /tn SET_UpdateDatabase

# Remove scheduled task
schtasks /delete /tn SET_UpdateDatabase /f
```

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
