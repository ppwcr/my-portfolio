#!/bin/bash

# SET Portfolio Manager - Cross Platform Build Script
# Build Windows applications on Mac

echo "========================================"
echo "SET Portfolio Manager - Cross Platform Build"
echo "Building Windows applications on Mac"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm is not available!"
    exit 1
fi

echo "✓ Node.js is available: $(node --version)"
echo "✓ npm is available: $(npm --version)"
echo ""

# Navigate to electron-app directory
cd electron-app

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ ERROR: package.json not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

echo "📁 Working directory: $(pwd)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install dependencies!"
    exit 1
fi

echo "✓ Dependencies installed successfully!"
echo ""

# Check if Wine is available for Windows builds
if ! command -v wine &> /dev/null; then
    echo "⚠️  WARNING: Wine is not installed!"
    echo "Wine is required for building Windows applications on Mac."
    echo ""
    echo "Installing Wine..."
    
    # Try to install Wine using Homebrew
    if command -v brew &> /dev/null; then
        echo "Installing Wine via Homebrew..."
        brew install --cask wine-stable
    else
        echo "❌ ERROR: Homebrew not found!"
        echo "Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
        echo "Then install Wine:"
        echo "  brew install --cask wine-stable"
        exit 1
    fi
fi

echo "✓ Wine is available: $(wine --version)"
echo ""

# Ask user for build type
echo "Choose build type:"
echo "1. Windows Portable (.exe)"
echo "2. Windows Installer (.exe)"
echo "3. Both Windows versions"
echo "4. All platforms (Windows + Mac)"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Building Windows portable executable..."
        npm run build-win-portable
        ;;
    2)
        echo ""
        echo "🔨 Building Windows installer..."
        npm run build-win-installer
        ;;
    3)
        echo ""
        echo "🔨 Building both Windows versions..."
        npm run build-win
        ;;
    4)
        echo ""
        echo "🔨 Building all platforms..."
        npm run build-win-on-mac
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Build failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""

# Show output files
dist_path="dist-cross-platform"
if [ -d "$dist_path" ]; then
    echo "📁 Output files are in: $dist_path"
    echo ""
    echo "📋 Output files:"
    ls -la "$dist_path"
    echo ""
    
    # Show file sizes
    echo "📊 File sizes:"
    du -h "$dist_path"/*
    echo ""
fi

echo "🎉 Build completed! You can now:"
echo "   1. Copy the .exe files to Windows machines"
echo "   2. Distribute the installer to Windows users"
echo "   3. Test the portable version on Windows"
echo ""

# Optional: Create a distribution package
echo "📦 Creating distribution package..."
cd "$dist_path"
if [ -f "SET-Portfolio-Manager-Portable.exe" ]; then
    echo "   ✓ Portable executable ready"
fi
if [ -f "SET Portfolio Manager Setup.exe" ]; then
    echo "   ✓ Installer ready"
fi

echo ""
echo "🚀 Ready for Windows distribution!"
