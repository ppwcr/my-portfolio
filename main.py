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
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from supabase_database import get_proper_db
import requests
try:
    import yfinance as yf
    HAS_YF = True
except Exception:
    HAS_YF = False

# Removed cache system to avoid data mixing issues

# Simple lock for serializing yfinance requests to prevent concurrent access issues
import threading
yfinance_lock = threading.Lock()


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


@app.get("/")
async def index():
    """Redirect root to the portfolio dashboard (panel deprecated)."""
    return RedirectResponse(url="/portfolio", status_code=307)


@app.get("/api/series/set-index")
def get_set_index_series():
    """Return SET index daily series and latest summary from Stooq CSV.

    Response:
      {
        "series": [{"time": "YYYY-MM-DD", "value": float}, ...],
        "latest": {
            "date": "YYYY-MM-DD",
            "open": float, "high": float, "low": float, "close": float, "volume": int,
            "change": float, "change_percent": float
        }
      }
    """
    try:
        df = None
        if HAS_YF:
            # Yahoo Finance index for SET
            df = yf.download("^SET.BK", period="max", interval="1d", progress=False)
            # Handle MultiIndex columns from yfinance
            if df is not None and not df.empty:
                # Reset index to make Date a column
                df = df.reset_index()
                # Flatten MultiIndex columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    # Create new column names by joining the levels
                    new_columns = []
                    for col in df.columns:
                        if col[0] == 'Date':
                            new_columns.append('Date')
                        else:
                            new_columns.append(col[0])  # Use the first level (Price type)
                    df.columns = new_columns
        if df is None or df.empty:
            # Fallback: Stooq (with SSL verification disabled for macOS compatibility)
            try:
                url = "https://stooq.com/q/d/l/?s=%5Eset&i=d"
                df = pd.read_csv(url, parse_dates=["Date"])  # Date, Open, High, Low, Close, Volume
            except Exception as stooq_error:
                print(f"Stooq fallback failed: {stooq_error}")
                # If both sources fail, return error
                return JSONResponse(status_code=502, content={"error": "No data from source", "message": f"Yahoo Finance and Stooq both failed: {stooq_error}"})

        df = df.dropna(subset=["Close"]).sort_values("Date")
        if df.empty:
            return JSONResponse(status_code=502, content={"error": "No data from source"})

        # Verify this is actually SET index data (should be around 1200-1400 range)
        latest_close = float(df.iloc[-1]["Close"])
        if latest_close < 500 or latest_close > 2000:
            print(f"⚠️  Suspicious SET index value: {latest_close}, this might be wrong data")
            # Try to get fresh data by clearing any potential cache
            if HAS_YF:
                try:
                    import yfinance as yf_module
                    yf_module.cache.clear()
                    yf_module.session.cache.clear()
                    yf_module.session.close()
                    yf_module.session = None
                    time.sleep(0.5)
                    
                    print("🔄 Retrying SET index with fresh session...")
                    df = yf.download("^SET.BK", period="max", interval="1d", progress=False)
                    if df is not None and not df.empty:
                        df = df.reset_index()
                        if isinstance(df.columns, pd.MultiIndex):
                            new_columns = []
                            for col in df.columns:
                                if col[0] == 'Date':
                                    new_columns.append('Date')
                                else:
                                    new_columns.append(col[0])
                            df.columns = new_columns
                        df = df.dropna(subset=["Close"]).sort_values("Date")
                        latest_close = float(df.iloc[-1]["Close"])
                        print(f"🔄 Retry result: {latest_close}")
                except Exception as retry_error:
                    print(f"⚠️  SET index retry failed: {retry_error}")

        series = [
            {"time": d.strftime("%Y-%m-%d"), "value": float(c)}
            for d, c in zip(df["Date"], df["Close"]) if pd.notna(c)
        ]

        latest_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) >= 2 else None
        close = float(latest_row["Close"]) if pd.notna(latest_row.get("Close")) else None
        prev_close = float(prev_row["Close"]) if (prev_row is not None and pd.notna(prev_row.get("Close"))) else None
        change = (close - prev_close) if (close is not None and prev_close is not None) else 0.0
        change_pct = (change / prev_close * 100.0) if (prev_close not in (None, 0)) else 0.0

        latest = {
            "date": latest_row["Date"].strftime("%Y-%m-%d") if isinstance(latest_row["Date"], (pd.Timestamp,)) else str(latest_row["Date"]),
            "open": float(latest_row.get("Open")) if pd.notna(latest_row.get("Open")) else None,
            "high": float(latest_row.get("High")) if pd.notna(latest_row.get("High")) else None,
            "low": float(latest_row.get("Low")) if pd.notna(latest_row.get("Low")) else None,
            "close": close,
            "volume": int(latest_row.get("Volume")) if pd.notna(latest_row.get("Volume")) else None,
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
        }

        return JSONResponse(content={"series": series, "latest": latest})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Failed to fetch SET index data", "message": str(e)})


@app.get("/api/series/symbol/{symbol}")
def get_symbol_series(symbol: str):
    """Return 1-year daily series for a specific symbol.

    Response:
      {
        "series": [{"time": "YYYY-MM-DD", "value": float}, ...],
        "latest": {
            "date": "YYYY-MM-DD",
            "close": float,
            "change": float,
            "change_percent": float
        }
      }
    """
    # Removed cache logic to avoid data mixing issues
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not HAS_YF:
                return JSONResponse(status_code=503, content={"error": "Yahoo Finance not available"})
            
            # Add .BK suffix for Thai stocks if not already present
            if not symbol.endswith('.BK'):
                symbol = f"{symbol}.BK"
            
            # Download 1 year of data with cache busting
            print(f"📊 Fetching data for {symbol} (attempt {attempt + 1})")
            
            # Add a delay to prevent rate limiting and allow cache to clear
            import time
            time.sleep(0.5)  # Increased delay for better cache clearing
                
            # Clear any potential yfinance cache more aggressively
            try:
                import yfinance as yf_module
                if hasattr(yf_module, 'cache'):
                    yf_module.cache.clear()
                # Also try to clear any session cache
                if hasattr(yf_module, 'session'):
                    yf_module.session.cache.clear()
                # Force a fresh session
                if hasattr(yf_module, 'session'):
                    yf_module.session.close()
                    yf_module.session = None
            except:
                pass
            
            # Use lock to serialize yfinance requests and prevent concurrent access issues
            with yfinance_lock:
                df = yf.download(symbol, period="1y", interval="1d", progress=False)
            
            # Debug: Check if we got the right data
            if not df.empty:
                try:
                    first_value = df.iloc[0]['Close'] if 'Close' in df.columns else df.iloc[0].iloc[0]
                    last_value = df.iloc[-1]['Close'] if 'Close' in df.columns else df.iloc[-1].iloc[0]
                    print(f"🔍 {symbol}: first={first_value}, last={last_value}")
                    
                    # Check if we got the wrong symbol's data by looking at the ticker name in the data
                    if str(first_value).startswith('Ticker'):
                        # Parse the ticker name from the string representation
                        first_value_str = str(first_value)
                        lines = first_value_str.split('\n')
                        ticker_in_data = None
                        
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('Ticker') and not line.startswith('Name:') and not line.startswith('dtype:'):
                                # Extract just the ticker name (before any spaces/values)
                                ticker_in_data = line.split()[0] if line.split() else None
                                break
                        
                        if ticker_in_data and ticker_in_data != symbol:
                            print(f"⚠️  Wrong symbol data detected for {symbol} (got {ticker_in_data}), retrying...")
                            if attempt < max_retries - 1:
                                continue
                        
                except Exception as e:
                    print(f"🔍 {symbol}: debug error - {e}")
            
            if df is None or df.empty:
                return JSONResponse(status_code=404, content={"error": f"No data found for {symbol}"})
            
            # Debug: Print basic info
            if not df.empty:
                print(f"📈 {symbol}: rows={len(df)}")
            
            # Handle MultiIndex columns from yfinance
            if isinstance(df.columns, pd.MultiIndex):
                # Reset index to make Date a column
                df = df.reset_index()
                # Flatten MultiIndex columns if present
                new_columns = []
                for col in df.columns:
                    if col[0] == 'Date':
                        new_columns.append('Date')
                    else:
                        new_columns.append(col[0])  # Use the first level (Price type)
                df.columns = new_columns
            else:
                df = df.reset_index()
            
            df = df.dropna(subset=["Close"]).sort_values("Date")
            if df.empty:
                return JSONResponse(status_code=404, content={"error": f"No valid data for {symbol}"})

            # Verify the data looks reasonable for this symbol
            latest_close = float(df.iloc[-1]["Close"])
            
            # Check for suspicious values that indicate wrong data
            if latest_close > 10000:  # Suspiciously high value
                print(f"⚠️  Suspicious data for {symbol}: close={latest_close}, retrying...")
                if attempt < max_retries - 1:
                    continue
                return JSONResponse(status_code=500, content={"error": f"Suspicious data returned for {symbol}"})
            
            # Additional check: if we got very low values that don't match expected ranges
            # This catches cases where we get wrong symbol data with very different price ranges
            if latest_close < 0.1 and symbol not in ['GRAND']:  # GRAND is legitimately very low
                print(f"⚠️  Suspiciously low data for {symbol}: close={latest_close}, retrying...")
                if attempt < max_retries - 1:
                    continue

            series = [
                {"time": d.strftime("%Y-%m-%d"), "value": float(c)}
                for d, c in zip(df["Date"], df["Close"]) if pd.notna(c)
            ]

            latest_row = df.iloc[-1]
            prev_row = df.iloc[-2] if len(df) >= 2 else None
            close = float(latest_row["Close"]) if pd.notna(latest_row.get("Close")) else None
            prev_close = float(prev_row["Close"]) if (prev_row is not None and pd.notna(prev_row.get("Close"))) else None
            change = (close - prev_close) if (close is not None and prev_close is not None) else 0.0
            change_pct = (change / prev_close * 100.0) if (prev_close not in (None, 0)) else 0.0

            latest = {
                "date": latest_row["Date"].strftime("%Y-%m-%d") if isinstance(latest_row["Date"], (pd.Timestamp,)) else str(latest_row["Date"]),
                "close": close,
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
            }

            print(f"✅ Successfully fetched data for {symbol} on attempt {attempt + 1}")
            
            result_data = {"series": series, "latest": latest}
            return JSONResponse(content=result_data)
            
        except Exception as e:
            print(f"❌ Error fetching {symbol} on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                continue
            return JSONResponse(status_code=500, content={"error": f"Failed to fetch data for {symbol}", "message": str(e)})


# Removed cache endpoints to avoid data mixing issues


@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_dashboard(request: Request):
    """Serve the portfolio dashboard page"""
    return templates.TemplateResponse("portfolio.html", {"request": request})


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


@app.post("/api/auto-update-database")
async def auto_update_database():
    """Auto-update database with daily limits and weekend skip"""
    try:
        # Check if today is weekend
        today = datetime.now()
        if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return {
                "success": True,
                "updated": False,
                "message": "Weekend - Market is closed, no update needed",
                "details": {"reason": "weekend", "day": today.strftime("%A")}
            }
        
        db = get_proper_db()
        today_date = today.date()
        
        # Check if we already updated today by looking at any table's latest data
        update_needed = False
        update_reasons = []
        
        # Check each data source
        checks = {
            "investor_summary": "No fresh investor data for today",
            "nvdr_trading": "No fresh NVDR data for today", 
            "short_sales_trading": "No fresh short sales data for today",
            "sector_data": "No fresh sector data for today"
        }
        
        for table_name, reason in checks.items():
            try:
                result = db.client.table(table_name).select('trade_date').eq('trade_date', today_date.isoformat()).limit(1).execute()
                if not result.data:
                    update_needed = True
                    update_reasons.append(reason)
            except Exception as e:
                # If table doesn't exist or has issues, we need to update
                update_needed = True
                update_reasons.append(f"{table_name}: {str(e)}")
        
        if not update_needed:
            return {
                "success": True,
                "updated": False,
                "message": "Database is already up to date for today",
                "details": {"date": today_date.isoformat(), "all_tables": "current"}
            }
        
        # Proceed with update
        update_progress("running", "auto-update", 0, "🔄 Starting automatic daily update...")
        
        return await save_to_database_internal()
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Auto-update error: {str(e)}")
        return {
            "success": False,
            "updated": False,
            "message": f"Auto-update failed: {str(e)}",
            "details": {"error": str(e), "timestamp": datetime.now().isoformat()}
        }


async def save_to_database_internal():
    """Internal function to save all data to database"""
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
        
        print(f"DB_DEBUG: Using trade date: {trade_date}")
        
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
            print(f"DB_ERROR: Investor scraping failed - exit_code: {exit_code}")
            update_progress("running", "investor_failed", 25, "❌ Failed to scrape investor data")
        
        # Step 2: Get all sector data
        update_progress("running", "sector_scraping", 35, "Scraping all sector constituents...", 
                      {"note": "This usually takes 30-60 seconds - scraping 8 sectors"})
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = OUTPUT_DIR / f"sectors_{timestamp}"
        outdir.mkdir(exist_ok=True)
        
        # Start with progress update during sector scraping
        sector_names = ["agro", "consump", "fincial", "indus", "propcon", "resourc", "service", "tech"]
        update_progress("running", "sector_scraping", 40, "📡 Preparing to scrape 8 sectors...", 
                      {"sectors": sector_names, "total": 8, "estimated": "30-60 seconds"})
        
        cmd = [sys.executable, "scrape_sector_data.py", "--outdir", str(outdir)]
        print(f"DB_DEBUG: Starting sector scraping to {outdir}")
        update_progress("running", "sector_scraping", 45, "🚀 Starting sector scraping command...", 
                      {"sectors": sector_names, "status": "launching scraper", "total": 8})
        
        # Small delay to ensure frontend receives the message
        await asyncio.sleep(0.2)
        
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=60)  # Increased to 60 seconds for reliability
        print(f"DEBUG: Sector scraping completed. Exit code: {exit_code}")
        print(f"DEBUG: stdout: {stdout[:200]}...")
        print(f"DEBUG: stderr: {stderr[:200]}...")
        
        # Always check if we got a complete set (8 sectors), regardless of exit code
        sector_files = list(outdir.glob("*.constituents.csv"))
        total_sectors = len(sector_files)
        
        # If we don't have all 8 sectors, use the most recent complete set
        if total_sectors < 8:
            print(f"DB_ERROR: Incomplete sector scraping - only got {total_sectors}/8 sectors")
            update_progress("running", "sector_fallback", 60, f"❌ Incomplete sector data ({total_sectors}/8) - using fallback...")
            
            # Find the most recent complete sector directory
            all_sector_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith("sectors_")]
            complete_dirs = []
            
            for sector_dir in all_sector_dirs:
                if sector_dir.name == outdir.name:  # Skip the current incomplete directory
                    continue
                sector_files_in_dir = list(sector_dir.glob("*.constituents.csv"))
                if len(sector_files_in_dir) >= 8:  # Complete set has all 8 sectors
                    complete_dirs.append((sector_dir, sector_files_in_dir))
            
            if complete_dirs:
                # Use the most recent complete directory (simple name sorting - works reliably)
                complete_dirs.sort(key=lambda x: x[0].name)
                outdir, sector_files = complete_dirs[-1]
                total_sectors = len(sector_files)
                print(f"DB_DEBUG: Using fallback data from {outdir.name} ({total_sectors} sectors)")
                update_progress("running", "sector_processing", 60, f"✅ Using complete sector data from {outdir.name} ({total_sectors} sectors)...")
            else:
                update_progress("running", "sector_failed", 60, "⚠️ No complete sector data available")
                sector_files = []
                total_sectors = 0
        else:
            print(f"DB_DEBUG: Using current scraping data ({total_sectors} sectors)")
            update_progress("running", "sector_processing", 60, f"✅ Processing complete sector data ({total_sectors} sectors)...")
        
        # Process sector files (whether from new scraping or fallback)
        sector_results = {}
        total_records_saved = 0
        
        if sector_files:
            for i, sector_file in enumerate(sector_files):
                sector_name = sector_file.stem.replace('.constituents', '')
                progress_pct = 60 + (i / total_sectors) * 30  # 60-90% range
                
                update_progress("running", "sector_processing", int(progress_pct), 
                              f"💾 Processing {sector_name} sector ({i+1}/{total_sectors})...", 
                              {"current_sector": sector_name, "completed": i, "total": total_sectors, "status": "processing"})
                
                # Small delay to ensure frontend receives the progress update
                await asyncio.sleep(0.1)
                
                try:
                    sector_df = pd.read_csv(sector_file)
                    print(f"DB_DEBUG: Loading {sector_name} - {len(sector_df)} rows from {sector_file.name}")
                    
                    # Save sector data with detailed error tracking
                    try:
                        success = db.save_sector_data(sector_df, sector_name, trade_date)
                        if success:
                            print(f"DB_DEBUG: {sector_name} sector saved successfully")
                        else:
                            print(f"DB_ERROR: {sector_name} sector save returned False")
                            update_progress("running", "sector_processing", int(progress_pct), 
                                          f"❌ {sector_name} sector save failed", 
                                          {"error": f"{sector_name} save returned False"})
                    except Exception as save_error:
                        print(f"DB_ERROR: {sector_name} sector save exception: {save_error}")
                        success = False
                        update_progress("running", "sector_processing", int(progress_pct), 
                                      f"❌ {sector_name} sector error: {str(save_error)[:30]}", 
                                      {"error": str(save_error)[:50]})
                    
                    results["sector_data"][sector_name] = success
                    sector_results[sector_name] = {"success": success, "records": len(sector_df) if success else 0}
                    
                    if success:
                        total_records_saved += len(sector_df)
                        completed_sectors = list(sector_results.keys())
                        update_progress("running", "sector_processing", int(progress_pct), 
                                      f"✅ {sector_name} sector complete ({len(sector_df)} records) [{i+1}/{total_sectors}]", 
                                      {"current_sector": sector_name, "records_count": len(sector_df), "completed": i+1, 
                                       "total": total_sectors, "completed_sectors": completed_sectors, "total_records": total_records_saved})
                        
                        # Small delay to ensure frontend receives the completion update
                        await asyncio.sleep(0.1)
                    else:
                        sector_results[sector_name] = {"success": False, "records": 0}
                        update_progress("running", "sector_processing", int(progress_pct), 
                                      f"⚠️ {sector_name} sector failed after {max_retries} attempts [{i+1}/{total_sectors}]", 
                                      {"current_sector": sector_name, "completed": i+1, "total": total_sectors, "error": f"failed after {max_retries} attempts"})
                        print(f"❌ Failed to save {sector_name} after {max_retries} attempts")
                        
                except Exception as e:
                    print(f"Error processing sector {sector_name}: {e}")
                    results["sector_data"][sector_name] = False
                    sector_results[sector_name] = {"success": False, "records": 0, "error": str(e)[:50]}
                    update_progress("running", "sector_processing", int(progress_pct), 
                                  f"❌ {sector_name} sector error: {str(e)[:30]}... [{i+1}/{total_sectors}]", 
                                  {"current_sector": sector_name, "completed": i+1, "total": total_sectors, "error": str(e)[:50]})
            
            # Sector completion summary
            successful_sectors = [name for name, result in sector_results.items() if result["success"]]
            failed_sectors = [name for name, result in sector_results.items() if not result["success"]]
            
            update_progress("running", "sector_summary", 89, 
                          f"🎯 Sector processing complete: {len(successful_sectors)}/{total_sectors} successful", 
                          {"successful_sectors": successful_sectors, "failed_sectors": failed_sectors, 
                           "total_records": total_records_saved, "summary": f"{len(successful_sectors)}/{total_sectors} sectors saved"})
            
            # Small delay to ensure frontend receives the summary
            await asyncio.sleep(0.2)
        
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
        
        # Final results with detailed statistics and debugging
        sector_success = all(results["sector_data"].values()) if results["sector_data"] else False
        total_success = results["investor_data"] and sector_success and results["nvdr_data"] and results["short_sales_data"]
        
        # Debug the final results
        print(f"DB_DEBUG: Final results summary:")
        print(f"  - Investor data: {results['investor_data']}")
        print(f"  - Sector success: {sector_success} (details: {results['sector_data']})")
        print(f"  - NVDR data: {results['nvdr_data']}")
        print(f"  - Short sales data: {results['short_sales_data']}")
        print(f"  - Total success: {total_success}")
        
        # Calculate detailed statistics
        successful_sectors = [name for name, success in results["sector_data"].items() if success] if results["sector_data"] else []
        failed_sectors = [name for name, success in results["sector_data"].items() if not success] if results["sector_data"] else []
        
        # Get record counts (approximate based on typical values)
        total_records_estimate = total_records_saved  # From sector processing
        if results["nvdr_data"]:
            total_records_estimate += 500  # Typical NVDR record count
        if results["short_sales_data"]:
            total_records_estimate += 200  # Typical short sales record count
        if results["investor_data"]:
            total_records_estimate += 4  # Investor summary records
        
        if total_success:
            update_progress("completed", "success", 100, 
                          f"🎉 Database update complete! All {len(successful_sectors)}/8 sectors + NVDR + Short Sales + Investor data saved successfully", 
                          {"successful_sectors": successful_sectors, "total_sectors": len(results["sector_data"]), 
                           "total_records": total_records_estimate, "trade_date": trade_date.isoformat() if trade_date else None,
                           "summary": f"✅ {len(successful_sectors)} sectors, ✅ NVDR data, ✅ Short sales data, ✅ Investor data"})
        else:
            success_count = sum([
                1 if results["investor_data"] else 0,
                len([v for v in results["sector_data"].values() if v]) if results["sector_data"] else 0,
                1 if results["nvdr_data"] else 0,
                1 if results["short_sales_data"] else 0
            ])
            total_count = 1 + len(results["sector_data"]) + 2  # investor + sectors + nvdr + short_sales
            
            status_summary = []
            if results["investor_data"]:
                status_summary.append("✅ Investor")
            else:
                status_summary.append("❌ Investor")
            
            if successful_sectors:
                status_summary.append(f"✅ {len(successful_sectors)} sectors")
            if failed_sectors:
                status_summary.append(f"❌ {len(failed_sectors)} sectors")
                
            if results["nvdr_data"]:
                status_summary.append("✅ NVDR")
            else:
                status_summary.append("❌ NVDR")
                
            if results["short_sales_data"]:
                status_summary.append("✅ Short Sales")
            else:
                status_summary.append("❌ Short Sales")
            
            update_progress("completed", "partial", 100, 
                          f"⚠️ Partial success: {success_count}/{total_count} datasets saved", 
                          {"successful_sectors": successful_sectors, "failed_sectors": failed_sectors,
                           "total_records": total_records_estimate, "status_summary": status_summary,
                           "details": results})
        
        return {
            "success": total_success,
            "updated": True,
            "message": "Data saved to database" if total_success else "Partial success",
            "details": results,
            "trade_date": trade_date.isoformat() if trade_date else None
        }
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Error: {str(e)}")
        return {
            "success": False,
            "updated": False,
            "message": f"Database save failed: {str(e)}",
            "details": {"error": str(e)},
            "trade_date": None
        }


