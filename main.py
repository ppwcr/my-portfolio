#!/usr/bin/env python3
"""
SET Data Export API - FastAPI backend for the floating panel UI

This app provides endpoints to call the four Python scraping scripts:
1. download_nvdr_excel.py
2. download_short_sales_excel.py  
3. scrape_investor_data.py
4. scrape_sector_data.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import asyncio
import json

from supabase_database import get_proper_db


# Initialize FastAPI app
app = FastAPI(title="SET Data Export API", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Progress tracking
progress_data = {
    "status": "idle",
    "step": "",
    "progress": 0,
    "message": "",
    "details": {}
}

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create output directories
OUTPUT_DIR = Path("_out")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "investor").mkdir(exist_ok=True)


def ts_name(prefix: str, ext: str) -> str:
    """Generate timestamped filename like prefix_YYYYMMDD_HHMMSS.ext"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{ext}"


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, create if needed"""
    path.mkdir(parents=True, exist_ok=True)


def stderr_tail(text: str, n: int = 60) -> str:
    """Get last n lines from stderr output"""
    lines = text.split('\n')
    return '\n'.join(lines[-n:]) if len(lines) > n else text


def update_progress(status: str, step: str, progress: int, message: str, details: dict = None):
    """Update global progress data"""
    global progress_data
    progress_data.update({
        "status": status,
        "step": step,
        "progress": progress,
        "message": message,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    })


async def generate_progress_stream():
    """Generate Server-Sent Events for progress updates"""
    global progress_data
    last_data = None
    
    while True:
        if progress_data != last_data:
            yield f"data: {json.dumps(progress_data)}\n\n"
            last_data = progress_data.copy()
            
            # Stop streaming when done
            if progress_data["status"] in ["completed", "error"]:
                break
                
        await asyncio.sleep(0.5)  # Check every 500ms


async def run_cmd(cmd: list[str], timeout: int = 60) -> Tuple[int, str, str]:
    """
    Run command asynchronously with timeout
    
    Returns:
        (exit_code, stdout, stderr)
    """
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        
        return (
            proc.returncode,
            stdout.decode('utf-8', errors='replace'),
            stderr.decode('utf-8', errors='replace')
        )
        
    except asyncio.TimeoutError:
        # Kill the process if it's still running
        if proc and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        
        # Don't raise HTTPException immediately, return timeout info
        return (
            124,  # Standard timeout exit code
            "",
            f"Command timed out after {timeout} seconds: {' '.join(cmd)}"
        )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main page with floating panel UI"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/progress")
async def progress_stream():
    """Server-Sent Events endpoint for progress updates"""
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@app.get("/api/progress/status")
async def get_progress_status():
    """Get current progress status"""
    return JSONResponse(content=progress_data)


@app.get("/api/nvdr/export.xlsx")
async def export_nvdr_excel():
    """Download NVDR Excel file"""
    output_path = OUTPUT_DIR / ts_name("nvdr", "xlsx")
    
    # Build command
    cmd = [sys.executable, "download_nvdr_excel.py", "--out", str(output_path)]
    
    # Add optional flags based on environment
    if os.getenv("HEADFUL") == "1":
        cmd.append("--headful")
    if os.getenv("NO_SANDBOX") == "1":
        cmd.append("--no-sandbox")
    
    try:
        # Run the command
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)
        
        if exit_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "NVDR download failed",
                    "stderr_tail": stderr_tail(stderr),
                    "command": ' '.join(cmd)
                }
            )
        
        # Check if file exists
        if not output_path.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Output file not found",
                    "hint": "The script completed but didn't create the expected file",
                    "expected_path": str(output_path)
                }
            )
        
        # Return the file
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="nvdr_trading_by_stock.xlsx"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "stderr_tail": str(e),
                "command": ' '.join(cmd)
            }
        )


@app.get("/api/short-sales/export.xlsx")
async def export_short_sales_excel():
    """Download Short Sales Excel file"""
    output_path = OUTPUT_DIR / ts_name("short_sales", "xlsx")
    
    # Build command
    cmd = [sys.executable, "download_short_sales_excel.py", "--out", str(output_path)]
    
    # Add optional flags based on environment
    if os.getenv("HEADFUL") == "1":
        cmd.append("--headful")
    if os.getenv("NO_SANDBOX") == "1":
        cmd.append("--no-sandbox")
    
    try:
        # Run the command
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)
        
        if exit_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Short sales download failed",
                    "stderr_tail": stderr_tail(stderr),
                    "command": ' '.join(cmd)
                }
            )
        
        # Check if file exists
        if not output_path.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Output file not found",
                    "hint": "The script completed but didn't create the expected file",
                    "expected_path": str(output_path)
                }
            )
        
        # Return the file
        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="short_sales_data.xlsx"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "stderr_tail": str(e),
                "command": ' '.join(cmd)
            }
        )


@app.get("/api/investor/table.csv")
async def export_investor_table(market: str = Query("SET", pattern="^(SET|MAI)$")):
    """Export investor type table as CSV"""
    csv_path = OUTPUT_DIR / "investor" / f"investor_table_{market}_simple.csv"
    json_path = OUTPUT_DIR / "investor" / f"investor_chart_{market}_simple.json"
    
    # Build command
    cmd = [
        sys.executable, "scrape_investor_data.py",
        "--market", market,
        "--out-table", str(csv_path),
        "--out-json", str(json_path),
        "--allow-missing-chart"
    ]
    
    try:
        # Run the command
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)
        
        if exit_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Investor table scraping failed",
                    "stderr_tail": stderr_tail(stderr),
                    "command": ' '.join(cmd)
                }
            )
        
        # Check if CSV file exists
        if not csv_path.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "CSV file not found",
                    "hint": "The script completed but didn't create the expected CSV file",
                    "expected_path": str(csv_path)
                }
            )
        
        # Return the CSV file
        return FileResponse(
            path=csv_path,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="investor_table_{market}.csv"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "stderr_tail": str(e),
                "command": ' '.join(cmd)
            }
        )


@app.get("/api/investor/chart.json")
async def export_investor_chart(market: str = Query("SET", pattern="^(SET|MAI)$")):
    """Export investor type chart as JSON"""
    csv_path = OUTPUT_DIR / "investor" / f"investor_table_{market}_simple.csv"
    json_path = OUTPUT_DIR / "investor" / f"investor_chart_{market}_simple.json"
    
    # First try to get existing JSON
    if json_path.exists():
        return FileResponse(
            path=json_path,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="investor_chart_{market}.json"'}
        )
    
    # If JSON doesn't exist, run the command without --allow-missing-chart
    cmd = [
        sys.executable, "scrape_investor_data.py",
        "--market", market,
        "--out-table", str(csv_path),
        "--out-json", str(json_path)
    ]
    
    try:
        # Run the command
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)
        
        if exit_code != 0:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Chart data not found",
                    "hint": "The script failed to extract chart data",
                    "stderr_tail": stderr_tail(stderr),
                    "command": ' '.join(cmd)
                }
            )
        
        # Check if JSON file exists
        if not json_path.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "JSON file not found",
                    "hint": "The script completed but didn't create the expected JSON file",
                    "expected_path": str(json_path)
                }
            )
        
        # Return the JSON file
        return FileResponse(
            path=json_path,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="investor_chart_{market}.json"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "stderr_tail": str(e),
                "command": ' '.join(cmd)
            }
        )


@app.get("/api/sector/constituents.csv")
async def export_sector_constituents(slug: str = Query(..., pattern="^(agro|consump|fincial|indus|propcon|resourc|service|tech)$")):
    """Export sector constituents as CSV"""
    # Create unique output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = OUTPUT_DIR / f"sectors_{timestamp}"
    outdir.mkdir(exist_ok=True)
    
    # Build command
    cmd = [sys.executable, "scrape_sector_data.py", "--outdir", str(outdir)]
    
    try:
        # Run the command
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=120)  # Longer timeout for multiple sectors
        
        if exit_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Sector scraping failed",
                    "stderr_tail": stderr_tail(stderr),
                    "command": ' '.join(cmd)
                }
            )
        
        # Look for the specific sector CSV file
        csv_path = outdir / f"{slug}.constituents.csv"
        
        if not csv_path.exists():
            # List available files for debugging
            available_files = [f.name for f in outdir.glob("*.constituents.csv")]
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Sector CSV file not found for '{slug}'",
                    "hint": f"Available files: {', '.join(available_files) if available_files else 'None'}",
                    "expected_path": str(csv_path)
                }
            )
        
        # Return the CSV file
        return FileResponse(
            path=csv_path,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{slug}_constituents.csv"'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unexpected error",
                "stderr_tail": str(e),
                "command": ' '.join(cmd)
            }
        )


@app.post("/api/save-to-database")
async def save_to_database():
    """Save investor type (SET market) and all sector data to Supabase database"""
    try:
        # Initialize progress
        update_progress("starting", "Initializing", 0, "Starting database save operation...")
        
        db = get_proper_db()
        results = {"investor_data": False, "sector_data": {}, "nvdr_data": False, "short_sales_data": False}
        
        # Initialize trade_date early to avoid reference errors
        # Extract date from NVDR or Short Sales file first
        trade_date = None
        nvdr_files = list(OUTPUT_DIR.glob("nvdr_*.xlsx"))
        short_sales_files = list(OUTPUT_DIR.glob("short_sales_*.xlsx"))
        print(f"DEBUG: Found {len(nvdr_files)} NVDR files, {len(short_sales_files)} short sales files")
        
        if nvdr_files:
            try:
                trade_date = db.get_latest_trade_date_from_excel(str(nvdr_files[-1]))
            except:
                pass
        elif short_sales_files:
            try:
                trade_date = db.get_latest_trade_date_from_excel(str(short_sales_files[-1]))
            except:
                pass
        
        if trade_date is None:
            trade_date = date.today()
        
        print(f"DEBUG: Trade date: {trade_date}")
        
        # Step 1: Get investor data for SET market
        update_progress("running", "investor_scraping", 10, "Scraping investor type data (SET market)...")
        
        csv_path = OUTPUT_DIR / "investor" / "investor_table_SET_simple.csv"
        json_path = OUTPUT_DIR / "investor" / "investor_chart_SET_simple.json"
        
        cmd = [
            sys.executable, "scrape_investor_data.py",
            "--market", "SET",
            "--out-table", str(csv_path),
            "--out-json", str(json_path),
            "--allow-missing-chart"
        ]
        
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)
        
        print(f"DEBUG: Investor scraping exit_code: {exit_code}, csv_path exists: {csv_path.exists()}")
        
        if exit_code == 0 and csv_path.exists():
            update_progress("running", "investor_processing", 25, "Processing investor data...")
            
            # Read and save investor data
            investor_df = pd.read_csv(csv_path)
            print(f"DEBUG: Read {len(investor_df)} investor records")
            results["investor_data"] = db.save_investor_summary(investor_df, trade_date)
            print(f"DEBUG: Investor data save result: {results['investor_data']}")
            
            update_progress("running", "investor_saved", 30, f"✅ Saved {len(investor_df)} investor records", 
                          {"records_count": len(investor_df), "trade_date": trade_date.isoformat() if trade_date else None})
        else:
            print(f"DEBUG: Investor scraping failed - exit_code: {exit_code}, csv exists: {csv_path.exists()}")
            update_progress("running", "investor_failed", 25, "⚠️ Failed to scrape investor data")
        
        # Step 2: Get all sector data
        update_progress("running", "sector_scraping", 35, "Scraping all sector constituents...", 
                      {"note": "This usually takes 30-60 seconds - scraping 8 sectors"})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = OUTPUT_DIR / f"sectors_{timestamp}"
        outdir.mkdir(exist_ok=True)
        
        # Start with progress update during sector scraping
        update_progress("running", "sector_scraping", 40, "📡 Scraping sectors: agro, consump, fincial, indus...", 
                      {"sectors": "8 total sectors", "estimated": "30-60 seconds"})
        
        cmd = [sys.executable, "scrape_sector_data.py", "--outdir", str(outdir)]
        print(f"DEBUG: Starting sector scraping command: {' '.join(cmd)}")
        update_progress("running", "sector_scraping", 45, "🚀 Starting sector scraping command...", 
                      {"command": "scrape_sector_data.py"})
        
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=45)  # 45 seconds - much faster now
        print(f"DEBUG: Sector scraping completed. Exit code: {exit_code}")
        print(f"DEBUG: stdout: {stdout[:200]}...")
        print(f"DEBUG: stderr: {stderr[:200]}...")
        
        if exit_code == 0:
            update_progress("running", "sector_processing", 60, "Processing sector data files...")
            
            # Process each sector CSV file
            sector_files = list(outdir.glob("*.constituents.csv"))
            total_sectors = len(sector_files)
        else:
            # If sector scraping failed/timed out, try to use the most recent complete sector data
            update_progress("running", "sector_fallback", 60, "Sector scraping timed out - using latest available data...")
            
            # Find the most recent complete sector directory
            all_sector_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith("sectors_")]
            complete_dirs = []
            
            for sector_dir in all_sector_dirs:
                sector_files_in_dir = list(sector_dir.glob("*.constituents.csv"))
                if len(sector_files_in_dir) >= 8:  # Complete set has all 8 sectors
                    complete_dirs.append((sector_dir, sector_files_in_dir))
            
            if complete_dirs:
                # Use the most recent complete directory
                complete_dirs.sort(key=lambda x: x[0].name)
                outdir, sector_files = complete_dirs[-1]
                total_sectors = len(sector_files)
                update_progress("running", "sector_processing", 60, f"Using complete sector data from {outdir.name}...")
                print(f"DEBUG: Using fallback sector data from {outdir} with {total_sectors} sectors")
            else:
                update_progress("running", "sector_failed", 60, "⚠️ No complete sector data available")
                sector_files = []
                total_sectors = 0
        
        # Process sector files (whether from new scraping or fallback)
        if sector_files:
            for i, sector_file in enumerate(sector_files):
                sector_name = sector_file.stem.replace('.constituents', '')
                progress_pct = 60 + (i / total_sectors) * 30  # 60-90% range
                
                update_progress("running", "sector_processing", int(progress_pct), 
                              f"Saving {sector_name} sector data...", {"current_sector": sector_name})
                
                try:
                    sector_df = pd.read_csv(sector_file)
                    success = db.save_sector_data(sector_df, sector_name, trade_date)
                    results["sector_data"][sector_name] = success
                    
                    if success:
                        update_progress("running", "sector_processing", int(progress_pct), 
                                      f"✅ Saved {len(sector_df)} records for {sector_name}", 
                                      {"current_sector": sector_name, "records_count": len(sector_df)})
                    else:
                        update_progress("running", "sector_processing", int(progress_pct), 
                                      f"⚠️ Failed to save {sector_name}", {"current_sector": sector_name})
                        
                except Exception as e:
                    print(f"Error processing sector {sector_name}: {e}")
                    results["sector_data"][sector_name] = False
                    update_progress("running", "sector_processing", int(progress_pct), 
                                  f"❌ Error with {sector_name}: {str(e)[:50]}...", {"current_sector": sector_name})
        
        # Step 3: Save NVDR data
        update_progress("running", "nvdr_processing", 90, "Saving NVDR data...")
        nvdr_files = list(OUTPUT_DIR.glob("nvdr_*.xlsx"))
        if nvdr_files:
            latest_nvdr = nvdr_files[-1]  # Get most recent file
            print(f"DEBUG: Processing NVDR file: {latest_nvdr}")
            results["nvdr_data"] = db.save_nvdr_trading(str(latest_nvdr), trade_date)
            if results["nvdr_data"]:
                update_progress("running", "nvdr_saved", 93, "✅ NVDR data saved successfully!")
            else:
                update_progress("running", "nvdr_failed", 93, "⚠️ Failed to save NVDR data")
        else:
            update_progress("running", "nvdr_skipped", 93, "⚠️ No NVDR files found")
        
        # Step 4: Save Short Sales data
        update_progress("running", "shortsales_processing", 95, "Saving Short Sales data...")
        short_files = list(OUTPUT_DIR.glob("short_sales_*.xlsx"))
        if short_files:
            latest_short = short_files[-1]  # Get most recent file
            print(f"DEBUG: Processing Short Sales file: {latest_short}")
            results["short_sales_data"] = db.save_short_sales_trading(str(latest_short), trade_date)
            if results["short_sales_data"]:
                update_progress("running", "shortsales_saved", 98, "✅ Short Sales data saved successfully!")
            else:
                update_progress("running", "shortsales_failed", 98, "⚠️ Failed to save Short Sales data")
        else:
            update_progress("running", "shortsales_skipped", 98, "⚠️ No Short Sales files found")
        
        # Final results
        sector_success = all(results["sector_data"].values()) if results["sector_data"] else False
        total_success = results["investor_data"] and sector_success and results["nvdr_data"] and results["short_sales_data"]
        
        if total_success:
            update_progress("completed", "success", 100, "🎉 All data saved successfully!", 
                          {"total_sectors": len(results["sector_data"]), "trade_date": trade_date.isoformat() if trade_date else None})
        else:
            success_count = sum([
                1 if results["investor_data"] else 0,
                len([v for v in results["sector_data"].values() if v]) if results["sector_data"] else 0,
                1 if results["nvdr_data"] else 0,
                1 if results["short_sales_data"] else 0
            ])
            total_count = 1 + len(results["sector_data"]) + 2  # investor + sectors + nvdr + short_sales
            update_progress("completed", "partial", 100, f"⚠️ Partial success - {success_count}/{total_count} datasets saved", 
                          {"details": results})
        
        return JSONResponse(
            status_code=200 if total_success else 207,
            content={
                "success": total_success,
                "message": "Data saved to database" if total_success else "Partial success",
                "details": results,
                "trade_date": trade_date.isoformat() if trade_date else None
            }
        )
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database save failed",
                "message": str(e)
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
