#!/bin/bash

echo "Starting Portfolio Dashboard Server with Auto-Scraper..."
echo ""
echo "This will start:"
echo "- Web server on http://0.0.0.0:8000 (accessible from network)"
echo "- Auto-scraper that runs every 10 minutes (sector + SET index)"
echo "- Scheduled scraper that runs full updates at 10:30, 13:00, 17:30 (weekdays)"
echo "Press Ctrl+C to stop all services"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check if auto-scraper dependencies are installed
if ! python3 -c "import schedule" &> /dev/null; then
    echo "Installing auto-scraper dependencies..."
    pip3 install schedule psutil
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install auto-scraper dependencies"
        exit 1
    fi
fi

# Check if playwright is installed
echo "Checking Playwright..."
if ! command -v playwright &> /dev/null; then
    echo "Installing Playwright browsers..."
    playwright install
    if [ $? -ne 0 ]; then
        echo "Warning: Playwright installation failed, but continuing..."
    fi
fi

echo ""
echo "Starting server..."
echo ""

# Get the local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo ""
echo "========================================"
echo "Server will be accessible at:"
echo "Local:  http://127.0.0.1:8000"
echo "Network: http://$LOCAL_IP:8000"
echo ""
echo "Auto-Scraper will:"
echo "- Scrape sector and SET index data every 10 minutes"
echo "- Clean up old data automatically"
echo "- Update web interface when new data arrives"
echo ""
echo "Scheduled Scraper will:"
echo "- Run full updates (all data sources) at 10:30, 13:00, 17:30"
echo "- Weekdays only (Monday-Friday)"
echo "- Update investor, NVDR, and short sales data"
echo "========================================"
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Stopping all services..."
    pkill -f "auto_scraper.py"
    pkill -f "scheduled_scraper.py"
    pkill -f "uvicorn main:app"
    echo "All services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "Starting auto-scraper in background..."
python3 auto_scraper.py &
AUTO_SCRAPER_PID=$!

echo "Starting scheduled scraper in background..."
python3 scheduled_scraper.py &
SCHEDULED_SCRAPER_PID=$!

echo "Auto-scraper PID: $AUTO_SCRAPER_PID"
echo "Scheduled scraper PID: $SCHEDULED_SCRAPER_PID"

echo "Opening browser in 3 seconds..."
sleep 3

# Open browser (macOS)
if command -v open &> /dev/null; then
    open http://127.0.0.1:8000/portfolio
fi

# Start the server
echo "Starting web server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