@app.post("/api/save-to-database")
async def save_to_database():
    """Public endpoint for manual database save"""
    try:
        result = await save_to_database_internal()
        return JSONResponse(
            status_code=200 if result["success"] else 207,
            content=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database save failed",
                "message": str(e)
            }
        )


@app.post("/api/test-update-database")
async def test_update_database():
    """Test endpoint to trigger database update (bypasses weekend check)"""
    try:
        db = get_proper_db()
        today_date = datetime.now().date()
        
        # Force update for testing (bypass weekend and daily checks)
        update_progress("running", "test-update", 0, "🧪 Starting test update...")
        
        return await save_to_database_internal()
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Test update error: {str(e)}")
        return {
            "success": False,
            "updated": False,
            "message": f"Test update failed: {str(e)}",
            "details": {"error": str(e), "timestamp": datetime.now().isoformat()}
        }


@app.get("/api/set-index")
async def get_set_index():
    """Get SET index data with daily caching (database + file fallback)"""
    try:
        # First check file cache to see if data is fresh (today)
        latest_file = Path("_out/set_index_latest.json")
        today = datetime.now().date()
        file_is_fresh = False
        
        if latest_file.exists():
            # Check if file was modified today
            file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime).date()
            file_is_fresh = (file_mtime == today)
            
            if file_is_fresh:
                print("📊 Using fresh SET index data from file cache")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if file_data.get('success') and file_data.get('data'):
                        return {
                            "success": True,
                            "data": file_data['data'],
                            "timestamp": f"Cached data from {file_data.get('timestamp', 'unknown time')}",
                            "source": "file_cache",
                            "scraped_at": file_data.get('scraped_at', datetime.now().isoformat())
                        }
        
        # Try database first if available
        try:
            db = get_proper_db()
            if db.is_set_index_data_fresh():
                print("📊 Using fresh SET index data from database")
                db_result = db.get_latest_set_index_data()
                if db_result['status'] == 'success' and db_result['data']:
                    return {
                        "success": True,
                        "data": db_result['data'],
                        "timestamp": f"Database data for {db_result['trade_date']}",
                        "source": "database",
                        "scraped_at": datetime.now().isoformat()
                    }
        except Exception as db_error:
            print(f"⚠️ Database check failed: {db_error}")
        
        # If no fresh data, scrape new data
        print("🔄 No fresh data found, scraping new SET index data...")
        
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "scrape_set_index.py", "--save-db"],
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=45
            )
            
            if result.returncode == 0:
                # After successful scraping, try database first, then file
                try:
                    db = get_proper_db()
                    db_result = db.get_latest_set_index_data()
                    if db_result['status'] == 'success' and db_result['data']:
                        return {
                            "success": True,
                            "data": db_result['data'],
                            "timestamp": f"Fresh data for {db_result['trade_date']}",
                            "source": "scraped_to_database",
                            "scraped_at": datetime.now().isoformat()
                        }
                except Exception as db_error:
                    print(f"⚠️ Database retrieval failed after scraping: {db_error}")
                
                # Fallback to file
                if latest_file.exists():
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        if file_data.get('success') and file_data.get('data'):
                            return {
                                "success": True,
                                "data": file_data['data'],
                                "timestamp": f"Fresh data: {file_data.get('timestamp', 'unknown time')}",
                                "source": "scraped_to_file",
                                "scraped_at": file_data.get('scraped_at', datetime.now().isoformat())
                            }
                
                raise Exception("Failed to retrieve data after successful scraping")
            else:
                raise Exception(f"Scraping failed: {result.stderr}")
                
        except Exception as scrape_error:
            # Final fallback: try any available data (database, then file)
            print(f"⚠️ Scraping failed: {scrape_error}, trying fallback...")
            
            try:
                db = get_proper_db()
                db_result = db.get_latest_set_index_data()
                if db_result['status'] == 'success' and db_result['data']:
                    return {
                        "success": True,
                        "data": db_result['data'],
                        "timestamp": f"Cached data from {db_result['trade_date']} (scraping failed)",
                        "source": "database_fallback",
                        "warning": f"Using cached data due to scraping error: {str(scrape_error)}",
                        "scraped_at": datetime.now().isoformat()
                    }
            except Exception:
                pass
            
            if latest_file.exists():
                with open(latest_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if file_data.get('success') and file_data.get('data'):
                        return {
                            "success": True,
                            "data": file_data['data'],
                            "timestamp": f"Cached data: {file_data.get('timestamp', 'unknown time')} (scraping failed)",
                            "source": "file_fallback",
                            "warning": f"Using cached file data due to scraping error: {str(scrape_error)}",
                            "scraped_at": file_data.get('scraped_at', datetime.now().isoformat())
                        }
            
            # Ultimate fallback: return error
            return {
                "success": False,
                "error": f"Failed to fetch SET index data: {str(scrape_error)}",
                "data": [],
                "timestamp": None,
                "source": "error",
                "scraped_at": datetime.now().isoformat()
            }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to load SET index data",
                "message": str(e)
            }
        )


