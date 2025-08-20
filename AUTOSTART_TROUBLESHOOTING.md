# Auto-Start Troubleshooting Guide

## 🔍 **Root Cause Analysis**

After analyzing your auto-start .bat file setup, I identified several critical issues that prevent auto-start from working correctly:

### **1. VBS Script Path Issues (CRITICAL)**
**Problem:** The original `setup.bat` created VBS scripts in `%TEMP%` directory
```batch
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\portfolio_startup_server.vbs"
```

**Why it fails:**
- `%TEMP%` directory gets cleared on system restart
- VBS script disappears after reboot
- Startup shortcut points to non-existent file

**Solution:** Create VBS script in project directory instead
```batch
set "VBS_PATH=%CURRENT_DIR%portfolio_startup_server.vbs"
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
```

### **2. Startup Folder Detection Issues**
**Problem:** Registry query for startup folder can fail
```batch
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"
```

**Why it fails:**
- Registry query may not work on all Windows versions
- No fallback if query fails
- No validation that folder exists

**Solution:** Multiple fallback methods
```batch
REM Method 1: Registry query
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Startup 2^>nul') do set "STARTUP_FOLDER=%%b"

REM Method 2: Environment variable
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
)

REM Method 3: Common location
if not defined STARTUP_FOLDER (
    set "STARTUP_FOLDER=%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
)
```

### **3. Missing Error Handling**
**Problem:** Setup continues even if critical steps fail
**Solution:** Added validation and error checking for each step

### **4. PowerShell Command Issues**
**Problem:** Complex PowerShell command may fail silently
**Solution:** Better error handling and exit codes

## 🛠️ **Solutions Implemented**

### **1. Fixed setup.bat**
- ✅ VBS script created in project directory (permanent)
- ✅ Multiple startup folder detection methods
- ✅ File existence validation
- ✅ Better error handling and user feedback
- ✅ Detailed troubleshooting information

### **2. Created diagnose_autostart.bat**
- ✅ Comprehensive system check
- ✅ Validates all auto-start components
- ✅ Tests VBS script syntax
- ✅ Checks permissions and file access
- ✅ Provides specific troubleshooting steps

### **3. Created fix_autostart.bat**
- ✅ Quick fix for common issues
- ✅ Recreates VBS script and shortcut
- ✅ Minimal setup without full reinstall
- ✅ Clear success/failure feedback

## 🚀 **How to Fix Auto-Start Issues**

### **Step 1: Run Diagnostics**
```cmd
diagnose_autostart.bat
```
This will identify exactly what's wrong with your auto-start setup.

### **Step 2: Apply Fix**
```cmd
fix_autostart.bat
```
This will recreate the VBS script and startup shortcut.

### **Step 3: Test**
1. Restart your computer
2. Check if server starts automatically
3. If not, run diagnostics again

### **Step 4: Full Setup (if needed)**
```cmd
setup.bat
```
Run as Administrator for complete setup including scheduled tasks.

## 🔧 **Manual Troubleshooting**

### **Check Auto-Start Components**
```cmd
# Check if VBS script exists
dir portfolio_startup_server.vbs

# Check if startup shortcut exists
# Press Win+R, type "shell:startup", press Enter
# Look for "Portfolio Dashboard Server.lnk"

# Test VBS script manually
cscript //nologo portfolio_startup_server.vbs

# Check scheduled tasks
schtasks /query /tn SET_Scraper_1030
```

### **Common Issues and Solutions**

**Issue: "VBS script not found"**
```cmd
# Recreate VBS script
echo Set WshShell = CreateObject("WScript.Shell") > portfolio_startup_server.vbs
echo WshShell.Run """start.bat""", 0, False >> portfolio_startup_server.vbs
```

**Issue: "Startup folder not found"**
```cmd
# Common startup folder locations:
# %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
# %USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

**Issue: "Permission denied"**
```cmd
# Run as Administrator
# Right-click Command Prompt → "Run as Administrator"
```

**Issue: "PowerShell execution policy"**
```cmd
# Check execution policy
Get-ExecutionPolicy

# If restricted, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📋 **Checklist for Working Auto-Start**

- [ ] `start.bat` exists in project directory
- [ ] `portfolio_startup_server.vbs` exists in project directory
- [ ] Startup shortcut exists in Windows startup folder
- [ ] VBS script syntax is valid
- [ ] Startup folder is writable
- [ ] Python is installed and in PATH
- [ ] FastAPI is installed
- [ ] Running as Administrator (for scheduled tasks)

## 🗑️ **Removing Auto-Start**

### **Remove Startup Shortcut**
```cmd
# Press Win+R, type "shell:startup", press Enter
# Delete "Portfolio Dashboard Server.lnk"
```

### **Remove VBS Script**
```cmd
del portfolio_startup_server.vbs
```

### **Remove Scheduled Tasks**
```cmd
schtasks /Delete /TN SET_Scraper_1030 /F
schtasks /Delete /TN SET_Scraper_1300 /F
schtasks /Delete /TN SET_Scraper_1730 /F
```

## 📞 **Getting Help**

If auto-start still doesn't work after following these steps:

1. Run `diagnose_autostart.bat` and note the error count
2. Check Windows Event Viewer for errors
3. Try manually running `start.bat` to see if it works
4. Check if antivirus is blocking the startup
5. Verify Python environment is working correctly

The diagnostic script will provide specific guidance based on what it finds.
