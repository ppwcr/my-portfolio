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

## 🖥️ Windows: One-Click Setup (Using .bat Files)

The project includes Windows batch files for easy automation. This is the **simplest way** to use the application on Windows.

### 📁 Available .bat Files:

- **`setup.bat`** (run once): Complete setup including auto-start and scheduled scraping
- **`start.bat`** (manual start): Starts the server with database updates (no browser)
- **`run_scheduled_scrape.bat`** (scheduled): Automated data scraping script
- **`server_manager.bat`** (control): Interactive server management interface
- **`git_update.bat`** (updates): Check for and pull latest git updates
- **`diagnose_autostart.bat`** (troubleshoot): Check auto-start system for issues
- **`fix_autostart.bat`** (repair): Fix common auto-start problems
- **`diagnose_windows_tasks.bat`** (diagnostic): Comprehensive Windows system check

### 🚀 **One-Click Windows Setup:**

#### **Step 1: Complete Setup (One-time)**
```bash
# Right-click Command Prompt → "Run as administrator"
# Navigate to your project folder
cd C:\path\to\my-portfolio

# Run the complete setup
setup.bat
```

**What setup.bat does:**
- ✅ Sets up auto-start (server starts automatically on login)
- ✅ Creates scheduled data scraping (10:30, 13:00, 17:30 weekdays)
- ✅ Includes git update checking
- ✅ No browser opens automatically (server only)

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

#### **Step 3: Access the Application**
```bash
# The server will start automatically on login
# Or manually start with:
start.bat

# Or use server manager for control:
server_manager.bat
```

