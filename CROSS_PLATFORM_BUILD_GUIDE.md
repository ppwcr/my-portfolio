# Cross-Platform Build Guide - Windows on Mac

This guide explains how to build Windows desktop applications on Mac using Electron's cross-platform compilation capabilities.

## 🍎 **Build Windows Apps on Mac** ✅

### **What You Get:**

- **Windows .exe files** built on Mac
- **Portable executables** that run on any Windows machine
- **Professional installers** with Start menu integration
- **No Windows machine needed** for development
- **Single build process** for multiple platforms

## 📋 **Prerequisites**

### **Required Software on Mac:**

1. **Node.js** (v16 or higher)
   ```bash
   # Install via Homebrew
   brew install node
   
   # Or download from https://nodejs.org/
   ```

2. **Homebrew** (for Wine installation)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **Wine** (for Windows compatibility)
   ```bash
   # Use our setup script
   ./setup-wine-on-mac.sh
   
   # Or install manually
   brew install --cask wine-stable
   ```

4. **Python** (for your backend)
   ```bash
   brew install python
   ```

## 🚀 **Quick Start**

### **Step 1: Setup Wine (One-time setup)**

```bash
# Run the Wine setup script
./setup-wine-on-mac.sh
```

This will:
- Install Homebrew (if needed)
- Install Wine for Windows compatibility
- Install winetricks for additional components
- Verify the installation

### **Step 2: Build Windows Applications**

```bash
# Run the cross-platform build script
./build-windows-on-mac.sh
```

Choose your build type:
1. **Windows Portable** (.exe) - Single file, no installation
2. **Windows Installer** (.exe) - Professional installer
3. **Both Windows versions** - Portable + Installer
4. **All platforms** - Windows + Mac versions

### **Step 3: Distribute to Windows**

After building, you'll find:
```
electron-app/dist-cross-platform/
├── SET-Portfolio-Manager-Portable.exe    # Portable version
├── SET Portfolio Manager Setup.exe       # Installer
└── win-unpacked/                        # Unpacked files
```

## 🛠️ **Manual Build Process**

### **Step 1: Install Dependencies**

```bash
cd electron-app
npm install
```

### **Step 2: Use Cross-Platform Package**

```bash
# Copy the cross-platform configuration
cp package-cross-platform.json package.json

# Or use it directly
npm run build-win -- --config package-cross-platform.json
```

### **Step 3: Build Specific Targets**

```bash
# Build Windows portable
npm run build-win-portable

# Build Windows installer
npm run build-win-installer

# Build both Windows versions
npm run build-win

# Build all platforms
npm run build-win-on-mac
```

## 📁 **File Structure**

```
my-portfolio/
├── electron-app/
│   ├── main-windows.js              # Windows-specific main process
│   ├── package-cross-platform.json  # Cross-platform build config
│   ├── package-windows.json         # Windows-only config
│   ├── assets/
│   │   ├── icon.ico                # Windows icon
│   │   ├── icon.icns               # Mac icon
│   │   └── icon.svg                # Source icon
│   └── dist-cross-platform/        # Build output
├── main.py                         # Your FastAPI app (unchanged)
├── build-windows-on-mac.sh         # Cross-platform build script
├── setup-wine-on-mac.sh            # Wine setup script
└── CROSS_PLATFORM_BUILD_GUIDE.md   # This guide
```

## 🎯 **Build Options**

### **Windows Portable (.exe)**
- **Single file** - No installation required
- **USB ready** - Can run from USB drive
- **No system changes** - Doesn't modify Windows registry
- **Easy distribution** - Just copy the .exe file

### **Windows Installer (.exe)**
- **Professional installation** - Installs to Program Files
- **Start menu integration** - Creates Start menu shortcuts
- **Desktop shortcut** - Optional desktop icon
- **Uninstaller** - Proper uninstallation support

### **Cross-Platform Build**
- **Multiple targets** - Build for Windows and Mac simultaneously
- **Optimized** - Each platform gets optimized binaries
- **Consistent** - Same codebase, multiple platforms

## 🔧 **Configuration**

### **Cross-Platform Package Configuration**

The `package-cross-platform.json` includes:

```json
{
  "build": {
    "win": {
      "target": ["nsis", "portable"],
      "arch": ["x64"]
    },
    "mac": {
      "target": ["dmg", "zip"],
      "arch": ["x64", "arm64"]
    }
  }
}
```

### **Customizing Builds**

Edit `electron-app/package-cross-platform.json`:

