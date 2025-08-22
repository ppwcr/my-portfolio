# Windows Setup Guide

## Quick Start

1. **Download/Clone the project** to a local folder (e.g., `C:\my-portfolio`)

2. **Open Command Prompt as Administrator** and navigate to the project folder:
   ```cmd
   cd C:\my-portfolio
   ```

3. **Run the troubleshooter** to check everything:
   ```cmd
   troubleshoot_windows.bat
   ```

4. **If all checks pass**, start the system:
   ```cmd
   start.bat
   ```

## Common Issues & Solutions

### ❌ "Could not import module 'main'"
**Problem**: Running from wrong directory
**Solution**: 
- Make sure you're in the project folder containing `main.py`
- Run `cd C:\path\to\my-portfolio` first
- Use `troubleshoot_windows.bat` to verify

### ❌ "Python not found"
**Problem**: Python not installed or not in PATH
**Solution**:
- Download Python 3.8+ from https://python.org
- **Important**: Check "Add Python to PATH" during installation
- Restart Command Prompt after installation

### ❌ "SUPABASE_URL not set"
**Problem**: Missing environment variables
**Solution**:
- Create a `.env` file in the project folder
- Add your Supabase credentials:
  ```
  SUPABASE_URL=your_supabase_url
  SUPABASE_SERVICE_KEY=your_supabase_key
  ```

### ❌ "Port 8000 already in use"
**Problem**: Another instance is running
**Solution**:
- Close any existing Command Prompt windows running the server
- Or kill the process: `taskkill /f /im python.exe`

## File Structure
Your project folder should contain:
```
my-portfolio/
├── main.py                    ← Main server file
├── auto_scraper.py           ← Auto-scraper
├── scheduled_scraper.py      ← Scheduled scraper
├── start.bat                 ← Windows startup script
├── troubleshoot_windows.bat  ← Troubleshooting tool
├── requirements.txt          ← Python dependencies
├── .env                      ← Your Supabase credentials
└── ... (other files)
```

## What Each Script Does

### `troubleshoot_windows.bat`
- Checks if you're in the correct directory
- Verifies Python installation
- Tests required packages
- Validates database connection
- **Run this first if you have issues**

### `start.bat`
- Starts the web server (http://127.0.0.1:8000)
- Launches auto-scraper (every 10 minutes)
- Launches scheduled scraper (10:30, 13:00, 17:30 weekdays)
- Opens browser automatically

### `setup.bat`
- Sets up auto-start when Windows boots
- Creates startup shortcut

## Network Access
The server runs on `http://0.0.0.0:8000` so you can access it from other devices on your network:
- Local: `http://127.0.0.1:8000`
- Network: `http://YOUR_IP:8000`

## Troubleshooting Steps

1. **Run troubleshooter**: `troubleshoot_windows.bat`
2. **Check directory**: Make sure you see `main.py` in the folder
3. **Check Python**: `python --version`
4. **Check dependencies**: `pip list`
5. **Check environment**: Verify `.env` file exists
6. **Restart Command Prompt** if you made changes

## Support
If you still have issues:
1. Run `troubleshoot_windows.bat` and note any error messages
2. Check that all files are present in your project folder
3. Ensure you're running Command Prompt as Administrator
4. Verify your Supabase credentials are correct
