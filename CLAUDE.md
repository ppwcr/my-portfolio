# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a SET (Stock Exchange of Thailand) data scraping and portfolio management application. It scrapes real-time financial data from the Thai stock exchange and stores it in a Supabase database. The app provides a floating panel web UI for data export operations.

## Architecture

### Core Components

1. **FastAPI Web Server** (`main.py`): REST API with floating panel UI that orchestrates data scraping operations
2. **Database Layer** (`supabase_database.py`): Supabase integration with proper schema management for financial data
3. **Scrapers**: Four specialized scrapers for different data types:
   - `scrape_investor_data.py`: Investor type data (SET/MAI markets) using Jina.ai proxy
   - `scrape_sector_data.py`: Sector constituent data for all 8 SET sectors
   - `download_nvdr_excel.py`: NVDR trading-by-stock Excel files via Playwright
   - `download_short_sales_excel.py`: Short sales Excel files via Playwright
4. **Excel Parser** (`excel_file_parser.py`): Utilities for processing downloaded Excel files

### Data Flow

1. Web UI triggers API endpoints
2. FastAPI runs Python scrapers as subprocess commands
3. Scrapers save data to `_out/` directory (timestamped)
4. Database operations read from output files and save to Supabase
5. Real-time progress tracking via Server-Sent Events

### Database Schema

The application manages four main data types in Supabase:
- **Investor Summary**: Trade date + investor type breakdowns for SET/MAI
- **Sector Data**: 8 SET sectors with constituent stocks, weights, trade dates
- **NVDR Trading**: NVDR trading-by-stock data with trade dates
- **Short Sales Trading**: Short sales data with trade dates

## Development Commands

### Running the Application
```bash
python main.py
# App runs on http://localhost:8000
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright for Excel downloads
pip install playwright
python -m playwright install chromium

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Supabase credentials
```

### Required Environment Variables
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### Optional Environment Flags
```bash
HEADFUL=1          # Run browser in visible mode
NO_SANDBOX=1       # Run without sandbox (some Linux environments)
```

### Testing Individual Scrapers
```bash
# Test investor data scraping
python scrape_investor_data.py --market SET

# Test sector data scraping
python scrape_sector_data.py --outdir _out/test_sectors

# Test Excel downloads
python download_nvdr_excel.py --out test_nvdr.xlsx
python download_short_sales_excel.py --out test_short.xlsx

# Test database connection
python -c "from supabase_database import get_proper_db; db = get_proper_db(); print('Connected!')"
```

## Key Implementation Details

### Error Handling & Timeouts
- All scraper commands have configurable timeouts (45-120 seconds)
- Comprehensive error handling with stderr tail capture
- Fallback mechanisms for sector data (uses most recent complete dataset)
- Progress tracking with detailed error messages

### File Organization
- `_out/` directory contains all generated files with timestamps
- NVDR/Short Sales files: `{type}_{YYYYMMDD_HHMMSS}.xlsx`
- Sector data: `sectors_{YYYYMMDD_HHMMSS}/` directories
- Investor data: `_out/investor/` subdirectory

### Performance Optimizations
- Concurrent sector scraping (4 parallel requests)
- Async subprocess execution for all external commands
- Efficient Excel parsing with pandas and openpyxl
- Real-time progress updates prevent UI blocking

### Browser Automation
- Uses Playwright for SET website Excel downloads
- Supports headless/headful modes via environment flags
- Handles sandbox restrictions for Linux environments
- Proper error handling for website changes/failures

## Common Issues & Solutions

### Database Connection Issues
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

### Playwright Issues
```bash
# Reinstall browsers
python -m playwright install --force

# Linux sandbox issues
export NO_SANDBOX=1
```

### Scraping Timeouts
- Sector scraping: Uses fallback to most recent complete data
- Excel downloads: Check website availability and network connectivity
- Investor data: Uses Jina.ai public proxy, check proxy status

## API Endpoints

- `GET /api/nvdr/export.xlsx` - Download NVDR Excel
- `GET /api/short-sales/export.xlsx` - Download Short Sales Excel  
- `GET /api/investor/table.csv?market=SET|MAI` - Investor table CSV
- `GET /api/investor/chart.json?market=SET|MAI` - Investor chart JSON
- `GET /api/sector/constituents.csv?slug={sector}` - Sector constituents
- `POST /api/save-to-database` - Save all data to Supabase
- `GET /api/progress` - SSE progress stream
- `GET /api/progress/status` - Current progress JSON