```json
{
  "build": {
    "productName": "Your App Name",
    "appId": "com.yourcompany.yourapp",
    "win": {
      "icon": "assets/your-icon.ico",
      "publisherName": "Your Company"
    }
  }
}
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **"Wine not found" error**
   ```bash
   # Install Wine
   ./setup-wine-on-mac.sh
   
   # Or manually
   brew install --cask wine-stable
   ```

2. **"Homebrew not found" error**
   ```bash
   # Install Homebrew
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. **"Build failed" error**
   ```bash
   # Check dependencies
   cd electron-app
   npm install
   
   # Try building with verbose output
   npm run build-win -- --verbose
   ```

4. **"Python not found" error**
   ```bash
   # Install Python
   brew install python
   
   # Install Python dependencies
   pip install -r requirements.txt
   ```

### **Wine Issues**

1. **Wine installation problems**
   ```bash
   # Try alternative Wine version
   brew install --cask wine-devel
   
   # Or download from Wine website
   # https://www.winehq.org/download/macosx
   ```

2. **Wine configuration**
   ```bash
   # Configure Wine
   winecfg
   
   # Install Windows components
   winetricks vcrun2019
   ```

### **Build Performance**

1. **Slow builds**
   ```bash
   # Use parallel builds
   npm run build-win -- --parallel
   
   # Skip unnecessary targets
   npm run build-win-portable
   ```

2. **Large file sizes**
   ```bash
   # Enable compression
   # Already enabled in package.json
   # "compression": "maximum"
   ```

## 📦 **Distribution**

### **Creating Distribution Packages**

```bash
# Build all versions
./build-windows-on-mac.sh

# Create distribution folder
mkdir -p distribution/windows
cp electron-app/dist-cross-platform/*.exe distribution/windows/

# Create README for Windows users
cat > distribution/windows/README.txt << EOF
SET Portfolio Manager for Windows

1. SET-Portfolio-Manager-Portable.exe - Run without installation
2. SET Portfolio Manager Setup.exe - Install to your computer

System Requirements:
- Windows 10 or later
- Python 3.8+ (will be bundled)
- 4GB RAM minimum
- 500MB disk space

Installation:
1. For portable: Just run the .exe file
2. For installer: Run Setup.exe and follow instructions
EOF
```

### **Testing on Windows**

1. **Transfer files to Windows machine**
   - Use USB drive, cloud storage, or network
   - Copy the .exe files

2. **Test portable version**
   - Double-click the portable .exe
   - Should run without installation

3. **Test installer**
   - Run the Setup.exe
   - Follow installation wizard
   - Check Start menu and desktop shortcuts

## 🔄 **Continuous Integration**

### **Automated Builds**

Create a GitHub Actions workflow:

```yaml
# .github/workflows/build.yml
name: Build Windows App

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd electron-app
        npm install
    
    - name: Build Windows app
      run: |
        cd electron-app
        npm run build-win
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: windows-app
        path: electron-app/dist-cross-platform/
```

## 🎨 **Customization**

### **Application Icons**

1. **Create Windows icon (.ico)**
   ```bash
   # Convert from SVG or PNG
   # Use online tools or ImageMagick
   convert icon.svg -resize 256x256 icon.ico
   ```

2. **Create Mac icon (.icns)**
   ```bash
   # Convert from SVG or PNG
   # Use online tools or iconutil
   ```

### **Build Configuration**

Customize `electron-app/package-cross-platform.json`:

```json
{
  "build": {
    "productName": "Your Custom App Name",
    "appId": "com.yourcompany.yourapp",
    "directories": {
      "output": "dist-custom"
    },
    "files": [
      "main-windows.js",
      "preload.js",
      "assets/**/*"
    ]
  }
}
```

## 📞 **Support**

### **Getting Help**

1. **Check build logs**
   ```bash
   cd electron-app
   npm run build-win -- --verbose
   ```

2. **Verify Wine installation**
   ```bash
   wine --version
   winetricks --version
   ```

3. **Test Wine functionality**
   ```bash
   wine notepad
   ```

### **Common Solutions**

1. **Restart terminal** after installing Wine
2. **Update Homebrew** before installing Wine
3. **Clear npm cache** if builds fail
4. **Check disk space** for large builds

## 🎯 **Next Steps**

### **Advanced Features**

1. **Code signing** for Windows
2. **Auto-updates** system
3. **Multi-language** support
4. **Custom installers** with branding

### **Performance Optimization**

1. **Reduce bundle size**
2. **Optimize startup time**
3. **Memory usage** optimization
4. **Build time** reduction

The cross-platform build system is now ready! You can build professional Windows applications on your Mac and distribute them to Windows users without needing a Windows machine. 🚀
