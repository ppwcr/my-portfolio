# SET Portfolio Manager - Desktop App

Desktop version of the SET (Stock Exchange of Thailand) Portfolio Management application built with Electron.

## Features

- Native desktop application
- Embedded FastAPI server (no external server needed)
- Same functionality as web version
- Offline capable
- Cross-platform (Windows, macOS, Linux)

## Development Setup

### Prerequisites

1. **Node.js** (v16 or higher)
2. **Python** (v3.8 or higher) with dependencies from parent directory
3. **All Python dependencies** from the main project

### Installation

```bash
# Navigate to electron app directory
cd electron-app

# Install Node.js dependencies
npm install

# Ensure Python dependencies are installed in parent directory
cd ..
pip install -r requirements.txt
cd electron-app
```

### Running in Development

```bash
# Start in development mode
npm run dev
```

This will:
1. Start the Python FastAPI server from parent directory
2. Open Electron window loading localhost:8000
3. Enable developer tools

### Building for Production

```bash
# Build for current platform
npm run build

# Build for specific platforms
npm run build-win    # Windows
npm run build-mac    # macOS
npm run build-linux  # Linux

# Built apps will be in dist/ directory
```

## How It Works

### Architecture

```
Electron App
├── Main Process (main.js)
│   ├── Starts Python server (../main.py)
│   ├── Creates browser window
│   └── Manages app lifecycle
├── Preload Script (preload.js)
│   └── Security bridge between main and renderer
└── Renderer Process
    └── Your FastAPI web app (localhost:8000)
```

### Key Components

1. **main.js**: Main Electron process
   - Spawns Python subprocess with your existing FastAPI app
   - Creates native window
   - Handles app lifecycle and cleanup

2. **preload.js**: Security layer
   - Provides safe APIs to renderer process
   - Prevents direct Node.js access from web content

3. **Python Backend**: Your existing FastAPI application
   - Runs as embedded subprocess
   - Same code, no modifications needed
   - Supabase integration works unchanged

## Distribution

### Packaging for Distribution

The built application includes:
- Electron runtime
- Your Python backend code
- All dependencies
- Native installers for each platform

### Requirements for End Users

- **No Python installation needed** (can be bundled)
- **No command line usage** 
- **No server management**
- Just install and run like any desktop app

## Configuration

### Environment Variables

Create `.env` file in parent directory:
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### Build Configuration

Edit `package.json` build section to customize:
- App name and identifier
- Icons and assets
- File associations
- Auto-updater settings

## For Users Without Python

If you don't have Python installed on your Mac, the app will guide you through installation:

### Option 1: Automatic Setup (Recommended)
```bash
# Run the included setup script
./setup-dependencies.sh
```

### Option 2: Manual Installation
1. **Install Python from python.org**:
   - Visit: https://www.python.org/downloads/macos/
   - Download Python 3.8+ installer
   - Run installer and follow instructions

2. **Or install via Homebrew**:
   ```bash
   # Install Homebrew (if not installed)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python
   brew install python
   ```

3. **Install Dependencies**:
   ```bash
   # Navigate to app directory and install requirements
   pip3 install -r requirements.txt
   ```

### Option 3: App Guided Installation
- When you first run the app without Python, it will show a dialog with installation options
- Choose "Install Python (Official)" or "Install Python (Homebrew)"
- Follow the instructions and restart the app

## Troubleshooting

### Python Server Won't Start
- Ensure Python is in PATH
- Check all requirements.txt dependencies are installed
- Verify .env file exists with Supabase credentials
- Try running the setup script: `./setup-dependencies.sh`

### Build Fails
- Check Node.js version (>=16)
- Ensure all npm dependencies installed
- Verify Python backend works standalone

### App Won't Load
- Check if port 8000 is available
- Look at developer console for errors
- Verify network/firewall settings

## Security Features

- Context isolation enabled
- Node integration disabled in renderer
- Web security enabled
- External links open in default browser
- No direct file system access from web content