@app.get("/api/portfolio/dashboard")
async def get_portfolio_dashboard():
    """Get portfolio dashboard data with latest investor summary, sector summary, and individual stock data"""
    try:
        db = get_proper_db()
        
        # Get latest trade date from any of the tables
        latest_trade_date = None
        
        # Try to get latest trade date from investor_summary
        try:
            investor_result = db.client.table('investor_summary').select('trade_date').order('trade_date', desc=True).limit(1).execute()
            if investor_result.data:
                latest_trade_date = investor_result.data[0]['trade_date']
        except:
            pass
        
        # If no investor data, try sector_data
        if not latest_trade_date:
            try:
                sector_result = db.client.table('sector_data').select('trade_date').order('trade_date', desc=True).limit(1).execute()
                if sector_result.data:
                    latest_trade_date = sector_result.data[0]['trade_date']
            except:
                pass
        
        # Get investor summary data for latest date
        investor_summary = []
        if latest_trade_date:
            investor_result = db.client.table('investor_summary').select('*').eq('trade_date', latest_trade_date).order('created_at', desc=True).execute()
            
            # Get unique investor types (latest entry for each type)
            seen_types = set()
            unique_investors = []
            for item in investor_result.data if investor_result.data else []:
                if item['investor_type'] not in seen_types:
                    unique_investors.append(item)
                    seen_types.add(item['investor_type'])
            
            # Sort in the same order as CSV: Local Institutions, Proprietary Trading, Foreign Investors, Local Individuals
            order = ['Local Institutions', 'Proprietary Trading', 'Foreign Investors', 'Local Individuals']
            def get_sort_key(investor):
                investor_type = investor['investor_type']
                try:
                    return order.index(investor_type)
                except ValueError:
                    return 999  # Put unknown types at the end
            
            investor_summary = sorted(unique_investors, key=get_sort_key)
        
        # Get sector summary (count of stocks and average prices by sector)
        sector_summary = []
        if latest_trade_date:
            sector_result = db.client.table('sector_data').select('sector, last_price, symbol').eq('trade_date', latest_trade_date).execute()
            sector_data = sector_result.data if sector_result.data else []
            
            # Group by sector
            sectors = {}
            for item in sector_data:
                sector = item['sector']
                if sector not in sectors:
                    sectors[sector] = {'count': 0, 'total_price': 0, 'prices': []}
                
                if item['last_price'] is not None:
                    sectors[sector]['count'] += 1
                    sectors[sector]['total_price'] += item['last_price']
                    sectors[sector]['prices'].append(item['last_price'])
            
            # Calculate averages
            for sector, data in sectors.items():
                avg_price = data['total_price'] / data['count'] if data['count'] > 0 else 0
                sector_summary.append({
                    'sector': sector,
                    'stock_count': data['count'],
                    'avg_price': round(avg_price, 2)
                })
        
        # Get individual stock data (combining sector_data, nvdr_trading, short_sales_trading)
        portfolio_stocks = []
        if latest_trade_date:
            # Get all stocks with prices from sector_data
            stocks_result = db.client.table('sector_data').select('symbol, last_price, sector, change, percent_change').eq('trade_date', latest_trade_date).execute()
            
            # Clean the data to prevent JSON compliance issues
            stocks_data = {}
            if stocks_result.data:
                for item in stocks_result.data:
                    # Only include stocks with valid last_price (allow legitimate low prices like 0.04)
                    if item.get('last_price') is not None and item['last_price'] >= 0:
                        # Clean change and percent_change values
                        cleaned_item = {
                            'symbol': item['symbol'],
                            'last_price': item['last_price'],
                            'sector': item['sector'],
                            'change': item.get('change', '0.00') or '0.00',
                            'percent_change': item.get('percent_change', '0.00') or '0.00'
                        }
                        stocks_data[item['symbol']] = cleaned_item
            print(f"📊 DEBUG: Found {len(stocks_data)} stocks in sector_data for date {latest_trade_date}")
            if 'GRAND' in stocks_data:
                print(f"✅ DEBUG: GRAND found in sector_data: {stocks_data['GRAND']}")
            else:
                print(f"❌ DEBUG: GRAND NOT found in sector_data")
            
            # Get NVDR data
            nvdr_result = db.client.table('nvdr_trading').select('symbol, value_net').eq('trade_date', latest_trade_date).execute()
            nvdr_data = {item['symbol']: item['value_net'] for item in nvdr_result.data if item['value_net'] is not None} if nvdr_result.data else {}
            
            # Get Short Sales data
            short_result = db.client.table('short_sales_trading').select('symbol, short_value_baht').eq('trade_date', latest_trade_date).execute()
            short_data = {item['symbol']: item['short_value_baht'] for item in short_result.data if item['short_value_baht'] is not None} if short_result.data else {}
            
            # Only include symbols that have sector data (price information)
            # This prevents JSON compliance issues with symbols that only have NVDR/short data
            for symbol in sorted(stocks_data.keys()):  # Only process symbols with sector data
                stock_info = stocks_data[symbol]
                
                # Skip symbols without valid last_price
                if not stock_info.get('last_price'):
                    continue
                
                # Parse change and percent_change strings to numbers
                change_str = stock_info.get('change', '')
                percent_change_str = stock_info.get('percent_change', '')
                
                # Helper function to parse change values
                def parse_change(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        # Remove + sign and convert to float
                        cleaned = str(value).replace('+', '').replace(',', '').strip()
                        if cleaned == '-' or cleaned == '':
                            return 0
                        result = float(cleaned)
                        # Check for invalid float values
                        import math
                        if math.isnan(result) or math.isinf(result):
                            print(f"⚠️  DEBUG: parse_change found invalid value: '{value}' -> '{cleaned}' -> {result}")
                            return 0
                        return result
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  DEBUG: parse_change error with '{value}': {e}")
                        return 0
                
                def parse_percent(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        # Remove % sign and + sign, then convert to float
                        cleaned = str(value).replace('%', '').replace('+', '').replace(',', '').strip()
                        if cleaned == '-' or cleaned == '':
                            return 0
                        result = float(cleaned)
                        # Check for invalid float values
                        import math
                        if math.isnan(result) or math.isinf(result):
                            print(f"⚠️  DEBUG: parse_percent found invalid value: '{value}' -> '{cleaned}' -> {result}")
                            return 0
                        return result
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  DEBUG: parse_percent error with '{value}': {e}")
                        return 0
                
                portfolio_stocks.append({
                    'symbol': symbol,
                    'close': stock_info.get('last_price', 0),
                    'change': parse_change(change_str),
                    'percent_change': parse_percent(percent_change_str),
                    'sector': stock_info.get('sector', ''),
                    'nvdr': nvdr_data.get(symbol, 0) if nvdr_data.get(symbol) else 0,  # Keep in Baht
                    'shortBaht': short_data.get(symbol, 0) if short_data.get(symbol) else 0,  # Keep in Baht
                })
        
        # Validate JSON compliance before returning
        def is_json_safe(value):
            """Check if a value is JSON compliant"""
            import math
            if isinstance(value, float):
                return not (math.isnan(value) or math.isinf(value))
            return True
            
        def validate_json_data(data, path=""):
            """Recursively validate JSON data for compliance"""
            if isinstance(data, dict):
                for key, value in data.items():
                    if not validate_json_data(value, f"{path}.{key}"):
                        print(f"❌ JSON compliance error at {path}.{key}: {value} ({type(value)})")
                        return False
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if not validate_json_data(item, f"{path}[{i}]"):
                        return False
            elif not is_json_safe(data):
                print(f"❌ JSON compliance error at {path}: {data} ({type(data)})")
                return False
            return True
        
        response_data = {
            'trade_date': latest_trade_date,
            'investor_summary': investor_summary,
            'sector_summary': sector_summary,
            'portfolio_stocks': portfolio_stocks
        }
        
        # Validate before returning
        if not validate_json_data(response_data):
            print("❌ Dashboard response contains non-JSON compliant data")
            # Return a safe fallback response
            return JSONResponse(content={
                'trade_date': latest_trade_date,
                'investor_summary': [],
                'sector_summary': [],
                'portfolio_stocks': [],
                'error': 'Data contains invalid float values'
            })
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get portfolio dashboard data",
                "message": str(e)
            }
        )


