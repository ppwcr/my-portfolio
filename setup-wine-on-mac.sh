#!/bin/bash

# SET Portfolio Manager - Wine Setup Script for Mac
# Install Wine for cross-platform Windows builds

echo "========================================"
echo "SET Portfolio Manager - Wine Setup"
echo "Installing Wine for Windows builds on Mac"
echo "========================================"
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ ERROR: Homebrew is not installed!"
    echo ""
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: Failed to install Homebrew!"
        exit 1
    fi
    
    echo "✓ Homebrew installed successfully!"
    echo ""
    
    # Add Homebrew to PATH for current session
    if [[ $(uname -m) == 'arm64' ]]; then
        # Apple Silicon Mac
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        # Intel Mac
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

echo "✓ Homebrew is available: $(brew --version | head -1)"
echo ""

# Check if Wine is already installed
if command -v wine &> /dev/null; then
    echo "✓ Wine is already installed: $(wine --version)"
    echo ""
    echo "Wine setup is complete! You can now build Windows applications."
    exit 0
fi

echo "📦 Installing Wine..."
echo "This may take several minutes..."

# Install Wine
brew install --cask wine-stable

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to install Wine!"
    echo ""
    echo "Alternative installation methods:"
    echo "1. Download from: https://www.winehq.org/download/macosx"
    echo "2. Or try: brew install --cask wine-devel"
    exit 1
fi

echo "✓ Wine installed successfully!"
echo ""

# Verify Wine installation
if command -v wine &> /dev/null; then
    echo "✓ Wine is available: $(wine --version)"
    echo ""
    echo "🎉 Wine setup completed successfully!"
    echo ""
    echo "You can now build Windows applications on Mac using:"
    echo "  ./build-windows-on-mac.sh"
    echo ""
else
    echo "❌ ERROR: Wine installation verification failed!"
    echo "Please try restarting your terminal and running this script again."
    exit 1
fi

# Optional: Install additional Wine components
echo "🔧 Installing additional Wine components..."
echo "This will improve Windows application compatibility..."

# Install winetricks if available
if command -v winetricks &> /dev/null; then
    echo "✓ Winetricks is available"
else
    echo "Installing winetricks..."
    brew install winetricks
fi

echo ""
echo "📋 Wine setup summary:"
echo "   ✓ Homebrew installed"
echo "   ✓ Wine installed"
echo "   ✓ Winetricks installed (if available)"
echo ""
echo "🚀 Ready for cross-platform builds!"
