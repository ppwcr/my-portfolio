#!/usr/bin/env python3
"""
Simple script to start the auto-scraper service
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("🤖 Starting Auto-Scraper Service...")
    print("📊 This will scrape data every 10 minutes and clean up old data")
    print("🌐 The web interface will automatically refresh when new data is available")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    try:
        # Start the auto-scraper
        subprocess.run([sys.executable, "auto_scraper.py"])
    except KeyboardInterrupt:
        print("\n🛑 Auto-scraper stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
