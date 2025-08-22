#!/usr/bin/env python3
"""
Auto-scraper that runs every 10 minutes to keep data fresh
Saves only the latest data for each date to optimize database space
"""

import time
import schedule
import subprocess
import sys
import os
from datetime import datetime, date, timedelta
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_scraping_script(script_name: str, args: list = None) -> bool:
    """Run a scraping script and return success status"""
    try:
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        logger.info(f"🔄 Running {script_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"✅ {script_name} completed successfully")
            return True
        else:
            logger.error(f"❌ {script_name} failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {script_name} timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"💥 {script_name} error: {e}")
        return False

def cleanup_old_data():
    """Clean up old data to keep only latest data for each date"""
    try:
        logger.info("🧹 Cleaning up old data...")
        
        # Import database manager
        from supabase_database import ProperDatabaseManager
        db = ProperDatabaseManager()
        
        # Get current date
        today = date.today()
        
        # Clean up old data for core market data tables
        # Focus on tables that are updated by the auto-scraper
        tables_to_clean = [
            'sector_data',
            'set_index'
        ]
        
        for table in tables_to_clean:
            try:
                # Keep only data from today and yesterday
                cutoff_date = (today - timedelta(days=2)).isoformat()
                
                # Delete old records
                result = db.client.table(table).delete().lt('trade_date', cutoff_date).execute()
                deleted_count = len(result.data) if result.data else 0
                
                if deleted_count > 0:
                    logger.info(f"🗑️  Deleted {deleted_count} old records from {table}")
                    
            except Exception as e:
                logger.error(f"❌ Error cleaning {table}: {e}")
        
        logger.info("✅ Data cleanup completed")
        
    except Exception as e:
        logger.error(f"💥 Error in cleanup: {e}")

def auto_scrape():
    """Main auto-scraping function - focuses on core market data (sector and SET index)"""
    logger.info("🚀 Starting auto-scrape cycle for core market data...")
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run core market data scraping scripts with --save-db flag
    # Focus on sector and SET index data that change frequently during trading hours
    scripts = [
        ("scrape_sector_data.py", ["--save-db"]),
        ("scrape_set_index.py", ["--save-db"])
    ]
    
    success_count = 0
    total_scripts = len(scripts)
    
    for script_name, args in scripts:
        if run_scraping_script(script_name, args):
            success_count += 1
    
    # Clean up old data
    cleanup_old_data()
    
    logger.info(f"📊 Auto-scrape completed: {success_count}/{total_scripts} core market data scripts successful")
    
    # Trigger web page refresh notification
    trigger_web_refresh()
    
    return success_count == total_scripts

def trigger_web_refresh():
    """Trigger web page refresh by updating a notification file"""
    try:
        # Create a notification file that the web app can watch
        notification_file = Path("data_update_notification.txt")
        with open(notification_file, "w") as f:
            f.write(f"Data updated at {datetime.now().isoformat()}")
        
        logger.info("🔔 Web refresh notification sent")
        
    except Exception as e:
        logger.error(f"❌ Error sending web refresh notification: {e}")

def main():
    """Main function to run the auto-scraper"""
    logger.info("🤖 Auto-scraper starting...")
    
    # Schedule auto-scrape every 10 minutes
    schedule.every(10).minutes.do(auto_scrape)
    
    # Run initial scrape
    logger.info("🔄 Running initial scrape...")
    auto_scrape()
    
    # Keep running and checking schedule
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("🛑 Auto-scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"💥 Auto-scraper error: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
