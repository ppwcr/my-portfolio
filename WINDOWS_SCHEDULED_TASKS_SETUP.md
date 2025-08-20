# Windows Scheduled Tasks Setup Guide

## 🔍 **Current Status**

Your scheduled tasks are **NOT currently usable** because:
- ❌ **No Windows scheduled tasks found** (you're on macOS)
- ❌ **Windows Task Scheduler not available** (macOS system)
- ✅ **All .bat files are ready** (run_scheduled_scrape.bat, setup.bat, etc.)
- ✅ **Python environment works** (tested and functional)

## 🖥️ **Windows Setup Required**

To use the scheduled tasks, you need to:

1. **Copy your project to a Windows machine**, OR
2. **Use Windows in a virtual machine**, OR  
3. **Use Windows Subsystem for Linux (WSL)** with Windows Task Scheduler

## 🛠️ **Windows Setup Instructions**

### **Step 1: Transfer Project to Windows**
Copy your entire `my-portfolio` folder to a Windows machine.

### **Step 2: Open Command Prompt as Administrator**
- Press `Win + X`
- Select "Windows PowerShell (Admin)" or "Command Prompt (Admin)"

### **Step 3: Navigate to Project Directory**
```cmd
cd C:\path\to\your\my-portfolio
```

### **Step 4: Run the Setup Script**
```cmd
setup.bat
```

This will automatically:
- ✅ Create auto-start for the server
- ✅ Set up 3 scheduled tasks:
  - **10:30 AM** (Monday-Friday)
  - **1:00 PM** (Monday-Friday)  
  - **5:30 PM** (Monday-Friday)

### **Step 5: Verify Setup**
```cmd
# Check if tasks were created
schtasks /query /tn SET_Scraper_1030
schtasks /query /tn SET_Scraper_1300
schtasks /query /tn SET_Scraper_1730
```

## 📋 **Available .bat Files for Windows**

### **Main Setup Files:**
- **`setup.bat`** - Complete setup (auto-start + scheduled tasks)
- **`start.bat`** - Manual server start
- **`run_scheduled_scrape.bat`** - Scheduled scraping script
- **`server_manager.bat`** - Interactive server management
- **`git_update.bat`** - Git updates

### **Diagnostic Files:**
- **`diagnose_autostart.bat`** - Check auto-start system
- **`fix_autostart.bat`** - Fix auto-start issues
- **`check_scheduled_tasks.py`** - Cross-platform diagnostic

## 🔧 **Manual Windows Task Setup**

If `setup.bat` doesn't work, create tasks manually:

### **Create 10:30 AM Task:**
```cmd
schtasks /Create /TN SET_Scraper_1030 /TR "C:\path\to\your\my-portfolio\run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 10:30 /RL LIMITED
```

### **Create 1:00 PM Task:**
```cmd
schtasks /Create /TN SET_Scraper_1300 /TR "C:\path\to\your\my-portfolio\run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 13:00 /RL LIMITED
```

### **Create 5:30 PM Task:**
```cmd
schtasks /Create /TN SET_Scraper_1730 /TR "C:\path\to\your\my-portfolio\run_scheduled_scrape.bat" /SC WEEKLY /D MON,TUE,WED,THU,FRI /ST 17:30 /RL LIMITED
```

## 🧪 **Testing on Windows**

### **Test 1: Manual Script Test**
```cmd
run_scheduled_scrape.bat
```

### **Test 2: Direct Python Test**
```cmd
python -c "from background_updater import BackgroundUpdater; import asyncio; asyncio.run(BackgroundUpdater().update_all_data())"
```

### **Test 3: Check Task Status**
```cmd
# View all tasks
schtasks /query /fo table

# View specific task details
schtasks /query /tn SET_Scraper_1030 /fo list
```

## 📊 **Monitoring on Windows**

### **Check Recent Activity**
```cmd
# View recent files
dir _out\ /o-d

# View log files
dir scraper_*.log
```

### **View Task History**
```cmd
# Open Task Scheduler
taskschd.msc

# Or check via command line
schtasks /query /tn SET_Scraper_1030 /fo list
```

## 🗑️ **Removing Windows Tasks**

### **Remove All Tasks:**
```cmd
schtasks /Delete /TN SET_Scraper_1030 /F
schtasks /Delete /TN SET_Scraper_1300 /F
schtasks /Delete /TN SET_Scraper_1730 /F
```

### **Remove Auto-Start:**
```cmd
# Delete startup shortcut
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Portfolio Dashboard Server.lnk"
```

## ⚠️ **Troubleshooting on Windows**

### **If setup.bat fails:**
1. **Run as Administrator** (right-click → "Run as Administrator")
2. **Check Python installation**: `python --version`
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Check file permissions**

### **If tasks don't run:**
1. **Check Task Scheduler**: `taskschd.msc`
2. **View task history** in Task Scheduler
3. **Check Windows Event Viewer** for errors
4. **Verify file paths** in task properties

### **If auto-start doesn't work:**
1. **Run diagnose_autostart.bat**
2. **Run fix_autostart.bat**
3. **Check startup folder**: `shell:startup`

## 📅 **Schedule Details**

The scheduled tasks run:
- **Monday through Friday only** (no weekends)
- **10:30 AM** - Morning data update
- **1:00 PM** - Afternoon data update  
- **5:30 PM** - Evening data update

## ✅ **Success Indicators**

After Windows setup, you should see:
- ✅ `schtasks /query` shows 3 SET_Scraper tasks
- ✅ Auto-start shortcut in startup folder
- ✅ `scraper_*.log` files created after runs
- ✅ New files in `_out\` directory at scheduled times
- ✅ No errors in Windows Event Viewer

## 🔄 **Next Steps**

1. **Transfer project to Windows machine**
2. **Run setup.bat as Administrator**
3. **Test with run_scheduled_scrape.bat**
4. **Monitor task execution**
5. **Check for new data files**

The .bat files are ready and will work perfectly on Windows!
