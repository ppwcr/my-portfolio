# SET Data Export Panel

A full-stack web application that provides a floating panel UI for exporting data from the Stock Exchange of Thailand (SET) using four Python scraping scripts.

## Features

- **Floating Panel UI**: Modern, responsive interface positioned bottom-right
- **NVDR Data**: Download NVDR trading-by-stock Excel files
- **Short Sales Data**: Download short sales Excel files  
- **Investor Type Data**: Export investor type tables (CSV) and charts (JSON) for SET/MAI
- **Sector Constituents**: Export sector index constituent lists (CSV)
- **Real-time Status**: Visual feedback with spinners and success indicators
- **Error Handling**: Toast notifications for errors with helpful messages
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

### 2. Verify Scripts

Ensure these four Python scripts are in the project root:
- `download_nvdr_excel.py`
- `download_short_sales_excel.py`
- `scrape_investor_type_simple.py`
- `scrape_set_sectors_jina.py`

### 3. Run the Application

```bash
python main.py
```

The app will start on `http://localhost:8000`

### 4. Access the Panel

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

## Environment Variables

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
├── scrape_investor_type_simple.py   # Investor type scraper
└── scrape_set_sectors_jina.py       # Sector scraper
```

## Error Handling

The application provides consistent error handling across all endpoints:

- **504 Timeout**: Command took too long to complete
- **404 Not Found**: Output file not generated
- **500 Server Error**: Script execution failed
- **Toast Notifications**: User-friendly error messages

## Keyboard Shortcuts

- **Ctrl/Cmd + 1**: NVDR Excel download
- **Ctrl/Cmd + 2**: Short Sales Excel download  
- **Ctrl/Cmd + 3**: Investor Table CSV download
- **Ctrl/Cmd + 4**: Sector Constituents CSV download

## Troubleshooting

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
python scrape_investor_type_simple.py --market SET
```

### Output Directory
The app creates an `_out/` directory for generated files. Check this directory if downloads aren't working.

## Development

### Adding New Endpoints
1. Add endpoint in `main.py`
2. Add button in `templates/index.html`
3. Add event handler in `static/app.js`
4. Update CSS if needed

### Customizing the Panel
- Modify `static/app.css` for styling changes
- Update `templates/index.html` for layout changes
- Extend `static/app.js` for new functionality

## License

This project is for educational and research purposes. Please respect the SET website's terms of service when using the scrapers.

## Support

For issues related to:
- **Web App**: Check FastAPI logs in terminal
- **Scrapers**: Test individual scripts directly
- **Browser**: Verify Playwright installation
- **Network**: Check internet connectivity and SET website availability
