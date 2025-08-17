# Auto-Start Setup Guide for Portfolio Dashboard

This guide explains how to set up the Portfolio Dashboard to automatically start when Windows boots up.

## 🚀 Quick Setup (Recommended)

### Method 1: Hidden Auto-Start (Best User Experience)

1. **Right-click** `setup_autostart.bat`
2. Select **"Run as administrator"**
3. **Follow the prompts** and wait for completion
4. **Restart your computer** to test

**Features:**
- ✅ Runs silently in background (no visible terminal)
- ✅ Automatically opens browser to portfolio page
- ✅ Most user-friendly experience
- ✅ Easy to disable if needed

---

## 🔧 Alternative Methods

### Method 2: Windows Task Scheduler

1. **Right-click** `setup_task_scheduler.bat`
2. Select **"Run as administrator"**
3. **Follow the prompts** and wait for completion
4. **Restart your computer** to test

**Features:**
- ✅ More reliable (Windows manages it)
- ✅ Can be easily disabled/enabled
- ✅ Shows terminal window for debugging
- ✅ Better for system administrators

### Method 3: Manual Startup Folder

1. **Right-click** `setup_manual_startup.bat`
2. Select **"Run as administrator"**
3. **Follow the prompts** and wait for completion
4. **Restart your computer** to test

**Features:**
- ✅ Simplest setup process
- ✅ Easy to understand and modify
- ✅ Shows terminal window
- ✅ Direct file-based approach

---

## 🚫 How to Disable Auto-Start

### For Method 1 & 3 (Startup Folder):

1. Press **Win + R** to open Run dialog
2. Type **`shell:startup`** and press Enter
3. Delete the file:
   - **Method 1:** Delete `Portfolio Dashboard.lnk`
   - **Method 3:** Delete `Portfolio Dashboard.bat`

### For Method 2 (Task Scheduler):

1. Open **Task Scheduler** (search in Windows Start menu)
2. Navigate to **Task Scheduler Library**
3. Find **"Portfolio Dashboard"** task
4. **Right-click** → Select **"Disable"** or **"Delete"**

---

## 🔍 Troubleshooting

### Issue: Auto-start not working

**Check these:**
1. **Did you run as administrator?** - Right-click → "Run as administrator"
2. **Is Python installed?** - Open Command Prompt and type `python --version`
3. **Are dependencies installed?** - Run `pip install -r requirements.txt`
4. **Check Windows startup folder:**
   - Press **Win + R**
   - Type **`shell:startup`** and press Enter
   - Verify the shortcut/file exists

### Issue: Browser doesn't open automatically

**Solutions:**
1. **Wait longer** - Server takes time to start (3-second delay)
2. **Check firewall** - Allow Python/uvicorn through Windows Firewall
3. **Manual test** - Open `http://127.0.0.1:8000/portfolio` in browser

### Issue: Server starts but crashes

**Solutions:**
1. **Check dependencies** - Run `pip install -r requirements.txt`
2. **Check Python version** - Must be 3.8 or higher
3. **Check port availability** - Port 8000 might be in use
4. **Run manually first** - Test with `start.bat` before setting up auto-start

---

## 📋 Manual Setup (Advanced Users)

### Create Auto-Start Manually:

1. **Open Startup Folder:**
   - Press **Win + R**
   - Type **`shell:startup`** and press Enter

2. **Create Shortcut:**
   - Right-click in startup folder
   - Select **New** → **Shortcut**
   - Browse to your `start.bat` file
   - Name it **"Portfolio Dashboard"**

3. **Test:**
   - Restart your computer
   - Check if application starts automatically

---

## ⚙️ Configuration Options

### Change Port (if 8000 is busy):

1. **Edit `start.bat`:**
   ```batch
   uvicorn main:app --reload --host 127.0.0.1 --port 8001
   ```

2. **Update browser URL:**
   ```batch
   start "" http://127.0.0.1:8001/portfolio
   ```

### Change Startup Delay:

1. **Edit `start.bat`:**
   ```batch
   timeout /t 5 /nobreak >nul  # Change 3 to 5 seconds
   ```

### Run Without Browser Auto-Open:

1. **Edit `start.bat`:**
   - Remove or comment out the `start "" http://127.0.0.1:8000/portfolio` line

---

## 🔒 Security Considerations

### Running as Administrator:
- **Required** for setting up auto-start
- **Not required** for normal operation
- **Safe** - only modifies startup settings

### Network Access:
- **Local only** - runs on 127.0.0.1 (localhost)
- **No external access** by default
- **Firewall friendly** - doesn't require external ports

### Data Privacy:
- **No data collection** - runs locally
- **No internet required** for basic operation
- **yfinance data** - only fetches public stock data

---

## 📞 Support

### If Auto-Start Still Doesn't Work:

1. **Check Windows Event Viewer:**
   - Press **Win + R**
   - Type **`eventvwr.msc`** and press Enter
   - Look for errors in **Windows Logs** → **Application**

2. **Test Manual Startup:**
   - Double-click `start.bat`
   - Verify it works manually first

3. **Check System Requirements:**
   - Windows 10/11
   - Python 3.8+
   - Internet connection (for stock data)

4. **Alternative Approach:**
   - Use **Method 2 (Task Scheduler)** instead
   - More reliable for some systems

---

## 🎯 Expected Behavior

### After Setup:
1. **Computer boots up**
2. **Portfolio Dashboard starts** (hidden or visible)
3. **Browser opens** to `http://127.0.0.1:8000/portfolio`
4. **Mini charts load** one by one with delays
5. **Application runs** until computer shuts down

### Performance:
- **Startup time:** 10-30 seconds (depending on system)
- **Memory usage:** ~50-100MB
- **CPU usage:** Low (mostly idle)
- **Network usage:** Only when fetching stock data

---

## 📝 Notes

- **First startup** may take longer due to dependency installation
- **Internet connection** required for stock data fetching
- **Windows updates** may reset startup settings
- **Antivirus software** may block auto-start (add to exceptions)
- **Multiple users** - each user needs separate setup

---

*Last updated: January 2025*
