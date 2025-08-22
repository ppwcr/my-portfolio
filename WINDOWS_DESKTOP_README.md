# SET Portfolio Manager - Windows Desktop Application

This guide explains how to build and run the SET Portfolio Manager as a native Windows desktop application using Electron.

## 🖥️ What You Get

- **Native Windows Application**: No web browser needed
- **Desktop Window**: Looks and feels like a native Windows app
- **Same Functionality**: All your existing FastAPI logic works unchanged
- **Professional UI**: Windows-style menus, icons, and behavior
- **Easy Distribution**: Create installers or portable executables

## 📋 Prerequisites

### Required Software

1. **Node.js** (v16 or higher)
   - Download from: https://nodejs.org/
   - Choose LTS version

2. **Python** (v3.8 or higher)
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

3. **Git** (optional)
   - Download from: https://git-scm.com/

### Python Dependencies

Make sure all your Python dependencies are installed:
```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Option 1: Development Mode (Recommended for testing)

1. **Run the development script:**
   ```bash
   # Double-click the batch file
   run-windows-app.bat
   
   # Or use command line
   cd electron-app
   npm install
   npm run dev
   ```

2. **The application will:**
   - Start the Python backend server
   - Open a native Windows window
   - Load your FastAPI application
   - Show developer tools (for debugging)

### Option 2: Build Production Application

1. **Build the application:**
   ```bash
   # Double-click the batch file
   build-windows-app.bat
   
   # Or use command line
   cd electron-app
   npm install
   npm run build-win
   ```

2. **Find your application:**
   - **Portable**: `electron-app/dist-windows/SET-Portfolio-Manager-Portable.exe`
   - **Installer**: `electron-app/dist-windows/SET Portfolio Manager Setup.exe`

## 🛠️ Manual Build Process

### Step 1: Install Dependencies

```bash
cd electron-app
npm install
```

### Step 2: Test Development Mode

```bash
npm run dev
```

### Step 3: Build Production Version

```bash
# Build portable executable
npm run build-win-portable

# Build installer
npm run build-win-installer

# Build both
npm run build-win
```

## 📁 File Structure

```
my-portfolio/
├── electron-app/
│   ├── main-windows.js          # Windows-specific Electron main process
│   ├── package-windows.json     # Windows build configuration
│   ├── preload.js               # Preload script for security
│   ├── assets/
│   │   ├── icon.ico            # Windows application icon
│   │   └── icon.svg            # Source icon
│   └── dist-windows/           # Build output directory
├── main.py                     # Your existing FastAPI application (unchanged)
├── requirements.txt            # Python dependencies (unchanged)
├── build-windows-app.bat       # Build script
├── run-windows-app.bat         # Development script
└── WINDOWS_DESKTOP_README.md   # This file
```

## 🎯 Features

### Native Windows Experience
- **Windows-style window**: Title bar, minimize/maximize/close buttons
- **System menu**: File, View, Help menus with keyboard shortcuts
- **Taskbar integration**: Shows in Windows taskbar
- **Start menu**: Can be pinned to Start menu
- **Desktop shortcut**: Optional desktop shortcut creation

### Application Features
- **No browser needed**: Runs as a native Windows application
- **Same functionality**: All your existing FastAPI endpoints work
- **Developer tools**: Press F12 to open developer tools
- **Auto-refresh**: Ctrl+R to refresh the application
- **External links**: Opens external links in default browser

### Build Options
- **Portable**: Single .exe file that can run anywhere
- **Installer**: Professional installer with Start menu integration
- **Auto-updates**: Framework for future auto-update functionality

## 🔧 Configuration

### Application Settings

Edit `electron-app/main-windows.js` to customize:

```javascript
// Window size and behavior
mainWindow = new BrowserWindow({
  width: 1400,           // Initial width
  height: 900,           // Initial height
  minWidth: 1000,        // Minimum width
  minHeight: 700,        // Minimum height
  // ... other options
});

