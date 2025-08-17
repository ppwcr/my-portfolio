#!/usr/bin/env python3
"""
Utility to get SET market timestamp for use by all scrapers
"""

import json
from pathlib import Path
from datetime import datetime
import subprocess
import sys

def get_set_timestamp():
    """Get the latest SET market timestamp"""
    try:
        # First try to get from existing SET index data
        latest_file = Path("_out/set_index_latest.json")
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('success') and data.get('set_datetime'):
                    return datetime.fromisoformat(data['set_datetime'].replace('Z', '+00:00'))
        
        # If no existing data, scrape fresh SET index data
        print("📊 Fetching fresh SET timestamp...")
        result = subprocess.run(
            [sys.executable, "scrape_set_index.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('success') and data.get('set_datetime'):
                    return datetime.fromisoformat(data['set_datetime'].replace('Z', '+00:00'))
        
        # Fallback to current time
        print("⚠️ Could not get SET timestamp, using current time")
        return datetime.now()
        
    except Exception as e:
        print(f"⚠️ Error getting SET timestamp: {e}, using current time")
        return datetime.now()

def get_set_trade_date():
    """Get the SET trade date (date only) for database storage"""
    return get_set_timestamp().date()

if __name__ == "__main__":
    timestamp = get_set_timestamp()
    print(f"SET Timestamp: {timestamp}")
    print(f"SET Trade Date: {get_set_trade_date()}")