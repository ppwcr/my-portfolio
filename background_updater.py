#!/usr/bin/env python3
"""
Background Data Updater
Automatically runs Python scripts and saves data to database on server startup
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackgroundUpdater:
    def __init__(self):
        self.output_dir = Path("_out")
        self.output_dir.mkdir(exist_ok=True)
        
    async def run_script(self, script_name: str, args: list = None, timeout: int = 180) -> tuple[int, str, str]:
        """Run a Python script and return exit code, stdout, stderr"""
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
            
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            exit_code = process.returncode
            
            return exit_code, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            logger.error(f"Script {script_name} timed out after {timeout}s")
            return 1, "", "Timeout"
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
            return 1, "", str(e)
    
    async def download_fresh_data(self) -> dict:
        """Download all fresh data from SET website"""
        results = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Download NVDR data
        logger.info("📥 Downloading NVDR data...")
        nvdr_file = self.output_dir / f"nvdr_{timestamp}.xlsx"
        exit_code, stdout, stderr = await self.run_script(
            "download_nvdr_excel.py", 
            ["--out", str(nvdr_file), "--timeout", "90000"]
        )
        
        if exit_code == 0 and nvdr_file.exists():
            results["nvdr_file"] = str(nvdr_file)
            logger.info("✅ NVDR data downloaded successfully")
        else:
            logger.error(f"❌ NVDR download failed: {stderr}")
            results["nvdr_file"] = None
            
        # 2. Download Short Sales data  
        logger.info("📥 Downloading Short Sales data...")
        short_file = self.output_dir / f"short_sales_{timestamp}.xlsx"
        exit_code, stdout, stderr = await self.run_script(
            "download_short_sales_excel.py",
            ["--out", str(short_file), "--timeout", "90000"]
        )
        
        if exit_code == 0 and short_file.exists():
            results["short_sales_file"] = str(short_file)
            logger.info("✅ Short Sales data downloaded successfully")
        else:
            logger.error(f"❌ Short Sales download failed: {stderr}")
            results["short_sales_file"] = None
            
        # 3. Scrape SET investor data
        logger.info("📥 Scraping SET investor data...")
        investor_dir = self.output_dir / "investor"
        investor_dir.mkdir(exist_ok=True)
        
        table_file = investor_dir / f"investor_table_SET_{timestamp}.csv"
        json_file = investor_dir / f"investor_chart_SET_{timestamp}.json"
        
        exit_code, stdout, stderr = await self.run_script(
            "scrape_investor_data.py",
            ["--market", "SET", "--out-table", str(table_file), "--out-json", str(json_file)]
        )
        
        if exit_code == 0:
            results["investor_set"] = {"table": str(table_file), "json": str(json_file)}
            logger.info("✅ SET investor data scraped successfully")
        else:
            logger.error(f"❌ SET investor scraping failed: {stderr}")
            results["investor_set"] = None
            
        # 4. Scrape sector data (needed for portfolio stock sectors)
        logger.info("📥 Scraping sector data...")
        sectors_dir = self.output_dir / f"sectors_{timestamp}"
        exit_code, stdout, stderr = await self.run_script(
            "scrape_sector_data.py",
            ["--outdir", str(sectors_dir)]
        )
        
        if exit_code == 0 and sectors_dir.exists():
            results["sectors_dir"] = str(sectors_dir)
            logger.info("✅ Sector data scraped successfully")
        else:
            logger.error(f"❌ Sector scraping failed: {stderr}")
            results["sectors_dir"] = None
            
        return results
    
    async def save_to_database(self, data_files: dict) -> bool:
        """Save all downloaded data to database"""
        try:
            from supabase_database import get_proper_db
            import datetime as dt
            
            db = get_proper_db()
            trade_date = dt.date.today()
            success_count = 0
            total_count = 0
            
            # Save NVDR data
            if data_files.get("nvdr_file"):
                total_count += 1
                logger.info("💾 Saving NVDR data to database...")
                if db.save_nvdr_trading(data_files["nvdr_file"], trade_date):
                    success_count += 1
                    logger.info("✅ NVDR data saved to database")
                else:
                    logger.error("❌ Failed to save NVDR data to database")
            
            # Save Short Sales data
            if data_files.get("short_sales_file"):
                total_count += 1
                logger.info("💾 Saving Short Sales data to database...")
                if db.save_short_sales_trading(data_files["short_sales_file"], trade_date):
                    success_count += 1
                    logger.info("✅ Short Sales data saved to database")
                else:
                    logger.error("❌ Failed to save Short Sales data to database")
            
            # Save SET investor data
            investor_data = data_files.get("investor_set")
            if investor_data and investor_data.get("table"):
                total_count += 1
                logger.info("💾 Saving SET investor data to database...")
                if db.save_investor_summary(investor_data["table"], "SET", trade_date):
                    success_count += 1
                    logger.info("✅ SET investor data saved to database")
                else:
                    logger.error("❌ Failed to save SET investor data to database")
            
            # Save sector data (needed for portfolio stock sectors)
            if data_files.get("sectors_dir"):
                total_count += 1
                logger.info("💾 Saving sector data to database...")
                sector_success = db.save_sector_constituents(data_files["sectors_dir"], trade_date)
                if sector_success:
                    success_count += 1
                    logger.info("✅ Sector data saved to database")
                else:
                    logger.error("❌ Failed to save sector data to database")
            
            logger.info(f"📊 Database save summary: {success_count}/{total_count} successful")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
            return False
    
    async def update_all_data(self):
        """Complete data refresh process"""
        logger.info("🚀 Starting complete data refresh...")
        start_time = datetime.now()
        
        # Download fresh data
        data_files = await self.download_fresh_data()
        
        # Save to database  
        db_success = await self.save_to_database(data_files)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if db_success:
            logger.info(f"✅ Complete data refresh successful in {duration:.1f}s")
        else:
            logger.warning(f"⚠️ Partial data refresh completed in {duration:.1f}s")
        
        return db_success

# Global updater instance
updater = BackgroundUpdater()

async def startup_data_refresh():
    """Run data refresh on server startup"""
    logger.info("🌟 Server startup: Beginning data refresh...")
    await updater.update_all_data()
    
async def scheduled_data_refresh():
    """Run periodic data refresh (every 30 minutes)"""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutes
            logger.info("⏰ Scheduled refresh: Beginning data update...")
            await updater.update_all_data()
        except Exception as e:
            logger.error(f"❌ Scheduled refresh error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry