# Windows Setup Guide for Portfolio Dashboard

## Quick Start

1. **Double-click `start.bat`** to automatically install dependencies and start the server
2. **Open your browser** and go to `http://127.0.0.1:8000/portfolio`
3. **Wait for mini charts to load** - they will appear one by one with 1-second delays

## Manual Setup (if start.bat doesn't work)

### 1. Install Python
- Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation

### 2. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 3. Install Playwright
```cmd
playwright install
```

### 4. Start Server
```cmd
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Troubleshooting

### Issue: "503 Service Unavailable" errors
**Solution:** The server is getting overwhelmed. The updated code now:
- Waits 1 second between chart requests (instead of 300ms)
- Retries 503 errors with longer delays (2-4 seconds)
- Shows ⚠️ instead of ! for persistent 503 errors

### Issue: "No module named yfinance"
**Solution:** Install the missing dependency:
```cmd
pip install yfinance>=0.2.30
```

### Issue: "Port 8000 already in use"
**Solution:** Use a different port:
```cmd
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### Issue: SSL Certificate errors
**Solution:** Install certifi:
```cmd
pip install certifi
```

### Issue: Charts not loading
**Check:**
1. Server is running (you should see "Uvicorn running on http://127.0.0.1:8000")
2. No error messages in the terminal
3. Browser console (F12) for JavaScript errors
4. Network tab in DevTools for failed API calls

### Issue: Slow chart loading
**This is normal!** The charts load one by one with delays to prevent server overload:
- First chart: 0 seconds
- Second chart: 1 second
- Third chart: 2 seconds
- etc.

## Expected Behavior

1. **Page loads** with portfolio table
2. **Loading indicators** show "..." for each chart
3. **Charts appear gradually** with 1-second intervals
4. **Failed charts** show retry indicators (↻, ↻↻, ↻↻↻)
5. **Persistent failures** show ⚠️

## Performance Tips

- **Close other applications** to free up system resources
- **Use a wired internet connection** for better yfinance data fetching
- **Wait for all charts to load** before refreshing the page
- **Don't open multiple browser tabs** of the same page

## Support

If you're still having issues:
1. Check the terminal for error messages
2. Check browser console (F12) for JavaScript errors
3. Try restarting the server
4. Make sure you have a stable internet connection