**Access the dashboard at:** [http://127.0.0.1:8000/portfolio](http://127.0.0.1:8000/portfolio)

### ⏰ **Automatic Features:**

#### **Auto-Start:**
- Server starts automatically when you log in
- No browser opens (server runs in background)
- Git updates checked automatically

#### **Scheduled Data Scraping:**
- **10:30 AM** - Morning data update
- **13:00 PM** - Afternoon data update  
- **17:30 PM** - Evening data update
- Runs Monday-Friday only
### 🔧 **Server Management:**

#### **Using Server Manager:**
```bash
# Run the interactive server manager
server_manager.bat
```

**Server Manager Options:**
- **1** - Start server in background
- **2** - Stop server
- **3** - Check server status
- **4** - Restart server
- **5** - View logs
- **6** - Exit

#### **Manual Control:**
```bash
# Start server manually
start.bat

# Check if server is running
curl http://127.0.0.1:8000

# Stop server (if needed)
taskkill /f /im python.exe
```

### 📋 **Daily Workflow:**

1. **Automatic:** Server starts automatically on login
2. **Manual control:** Use `server_manager.bat` when needed
3. **Access dashboard:** [http://127.0.0.1:8000/portfolio](http://127.0.0.1:8000/portfolio)

### ⚠️ **Important Notes:**

- **Administrator Rights:** `setup.bat` needs Administrator privileges for scheduled tasks
- **Auto-start:** Server runs automatically in background
- **Python Required:** Make sure Python 3.10+ is installed
- **Environment File:** Don't forget to create your `.env` file
- **Weekend Skip:** Scheduled scraping runs Monday-Friday only

### 🔧 **Troubleshooting:**

**If setup.bat fails:**

1. **Run diagnostics first:**
   ```cmd
   diagnose_autostart.bat
   ```
   This will identify specific issues with your auto-start setup.

2. **Try the auto-start fix:**
   ```cmd
   fix_autostart.bat
   ```
   This will recreate the VBS script and startup shortcut.

3. **Check Python installation:**
   ```cmd
   python --version
   ```
   If Python is not found, install Python 3.8+ from python.org

4. **Run setup.bat again**

### 🔄 **For Users Who Already Installed:**

**Check if your setup is working:**
```cmd
# Comprehensive Windows diagnostic
diagnose_windows_tasks.bat

# Check scheduled tasks status
schtasks /query /fo table

# Test the scraping script manually
run_scheduled_scrape.bat
```

**If tasks are working but you want to update:**
```cmd
# Pull latest changes
git_update.bat

# Or manually:
git pull origin main
```

**If only auto-start is broken:**
```cmd
# Quick fix for auto-start only
fix_autostart.bat
```

**If specific tasks are missing:**
```cmd
# Recreate individual tasks (no need to reinstall everything)
schtasks /Create /TN SET_Scraper_1030 /TR "run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 10:30 /RL LIMITED
schtasks /Create /TN SET_Scraper_1300 /TR "run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 13:00 /RL LIMITED
schtasks /Create /TN SET_Scraper_1730 /TR "run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:30 /RL LIMITED
```

**Signs your setup is working:**
- ✅ `schtasks /query` shows 3 SET_Scraper tasks
- ✅ New files appear in `_out` directory at scheduled times
- ✅ `scraper_*.log` files are created
- ✅ Server starts automatically on login

**If server doesn't start automatically:**

1. **Run diagnostics:**
   ```cmd
   diagnose_autostart.bat
   ```
   This will check all auto-start components and identify issues.

2. **Try the fix script:**
   ```cmd
   fix_autostart.bat
   ```
   This will recreate the VBS script and startup shortcut.

3. **Manual checks:**
   ```cmd
   # Check auto-start shortcut
   # Press Win+R, type "shell:startup" and press Enter
   # Look for "Portfolio Dashboard Server.lnk"

   # Or manually start:
   start.bat
   ```

**If scheduled tasks don't work:**
```bash
# Check if tasks were created
schtasks /query /tn SET_Scraper_1030
schtasks /query /tn SET_Scraper_1300
schtasks /query /tn SET_Scraper_1730

# Check server status
curl http://127.0.0.1:8000

# View scraping logs
dir scraper_*.log
```

**If you get permission errors:**
```bash
# Right-click Command Prompt and "Run as Administrator"
# Then run setup.bat again
```

### 📤 **Updating and Pushing Changes:**

**Check for updates:**
```cmd
# Check if you have the latest version
git status

# Pull latest changes
git_update.bat

# Or manually:
git pull origin main
```

**Push your changes:**
```cmd
# Add all changes
git add .

# Commit changes
git commit -m "Updated portfolio data and settings"

# Push to remote repository
git push origin main
```

**If you have local changes to keep:**
```cmd
# Stash your changes before pulling
git stash

# Pull latest changes
git pull origin main

# Apply your changes back
git stash pop
```

**After updating:**
```cmd
# Test if everything still works
run_scheduled_scrape.bat

# Check if tasks are still active
schtasks /query /fo table
```

### 🗑️ **Removing the Setup:**

**To remove auto-start:**
```bash
# Press Win+R, type "shell:startup" and press Enter
# Delete "Portfolio Dashboard Server.lnk"
```

**To remove scheduled tasks:**
```bash
# Run as Administrator
schtasks /Delete /TN SET_Scraper_1030 /F
schtasks /Delete /TN SET_Scraper_1300 /F
schtasks /Delete /TN SET_Scraper_1730 /F
```

**To remove everything:**
```bash
# Run setup.bat again (it will clean up and recreate)
setup.bat
```
- Right-click Command Prompt → "Run as administrator"
- Make sure you're in the correct project directory

### 🎯 **Quick Commands Reference:**

```bash
# First time setup
setup.bat

# Start the application
start.bat

# Check server status
curl http://127.0.0.1:8000

# View scraping logs
dir scraper_*.log

# Remove scheduled tasks
schtasks /delete /tn SET_Scraper_1030 /F
schtasks /delete /tn SET_Scraper_1300 /F
schtasks /delete /tn SET_Scraper_1730 /F
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
my-portfolio/
├─ main.py                          # FastAPI app (endpoints, auto DB save)
├─ requirements.txt
├─ supabase_database.py             # Supabase helpers (server-side)
├─ background_updater.py            # Automatic data collection & updates
├─ templates/
│  └─ index.html                    # Floating panel UI
├─ static/
│  ├─ app.css
│  └─ app.js
├─ _out/                            # Generated files
│  ├─ investor/
│  └─ sectors_YYYYMMDD_HHMMSS/
├─ download_nvdr_excel.py           # NVDR data scraper
├─ download_short_sales_excel.py    # Short sales data scraper
├─ scrape_investor_data.py          # Investor data scraper
├─ scrape_sector_data.py            # Sector data scraper
├─ .env.example
├─ setup.bat                        # One-click complete setup
├─ start.bat                        # Manual server start
├─ server_manager.bat               # Interactive server control
└─ run_scheduled_scrape.bat         # Scheduled scraping script
```

---

## Database (Supabase) – overview

* Supabase is **managed Postgres**. Use the **service role key** on the server to insert/update.
* **Automatic data updates** run at 10:30 AM, 1:00 PM, and 5:30 PM (weekdays)
* **Background updater** handles all data collection and database saves automatically

### Database Tables:

* **`investor_summary`** - Investor type trading data (period1/2/3 buy/sell/net values)
* **`nvdr_trading`** - NVDR trading data (volume/value buy/sell/total/net)
* **`short_sales_trading`** - Short sales data (short volume/value, outstanding shares)
* **`sector_data`** - Sector constituent stocks (prices, volume, sector classification)
* **`set_index`** - SET index data (index values, changes, volume)
* **`portfolio_symbols`** - User portfolio symbols (watchlist)
* **`portfolio_holdings`** - Portfolio holdings (quantity, cost price, trade date)

### Automatic Features:

* **Scheduled scraping** downloads fresh data from SET website
* **Database upserts** prevent duplicates using `(date, key)` constraints
* **Error logging** tracks failed updates in `scraper_*.log` files
* **Background processing** runs independently of web interface

### Manual Database Updates:

```bash
# Trigger manual database update (server must be running)
curl -X POST http://127.0.0.1:8000/api/save-to-database

# View update logs
dir scraper_*.log
```

### Detailed Table Structures:

#### **investor_summary**
- `investor_type` (str) - Type of investor (Local, Foreign, etc.)
- `period1/2/3_buy_value` (float) - Buy values for each period
- `period1/2/3_sell_value` (float) - Sell values for each period  
- `period1/2/3_net_value` (float) - Net values for each period
- `trade_date` (str) - Trading date (YYYY-MM-DD)
- `created_at` (str) - Record creation timestamp

#### **nvdr_trading**
- `symbol` (str) - Stock symbol
- `volume_buy/sell/total/net` (int) - Trading volumes
- `value_buy/sell/total/net` (int) - Trading values in Baht
- `volume_percent` (float) - Volume percentage
- `value_percent` (float) - Value percentage
- `trade_date` (str) - Trading date

#### **short_sales_trading**
- `symbol` (str) - Stock symbol
- `short_volume_local/nvdr/total` (int) - Short sale volumes
- `short_value_baht` (int) - Short sale value in Baht
- `short_percentage` (float) - Short sale percentage
- `outstanding_local/nvdr/total` (int) - Outstanding shares
- `outstanding_percentage` (float) - Outstanding percentage
- `trade_date` (str) - Trading date

#### **sector_data**
- `symbol` (str) - Stock symbol
- `open/high/low/last_price` (float) - Price data
- `change` (str) - Price change
- `percent_change` (str) - Percentage change
- `volume_shares` (int) - Trading volume
- `value_baht` (float) - Trading value
- `sector` (str) - Sector classification
- `trade_date` (str) - Trading date

#### **set_index**
- `index_name` (str) - Index name (SET, MAI, etc.)
- `last_value` (float) - Last index value
- `change_value` (float) - Index change
- `change_text` (str) - Change description
- `volume_thousands` (int) - Volume in thousands
- `value_million_baht` (float) - Value in million Baht
- `trade_date` (str) - Trading date

#### **portfolio_symbols**
- `symbol` (str) - Stock symbol in watchlist
- `added_at` (str) - When added to watchlist

#### **portfolio_holdings**
- `symbol` (str) - Stock symbol
- `quantity` (int) - Number of shares
- `avg_cost_price` (float) - Average cost per share
- `cost` (float) - Total cost
- `trade_date` (str) - Trade date

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
