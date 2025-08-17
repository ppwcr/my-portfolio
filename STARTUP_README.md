# Portfolio Dashboard Auto-Startup with Database Update

This guide explains how to set up the Portfolio Dashboard to automatically start when your PC boots and update the database with fresh market data.

## Quick Setup

### Option 1: Auto-Start with Database Update (Recommended)
1. Run `setup_autostart.bat` as Administrator
2. This will set up the dashboard to:
   - Start automatically when you log in to Windows
   - Update database with fresh market data on startup
   - Continue with automatic background updates every 30 minutes

### Option 2: Manual Start with Database Update
- Double-click `start_with_db_update.bat` to start with database update
- Double-click `start.bat` to start without database update (uses existing data)

## What Happens on Startup

1. **Database Update**: Downloads fresh market data (1-2 minutes)
   - Investor data (SET/MAI)
   - Sector data (all 8 SET sectors)
   - Historical price data

2. **Server Start**: Launches the FastAPI server on `http://127.0.0.1:8000`

3. **Browser Opens**: Automatically opens the dashboard in your default browser

4. **Ready to Use**: Dashboard is ready with fresh data, no further automatic updates

## Files Created

- `startup_with_update.py`: Python script that handles database update and server startup
- `start_with_db_update.bat`: Windows batch file that calls the Python startup script
- `setup_autostart.bat`: Modified to use the new startup script with database update

## UI Changes

- **Removed "Update Database" button**: No longer needed since database updates happen automatically
- **Status display**: Shows when the last update occurred and current update status
- **Manual refresh**: "Refresh Data" button reloads from database without updating it

## Troubleshooting

### If auto-start doesn't work:
1. Run `setup_autostart.bat` as Administrator
2. Check if Python is in your PATH
3. Ensure all dependencies are installed (`pip install -r requirements.txt`)

### If database update fails:
- The server will still start with existing data
- Use "Refresh Data" button to reload from database
- Check internet connection and Supabase credentials in `.env` file

### To disable auto-start:
1. Press `Win+R`, type `shell:startup`, press Enter
2. Delete `Portfolio Dashboard.lnk`

## Benefits

✅ **Hands-off operation**: No manual intervention needed
✅ **Fresh data**: Always starts with latest market data  
✅ **Single update**: Updates only on startup, no background updates
✅ **Clean UI**: Simple "Refresh Data" button reloads from database
✅ **Reliable**: Auto-retry mechanisms for failed updates
✅ **Fast loading**: Data appears instantly from database

## Technical Details

- **Startup time**: 2-3 minutes (including database update)
- **Update frequency**: Only on PC startup
- **Memory usage**: ~50-100MB
- **Network usage**: ~1-5MB on startup
- **Dependencies**: Python 3.8+, FastAPI, Playwright, Supabase