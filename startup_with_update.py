#!/usr/bin/env python3
"""
Portfolio Dashboard Startup Script with Database Update
Runs database update on startup, then starts the FastAPI server.
"""
import asyncio
import subprocess
import sys
import time
import webbrowser
import threading
from pathlib import Path

# Import our database functions
try:
    from supabase_database import get_proper_db
    from scrape_investor_data import main as scrape_investor
    from scrape_sector_data import main as scrape_sectors
except ImportError as e:
    print(f"Warning: Could not import scraping modules: {e}")
    print("Server will start but database update may not work properly")

def print_banner():
    print("=" * 60)
    print("🚀 PORTFOLIO DASHBOARD STARTUP")
    print("=" * 60)
    print()
    
def update_database():
    """Update database with fresh market data"""
    print("⏳ Updating database with fresh market data...")
    print("This may take 1-2 minutes...")
    print()
    
    try:
        # Test database connection
        print("📡 Testing database connection...")
        db = get_proper_db()
        print("✅ Database connection successful")
        
        # Update investor data (fastest)
        print("📊 Updating investor data...")
        try:
            # Run investor scraper for both SET and MAI
            subprocess.run([sys.executable, "scrape_investor_data.py", "--market", "SET"], 
                         check=True, timeout=60)
            subprocess.run([sys.executable, "scrape_investor_data.py", "--market", "MAI"], 
                         check=True, timeout=60)
            print("✅ Investor data updated")
        except Exception as e:
            print(f"⚠️  Investor data update failed: {e}")
        
        # Update sector data
        print("🏢 Updating sector data...")
        try:
            subprocess.run([sys.executable, "scrape_sector_data.py"], 
                         check=True, timeout=90)
            print("✅ Sector data updated")
        except Exception as e:
            print(f"⚠️  Sector data update failed: {e}")
            
        print()
        print("✅ Database update completed!")
        print("📊 Fresh market data is now available")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        print("⚠️  Server will still start, data will auto-update in background")
    
    print()

def open_browser_delayed():
    """Open browser after a delay"""
    time.sleep(8)  # Wait for server to fully start
    try:
        webbrowser.open('http://127.0.0.1:8000/portfolio')
        print("🌐 Browser opened at http://127.0.0.1:8000/portfolio")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please manually visit: http://127.0.0.1:8000/portfolio")

def main():
    print_banner()
    
    # Update database first
    update_database()
    
    # Start browser in background thread
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # Start the FastAPI server
    print("🚀 Starting Portfolio Dashboard server...")
    print("📡 Server will be available at: http://127.0.0.1:8000/portfolio")
    print()
    print("💡 The database will auto-update only when PC starts up")
    print("🔄 Press Ctrl+C to stop the server")
    print()
    print("-" * 60)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()