#!/bin/bash
# Setup script for SET Portfolio Manager dependencies

echo "🏗️  SET Portfolio Manager - Dependency Setup"
echo "============================================="
echo

# Check if Python is installed
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 is already installed: $(python3 --version)"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ Python is already installed: $(python --version)"
    PYTHON_CMD="python"
else
    echo "❌ Python is not installed"
    echo
    echo "📥 Installing Python..."
    
    # Check if Homebrew is available
    if command -v brew &> /dev/null; then
        echo "🍺 Installing Python via Homebrew..."
        brew install python
    else
        echo "⚠️  Homebrew not found. Please install Python manually:"
        echo "   1. Download from: https://www.python.org/downloads/macos/"
        echo "   2. Or install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "   3. Then run: brew install python"
        exit 1
    fi
    
    PYTHON_CMD="python3"
fi

echo
echo "📦 Installing Python dependencies..."

# Navigate to the Python backend directory
if [ -d "Resources/python-backend" ]; then
    cd Resources/python-backend
elif [ -d "../" ]; then
    cd ../
else
    echo "❌ Could not find Python backend directory"
    exit 1
fi

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    $PYTHON_CMD -m pip install -r requirements.txt
else
    echo "❌ requirements.txt not found"
    exit 1
fi

echo
echo "✅ Setup complete!"
echo "🚀 You can now run the SET Portfolio Manager application."
echo