# SET Data Export Panel

A full-stack web application that provides a floating panel UI for exporting data from the Stock Exchange of Thailand (SET) using Python scraping scripts and storing data in a Supabase database.

## Features

- **Floating Panel UI**: Modern, responsive interface positioned bottom-right
- **NVDR Data**: Download NVDR trading-by-stock Excel files
- **Short Sales Data**: Download short sales Excel files  
- **Investor Type Data**: Export investor type tables (CSV) and charts (JSON) for SET/MAI
- **Sector Constituents**: Export sector index constituent lists (CSV)
- **Database Integration**: Save all data to Supabase database with progress tracking
- **Real-time Progress**: Server-Sent Events for live progress updates
- **Error Handling**: Comprehensive error handling with detailed feedback
- **Keyboard Shortcuts**: Quick access with Ctrl/Cmd + 1-4

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies for the web app
pip install -r requirements.txt

# Install Playwright for browser automation (required for Excel downloads)
pip install playwright
python -m playwright install chromium
```

### 2. Environment Setup

Create a `.env` file based on `.env.example`:

```bash
# Copy the example file
cp .env.example .env

# Edit with your Supabase credentials
nano .env
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key

### 3. Verify Scripts

Ensure these Python scripts are in the project root:
- `download_nvdr_excel.py`
- `download_short_sales_excel.py`
- `scrape_investor_data.py`
- `scrape_sector_data.py`
- `supabase_database.py`

### 4. Run the Application

```bash
python main.py
```

The app will start on `http://localhost:8000`

### 5. Access the Panel

Open your browser and navigate to `http://localhost:8000` to see the floating export panel.

## API Endpoints

### NVDR Excel Export
- **GET** `/api/nvdr/export.xlsx`
- Downloads NVDR trading-by-stock data as Excel file
- Returns: `nvdr_trading_by_stock.xlsx`

### Short Sales Excel Export  
- **GET** `/api/short-sales/export.xlsx`
- Downloads short sales data as Excel file
- Returns: `short_sales_data.xlsx`

### Investor Type Table
- **GET** `/api/investor/table.csv?market=SET|MAI`
- Exports investor type table as CSV
- Parameters: `market` (default: SET)
- Returns: `investor_table_{market}.csv`

### Investor Type Chart
- **GET** `/api/investor/chart.json?market=SET|MAI`
- Exports investor type chart data as JSON
- Parameters: `market` (default: SET)
- Returns: `investor_chart_{market}.json`

### Sector Constituents
- **GET** `/api/sector/constituents.csv?slug={sector}`
- Exports sector constituents as CSV
- Parameters: `slug` (agro|consump|fincial|indus|propcon|resourc|service|tech)
- Returns: `{slug}_constituents.csv`

### Database Save
- **POST** `/api/save-to-database`
- Saves all scraped data to Supabase database
- Includes progress tracking via Server-Sent Events
- Returns: JSON with save results for each data type

### Progress Tracking
- **GET** `/api/progress`
- Server-Sent Events stream for real-time progress updates
- **GET** `/api/progress/status`
- Current progress status as JSON

## Environment Variables

### Database Configuration
```bash
# Supabase credentials (required)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
```

### Browser Options
```bash
# Run browser in headful mode (visible)
export HEADFUL=1

# Run without sandbox (for some Linux environments)
export NO_SANDBOX=1
```

### SSH Tunnel (for remote access)
```bash
# Forward local port 8000 to remote server
ssh -L 8000:localhost:8000 user@remote-server

# Then access via http://localhost:8000 on your local machine
```

## File Structure

```
my-portfolio/
├── main.py                          # FastAPI application
├── requirements.txt                  # Python dependencies
├── supabase_database.py             # Database operations
├── templates/
│   └── index.html                   # Main page template
├── static/
│   ├── app.css                      # Panel styling
│   └── app.js                       # Frontend logic
├── _out/                            # Generated output files
│   ├── investor/                    # Investor type data
│   └── sectors_*/                   # Sector data (timestamped)
├── download_nvdr_excel.py           # NVDR scraper
├── download_short_sales_excel.py    # Short sales scraper
├── scrape_investor_data.py          # Investor type scraper
├── scrape_sector_data.py            # Sector scraper
├── excel_file_parser.py             # Excel parsing utilities
└── .env.example                     # Environment variables template
```

## Database Schema

The application saves data to the following Supabase tables:

### Investor Summary
- Stores investor type data for SET/MAI markets
- Includes trade date and investor categories

### Sector Data
- Stores constituent data for all 8 SET sectors
- Includes stock symbols, weights, and trade dates

### NVDR Trading
- Stores NVDR trading-by-stock data
- Includes trade date and stock-specific data

### Short Sales Trading
- Stores short sales data
- Includes trade date and short sales information

## Error Handling

The application provides comprehensive error handling:

- **504 Timeout**: Command took too long to complete
- **404 Not Found**: Output file not generated
- **500 Server Error**: Script execution failed
- **Progress Tracking**: Real-time status updates via SSE
- **Fallback Mechanisms**: Uses cached data when scraping fails
- **Toast Notifications**: User-friendly error messages

## Keyboard Shortcuts

- **Ctrl/Cmd + 1**: NVDR Excel download
- **Ctrl/Cmd + 2**: Short Sales Excel download  
- **Ctrl/Cmd + 3**: Investor Table CSV download
- **Ctrl/Cmd + 4**: Sector Constituents CSV download

## Progress Tracking

The application provides real-time progress updates for database operations:

1. **Investor Data Scraping** (10-30%)
2. **Sector Data Scraping** (35-60%)
3. **Sector Data Processing** (60-90%)
4. **NVDR Data Processing** (90-93%)
5. **Short Sales Processing** (95-98%)
6. **Completion** (100%)

## Troubleshooting

### Database Issues
```bash
# Check Supabase connection
python -c "from supabase_database import get_proper_db; db = get_proper_db(); print('Connected!')"

# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

### Playwright Issues
```bash
# Reinstall Playwright browsers
python -m playwright install --force

# Run with no sandbox (Linux)
export NO_SANDBOX=1
python main.py
```

### Permission Issues
```bash
# Make scripts executable
chmod +x *.py

# Check Python path
which python
```

### Network Issues
```bash
# Test individual scripts
python download_nvdr_excel.py --out test.xlsx
python scrape_investor_data.py --market SET
```

### Output Directory
The app creates an `_out/` directory for generated files. Check this directory if downloads aren't working.

## Development

### Adding New Endpoints
1. Add endpoint in `main.py`
2. Add button in `templates/index.html`
3. Add event handler in `static/app.js`
4. Update CSS if needed

### Database Operations
- Add new table methods in `supabase_database.py`
- Update progress tracking in main.py
- Test with sample data

### Customizing the Panel
- Modify `static/app.css` for styling changes
- Update `templates/index.html` for layout changes
- Extend `static/app.js` for new functionality

## License

This project is for educational and research purposes. Please respect the SET website's terms of service when using the scrapers.

## Support

For issues related to:
- **Web App**: Check FastAPI logs in terminal
- **Database**: Verify Supabase credentials and connection
- **Scrapers**: Test individual scripts directly
- **Browser**: Verify Playwright installation
- **Network**: Check internet connectivity and SET website availability