@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Get summary statistics for the portfolio dashboard"""
    try:
        db = get_proper_db()
        
        # Get latest trade date
        sector_result = db.client.table('sector_data').select('trade_date').order('trade_date', desc=True).limit(1).execute()
        latest_trade_date = sector_result.data[0]['trade_date'] if sector_result.data else None
        
        if not latest_trade_date:
            return JSONResponse(content={'error': 'No data available'})
        
        # Count total symbols
        stocks_result = db.client.table('sector_data').select('symbol').eq('trade_date', latest_trade_date).execute()
        total_symbols = len(stocks_result.data) if stocks_result.data else 0
        
        # Get NVDR totals
        nvdr_result = db.client.table('nvdr_trading').select('value_net').eq('trade_date', latest_trade_date).execute()
        total_nvdr = sum(item['value_net'] for item in nvdr_result.data if item['value_net'] is not None) if nvdr_result.data else 0
        
        # Get Short Sales totals
        short_result = db.client.table('short_sales_trading').select('short_value_baht').eq('trade_date', latest_trade_date).execute()
        total_short = sum(item['short_value_baht'] for item in short_result.data if item['short_value_baht'] is not None) if short_result.data else 0
        
        # Calculate average price
        prices_result = db.client.table('sector_data').select('last_price').eq('trade_date', latest_trade_date).execute()
        prices = [item['last_price'] for item in prices_result.data if item['last_price'] is not None] if prices_result.data else []
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return JSONResponse(content={
            'trade_date': latest_trade_date,
            'total_symbols': total_symbols,
            'avg_price': round(avg_price, 2),
            'total_nvdr_mb': round(total_nvdr / 1000000, 2),  # Convert to millions
            'total_short_mb': round(total_short / 1000000, 2)  # Convert to millions
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get portfolio summary",
                "message": str(e)
            }
        )


@app.post("/api/portfolio/add-symbol")
async def add_portfolio_symbol(request: Request):
    """Add a symbol to the user's portfolio"""
    try:
        data = await request.json()
        symbol = data.get('symbol', '').strip().upper()
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        db = get_proper_db()
        success = db.add_portfolio_symbol(symbol)
        
        if success:
            return JSONResponse(content={"success": True, "message": f"Added {symbol} to portfolio"})
        else:
            raise HTTPException(status_code=500, detail="Failed to add symbol to portfolio")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding symbol: {str(e)}")


