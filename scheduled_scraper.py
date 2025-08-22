#!/usr/bin/env python3
"""
Scheduled scraper that runs full updates at specific times on weekdays
Runs alongside the auto_scraper.py for comprehensive data coverage
"""

import time
import schedule
import subprocess
import sys
import os
from datetime import datetime, date
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduled_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_weekday():
    """Check if today is a weekday (Monday=0, Sunday=6)"""
    return datetime.now().weekday() < 5

def run_full_scraping():
    """Run full scraping of all data sources"""
    if not is_weekday():
        logger.info("📅 Weekend detected - skipping scheduled full update")
        return
    
    logger.info("🚀 Starting scheduled full scraping (all data sources)...")
    
    # Run all scraping scripts with --save-db flag
    scripts = [
        ("scrape_investor_data.py", ["--save-db"]),
        ("scrape_sector_data.py", ["--save-db"]),
        ("scrape_set_index.py", ["--save-db"]),
        ("download_nvdr_excel.py", ["--save-db"]),
        ("download_short_sales_excel.py", ["--save-db"])
    ]
    
    success_count = 0
    total_scripts = len(scripts)
    
    for script_name, args in scripts:
        try:
            cmd = [sys.executable, script_name]
            if args:
                cmd.extend(args)
            
            logger.info(f"🔄 Running {script_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ {script_name} completed successfully")
                success_count += 1
            else:
                logger.error(f"❌ {script_name} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {script_name} timed out after 5 minutes")
        except Exception as e:
            logger.error(f"💥 {script_name} error: {e}")
    
    logger.info(f"📊 Scheduled full scraping completed: {success_count}/{total_scripts} scripts successful")
    
    # Trigger web page refresh notification
    trigger_web_refresh()

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
    """Main function to run the scheduled scraper"""
    logger.info("📅 Scheduled Scraper starting...")
    logger.info("⏰ Will run full updates at 10:30, 13:00, 17:30 on weekdays")
    
    # Schedule full scraping at specific times (weekdays only)
    schedule.every().monday.at("10:30").do(run_full_scraping)
    schedule.every().monday.at("13:00").do(run_full_scraping)
    schedule.every().monday.at("17:30").do(run_full_scraping)
    
    schedule.every().tuesday.at("10:30").do(run_full_scraping)
    schedule.every().tuesday.at("13:00").do(run_full_scraping)
    schedule.every().tuesday.at("17:30").do(run_full_scraping)
    
    schedule.every().wednesday.at("10:30").do(run_full_scraping)
    schedule.every().wednesday.at("13:00").do(run_full_scraping)
    schedule.every().wednesday.at("17:30").do(run_full_scraping)
    
    schedule.every().thursday.at("10:30").do(run_full_scraping)
    schedule.every().thursday.at("13:00").do(run_full_scraping)
    schedule.every().thursday.at("17:30").do(run_full_scraping)
    
    schedule.every().friday.at("10:30").do(run_full_scraping)
    schedule.every().friday.at("13:00").do(run_full_scraping)
    schedule.every().friday.at("17:30").do(run_full_scraping)
    
    # Run initial full scrape if it's a weekday and before 10:30
    current_time = datetime.now().time()
    if is_weekday() and current_time < datetime.strptime("10:30", "%H:%M").time():
        logger.info("🔄 Running initial full scrape (weekday before 10:30)...")
        run_full_scraping()
    
    # Keep running and checking schedule
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("🛑 Scheduled scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"💥 Scheduled scraper error: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