// Server port (must match your main.py)
const SERVER_PORT = 8000;
```

### Build Configuration

Edit `electron-app/package-windows.json` to customize:

```json
{
  "build": {
    "productName": "SET Portfolio Manager",
    "appId": "com.setportfolio.desktop",
    "win": {
      "icon": "assets/icon.ico",
      "target": ["nsis", "portable"]
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **"Python not found" error**
   - Ensure Python is installed and in PATH
   - Try running `python --version` in Command Prompt
   - Reinstall Python with "Add to PATH" option

2. **"Node.js not found" error**
   - Install Node.js from https://nodejs.org/
   - Restart Command Prompt after installation

3. **"Port already in use" error**
   - Close any running instances of your application
   - Check if port 8000 is used by another application
   - Change the port in `main-windows.js` if needed

4. **"Build failed" error**
   - Ensure all dependencies are installed
   - Check if you have write permissions in the directory
   - Try running as Administrator

### Debug Mode

Run in debug mode to see detailed logs:

```bash
cd electron-app
npm run dev
```

This will show:
- Python server startup logs
- Electron process logs
- Any error messages

### Manual Testing

1. **Test Python backend separately:**
   ```bash
   python main.py
   # Open http://localhost:8000 in browser
   ```

2. **Test Electron separately:**
   ```bash
   cd electron-app
   npm start
   # This will try to connect to existing server
   ```

## 📦 Distribution

### Creating Installer

```bash
cd electron-app
npm run build-win-installer
```

The installer will:
- Install to Program Files
- Create Start menu shortcuts
- Create desktop shortcut (optional)
- Add uninstaller

### Creating Portable Version

```bash
cd electron-app
npm run build-win-portable
```

The portable version:
- Single .exe file
- No installation required
- Can run from USB drive
- No system changes

### Distribution Files

After building, you'll find:

```
electron-app/dist-windows/
├── SET Portfolio Manager Setup.exe    # Installer
├── SET-Portfolio-Manager-Portable.exe # Portable version
└── win-unpacked/                     # Unpacked files
    └── SET Portfolio Manager.exe      # Direct executable
```

## 🔄 Updates and Maintenance

### Updating the Application

1. **Update Python code:**
   - Modify `main.py` as needed
   - No changes to Electron code required

2. **Update Electron code:**
   - Modify `electron-app/main-windows.js`
   - Rebuild the application

3. **Rebuild:**
   ```bash
   cd electron-app
   npm run build-win
   ```

### Version Management

Update version in `electron-app/package-windows.json`:

```json
{
  "version": "1.0.1",
  "build": {
    "appId": "com.setportfolio.desktop"
  }
}
```

## 🎨 Customization

### Application Icon

1. **Create icon files:**
   - Convert your logo to .ico format
   - Place in `electron-app/assets/icon.ico`

2. **Multiple sizes:**
   - 16x16, 32x32, 48x48, 256x256 pixels
   - Windows will use appropriate size

### Window Styling

Customize window appearance in `main-windows.js`:

```javascript
mainWindow = new BrowserWindow({
  // Window appearance
  titleBarStyle: 'default',     // or 'hidden', 'hiddenInset'
  frame: true,                  // false for frameless
  transparent: false,           // true for transparency
  
  // Window behavior
  resizable: true,
  maximizable: true,
  minimizable: true,
  
  // Position and size
  center: true,
  width: 1400,
  height: 900
});
```

## 📞 Support

### Getting Help

1. **Check logs:**
   - Development mode shows console logs
   - Check Windows Event Viewer for system logs

2. **Common solutions:**
   - Restart the application
   - Reinstall dependencies
   - Run as Administrator

3. **Debug mode:**
   - Press F12 to open developer tools
   - Check Console tab for errors
   - Check Network tab for API calls

### File Locations

- **Application data:** `%APPDATA%/SET Portfolio Manager/`
- **Logs:** Check Console in developer tools
- **Temporary files:** `%TEMP%/SET Portfolio Manager/`

## 🎯 Next Steps

### Potential Enhancements

1. **Auto-updates**: Implement automatic update system
2. **System tray**: Add system tray icon and menu
3. **Notifications**: Windows toast notifications
4. **File associations**: Associate with .csv files
5. **Drag & drop**: Support for file drag and drop

### Performance Optimization

1. **Code splitting**: Split large JavaScript files
2. **Lazy loading**: Load components on demand
3. **Caching**: Implement proper caching strategies
4. **Memory management**: Monitor and optimize memory usage

The Windows desktop application is now ready! You can build and distribute it as a native Windows application while keeping all your existing FastAPI logic unchanged.