@app.delete("/api/portfolio/remove-symbol/{symbol}")
async def remove_portfolio_symbol(symbol: str):
    """Remove a symbol from the user's portfolio"""
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        db = get_proper_db()
        success = db.remove_portfolio_symbol(symbol)
        
        if success:
            return JSONResponse(content={"success": True, "message": f"Removed {symbol} from portfolio"})
        else:
            raise HTTPException(status_code=500, detail="Failed to remove symbol from portfolio")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing symbol: {str(e)}")


@app.get("/api/portfolio/my-symbols")
async def get_my_portfolio():
    """Get the user's portfolio with current stock data"""
    try:
        db = get_proper_db()
        
        # Get portfolio symbols
        portfolio_symbols = db.get_portfolio_symbols()
        
        if not portfolio_symbols:
            return JSONResponse(content={
                'portfolio_symbols': [],
                'portfolio_stocks': []
            })
        
        # Get latest trade date
        sector_result = db.client.table('sector_data').select('trade_date').order('trade_date', desc=True).limit(1).execute()
        latest_trade_date = sector_result.data[0]['trade_date'] if sector_result.data else None
        
        portfolio_stocks = []
        if latest_trade_date:
            # Get stock data for portfolio symbols
            stocks_result = db.client.table('sector_data').select('symbol, last_price, sector, change, percent_change').eq('trade_date', latest_trade_date).execute()
            stocks_data = {item['symbol']: item for item in stocks_result.data} if stocks_result.data else {}
            
            # Get NVDR data for portfolio symbols
            nvdr_result = db.client.table('nvdr_trading').select('symbol, value_net').eq('trade_date', latest_trade_date).execute()
            nvdr_data = {item['symbol']: item['value_net'] for item in nvdr_result.data if item['value_net'] is not None} if nvdr_result.data else {}
            
            # Get Short Sales data for portfolio symbols
            short_result = db.client.table('short_sales_trading').select('symbol, short_value_baht').eq('trade_date', latest_trade_date).execute()
            short_data = {item['symbol']: item['short_value_baht'] for item in short_result.data if item['short_value_baht'] is not None} if short_result.data else {}
            
            # Build portfolio stock data (symbols already sorted A-Z from database)
            for symbol in portfolio_symbols:
                stock_info = stocks_data.get(symbol, {})
                
                # Parse change data
                def parse_change(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        cleaned = str(value).replace('+', '').replace(',', '').strip()
                        return float(cleaned) if cleaned != '-' else 0
                    except (ValueError, TypeError):
                        return 0
                
                def parse_percent(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        cleaned = str(value).replace('%', '').replace('+', '').replace(',', '').strip()
                        return float(cleaned) if cleaned != '-' else 0
                    except (ValueError, TypeError):
                        return 0
                
                change_str = stock_info.get('change', '')
                percent_change_str = stock_info.get('percent_change', '')
                
                # Check if we have valid data from sector_data
                close_price = stock_info.get('last_price', 0)
                sector = stock_info.get('sector', '')
                
                # If no valid data from sector_data, mark for API update
                # Note: Only treat as invalid if price is None/missing AND no sector data
                if (close_price is None or close_price < 0) or not sector:
                    print(f"⚠️ {symbol} has no valid data in sector_data (close={close_price}, sector={sector})")
                    # We'll handle this in the frontend by showing a note to refresh
                
                portfolio_stocks.append({
                    'symbol': symbol,
                    'close': close_price,
                    'change': parse_change(change_str),
                    'percent_change': parse_percent(percent_change_str),
                    'sector': sector,
                    'nvdr': nvdr_data.get(symbol, 0) if nvdr_data.get(symbol) else 0,
                    'shortBaht': short_data.get(symbol, 0) if short_data.get(symbol) else 0,
                })
        
        return JSONResponse(content={
            'portfolio_symbols': portfolio_symbols,
            'portfolio_stocks': portfolio_stocks,
            'trade_date': latest_trade_date
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio: {str(e)}")


@app.post("/api/portfolio/update-symbol-data/{symbol}")
async def update_symbol_data(symbol: str):
    """Update portfolio symbol data with latest API data"""
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Get latest data from API
        api_data = get_symbol_series(symbol)
        if hasattr(api_data, 'body'):
            import json
            api_content = json.loads(api_data.body.decode())
            latest_data = api_content.get('latest', {})
            
            if latest_data.get('close', 0) > 0:
                # Update the portfolio data in memory (for this session)
                # Note: This is a temporary fix - in a real app you'd update the database
                return JSONResponse(content={
                    "success": True,
                    "message": f"Updated {symbol} data",
                    "data": {
                        "symbol": symbol,
                        "close": latest_data['close'],
                        "change": latest_data['change'],
                        "change_percent": latest_data['change_percent'],
                        "date": latest_data['date']
                    }
                })
            else:
                raise HTTPException(status_code=404, detail=f"No valid data found for {symbol}")
        else:
            raise HTTPException(status_code=500, detail="Failed to get API data")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating symbol data: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
