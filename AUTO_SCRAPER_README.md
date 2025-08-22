# 🤖 Auto-Scraper System

This system automatically scrapes data every 10 minutes and keeps your web dashboard updated with the latest information.

## 🚀 Features

- **Automatic Data Scraping**: Runs every 10 minutes
- **Database Optimization**: Keeps only the latest data for each date (saves space)
- **Web Auto-Refresh**: Dashboard automatically updates when new data arrives
- **Background Operation**: Runs independently of the web server
- **Easy Control**: Start/stop from the web interface

## 📊 What Gets Scraped

### 🤖 Auto-Scraper (Every 10 minutes)
Runs these core market data scripts continuously:
1. `scrape_sector_data.py` - SET sector constituents (real-time market data)
2. `scrape_set_index.py` - SET index data (real-time market data)

### 📅 Scheduled Scraper (Weekdays at 10:30, 13:00, 17:30)
Runs full updates of all data sources:
1. `scrape_investor_data.py` - Investor summary data
2. `scrape_sector_data.py` - SET sector constituents
3. `scrape_set_index.py` - SET index data
4. `download_nvdr_excel.py` - NVDR trading data
5. `download_short_sales_excel.py` - Short sales data

**Hybrid System**: Combines real-time updates (every 10 minutes) with scheduled full updates (3 times per weekday) for comprehensive data coverage.

## 🗄️ Database Optimization

The auto-scraper automatically cleans up old data to save database space:
- **Keeps**: Today's and yesterday's data
- **Deletes**: Data older than 2 days
- **Result**: Only the latest data for each date is preserved
- **Focus**: Only cleans up sector_data and set_index tables (the ones being auto-scraped)

## 🌐 Web Interface Controls

### Auto-Scraper Controls
- **Start Auto-Scrape**: Start the automatic scraping service
- **Stop Auto-Scrape**: Stop the automatic scraping service
- **Status**: Shows if auto-scraper is running

### Auto-Refresh
- The web page automatically checks for updates every 30 seconds
- When new data is detected, the dashboard refreshes automatically
- You'll see a notification when data is updated

## 🛠️ Manual Usage

### Start Complete System (Recommended)
```bash
python start.bat
```

### Start Auto-Scraper Only
```bash
python auto_scraper.py
```

### Start Scheduled Scraper Only
```bash
python scheduled_scraper.py
```

### API Endpoints

#### Check Auto-Scraper Status
```bash
curl http://localhost:8000/api/auto-scraper/status
```

#### Start Auto-Scraper
```bash
curl -X POST http://localhost:8000/api/auto-scraper/start
```

#### Stop Auto-Scraper
```bash
curl -X POST http://localhost:8000/api/auto-scraper/stop
```

#### Check for Data Updates
```bash
curl http://localhost:8000/api/data/check-updates
```

## 📝 Logs

The auto-scraper creates detailed logs in `auto_scraper.log`:
- Scraping success/failure
- Database cleanup operations
- Error messages and debugging info

## ⚙️ Configuration

### Scraping Interval
To change the scraping interval, edit `auto_scraper.py`:
```python
# Change from 10 minutes to any interval
schedule.every(10).minutes.do(auto_scrape)
```

### Data Retention
To change how long data is kept, edit the cleanup function:
```python
# Keep data for more days
cutoff_date = (today - timedelta(days=7)).isoformat()  # Keep 7 days
```

### Auto-Refresh Interval
To change how often the web page checks for updates, edit `templates/portfolio.html`:
```javascript
// Change from 30 seconds to any interval
autoRefreshInterval = setInterval(checkForUpdates, 60000); // Check every 60 seconds
```

## 🔧 Troubleshooting

### Auto-Scraper Not Starting
1. Check if port 8000 is available
2. Ensure all dependencies are installed: `pip install schedule psutil`
3. Check the log file: `tail -f auto_scraper.log`

### Web Page Not Auto-Refreshing
1. Check browser console for JavaScript errors
2. Verify the auto-scraper is running: `curl http://localhost:8000/api/auto-scraper/status`
3. Check if data updates are being detected: `curl http://localhost:8000/api/data/check-updates`

### Database Space Issues
1. Check if cleanup is working: Look for cleanup messages in `auto_scraper.log`
2. Manually run cleanup: The auto-scraper includes a `cleanup_old_data()` function

## 📈 Benefits

1. **Always Fresh Data**: Your dashboard always shows the latest market data
2. **Efficient Storage**: Database stays lean with only recent data
3. **No Manual Work**: Set it and forget it
4. **Real-time Updates**: Web interface updates automatically
5. **Reliable**: Runs in the background with error handling and logging

## 🎯 Use Cases

- **Trading Desks**: Always have the latest market data
- **Portfolio Management**: Real-time portfolio monitoring
- **Research**: Automated data collection for analysis
- **Monitoring**: Continuous market surveillance

The auto-scraper system ensures your SET portfolio dashboard is always up-to-date with minimal manual intervention! 🚀
