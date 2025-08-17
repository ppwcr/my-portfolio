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

# Windows-specific asyncio event loop policy fix
if sys.platform == "win32":
    # Set event loop policy to avoid issues with subprocess on Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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
    
    # Windows-specific fixes
    if sys.platform == "win32":
        # On Windows, ensure the script paths exist and are accessible
        if len(cmd) >= 2 and cmd[1].endswith('.py'):
            script_path = Path(cmd[1])
            if not script_path.exists():
                return (
                    1,
                    "",
                    f"Script not found: {script_path.absolute()}"
                )
        
        # Try using subprocess.run first for better Windows compatibility
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=Path.cwd()
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (124, "", f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
        except Exception as sync_error:
            print(f"Windows subprocess.run failed: {sync_error}, trying asyncio...")
    
    # Fallback to asyncio method (for non-Windows or if subprocess.run fails)
    kwargs = {}
    if sys.platform == "win32":
        import subprocess
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd(),
            **kwargs
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        
        # Use proper encoding detection for Windows
        encoding = 'utf-8'
        if sys.platform == "win32":
            import locale
            try:
                encoding = locale.getpreferredencoding() or 'utf-8'
            except:
                encoding = 'cp1252'
        
        return (
            proc.returncode,
            stdout.decode(encoding, errors='replace'),
            stderr.decode(encoding, errors='replace')
        )
        
    except asyncio.TimeoutError:
        if 'proc' in locals() and proc and proc.returncode is None:
            if sys.platform == "win32":
                proc.kill()
            else:
                proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        
        return (124, "", f"Command timed out after {timeout} seconds: {' '.join(cmd)}")
    except Exception as e:
        return (1, "", f"Subprocess error: {str(e)}")


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
    if os.getenv("NO_SANDBOX") == "1" or sys.platform == "win32":
        cmd.append("--no-sandbox")  # Always use --no-sandbox on Windows
    
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
    if os.getenv("NO_SANDBOX") == "1" or sys.platform == "win32":
        cmd.append("--no-sandbox")  # Always use --no-sandbox on Windows
    
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
    """Auto-update database - always runs when called (weekend detection disabled)"""
    try:
        # Proceed with update immediately (no weekend or daily checks)
        update_progress("running", "auto-update", 0, "🔄 Starting database update...")
        
        return await save_to_database()
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Auto-update error: {str(e)}")
        return {
            "success": False,
            "updated": False,
            "message": f"Auto-update failed: {str(e)}",
            "details": {"error": str(e), "timestamp": datetime.now().isoformat()}
        }



@app.post("/api/save-to-database")
async def save_to_database():
    """Save investor type (SET market) and all sector data to Supabase database"""
    try:
        # Initialize progress
        update_progress("starting", "Initializing", 0, "Starting database save operation...")
        
        # Initialize database connection with error handling
        try:
            db = get_proper_db()
            update_progress("running", "db_connected", 5, "Database connection established")
        except Exception as db_error:
            error_msg = f"Failed to connect to database: {str(db_error)}"
            update_progress("error", "db_failed", 0, error_msg)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Database connection failed",
                    "message": str(db_error),
                    "platform": sys.platform
                }
            )
        results = {"investor_data": False, "sector_data": {}, "nvdr_data": False, "short_sales_data": False}
        
        # Initialize trade_date early to avoid reference errors
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
            investor_df = pd.read_csv(csv_path)
            results["investor_data"] = db.save_investor_summary(investor_df, trade_date)
            update_progress("running", "investor_saved", 30, f"Saved {len(investor_df)} investor records")
        else:
            error_msg = f"Failed to scrape investor data (exit_code: {exit_code})"
            if stderr:
                error_msg += f" - {stderr_tail(stderr)}"
            update_progress("running", "investor_failed", 25, error_msg)
            print(f"❌ Investor scraping failed: {error_msg}")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
        
        # Step 2: Get all sector data
        update_progress("running", "sector_scraping", 35, "Scraping sector data...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outdir = OUTPUT_DIR / f"sectors_{timestamp}"
        outdir.mkdir(exist_ok=True)
        
        cmd = [sys.executable, "scrape_sector_data.py", "--outdir", str(outdir)]
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=120)
        
        if exit_code != 0:
            error_msg = f"Sector scraping had issues (exit_code: {exit_code})"
            if stderr:
                error_msg += f" - {stderr_tail(stderr)}"
            print(f"⚠️ Sector scraping warning: {error_msg}")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            update_progress("running", "sector_warning", 40, "Sector scraping had issues, trying fallback data...")
        
        # Process sector files
        sector_files = list(outdir.glob("*.constituents.csv"))
        total_sectors = len(sector_files)
        
        if total_sectors < 8:
            # Use fallback data
            all_sector_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name.startswith("sectors_")]
            complete_dirs = [(d, list(d.glob("*.constituents.csv"))) for d in all_sector_dirs if len(list(d.glob("*.constituents.csv"))) >= 8]
            
            if complete_dirs:
                complete_dirs.sort(key=lambda x: x[0].name)
                outdir, sector_files = complete_dirs[-1]
                total_sectors = len(sector_files)
        
        update_progress("running", "sector_processing", 60, f"Processing {total_sectors} sectors")
        
        for i, sector_file in enumerate(sector_files):
            sector_name = sector_file.stem.replace('.constituents', '')
            try:
                sector_df = pd.read_csv(sector_file)
                success = db.save_sector_data(sector_df, sector_name, trade_date)
                results["sector_data"][sector_name] = success
                
                progress_pct = 60 + (i / total_sectors) * 30
                if success:
                    update_progress("running", "sector_processing", int(progress_pct), f"Saved {sector_name}")
                else:
                    update_progress("running", "sector_processing", int(progress_pct), f"Failed {sector_name}")
            except Exception as e:
                results["sector_data"][sector_name] = False
                update_progress("running", "sector_processing", int(progress_pct), f"Error {sector_name}")
        
        # Step 3: Download and save NVDR data
        update_progress("running", "nvdr_downloading", 90, "Downloading NVDR Excel file...")
        
        nvdr_output_path = OUTPUT_DIR / ts_name("nvdr", "xlsx")
        nvdr_cmd = [sys.executable, "download_nvdr_excel.py", "--out", str(nvdr_output_path)]
        
        # Add Windows-specific flags
        if os.getenv("HEADFUL") == "1":
            nvdr_cmd.append("--headful")
        if os.getenv("NO_SANDBOX") == "1" or sys.platform == "win32":
            nvdr_cmd.append("--no-sandbox")  # Always use --no-sandbox on Windows
        
        nvdr_exit_code, nvdr_stdout, nvdr_stderr = await run_cmd(nvdr_cmd, timeout=60)
        
        if nvdr_exit_code == 0 and nvdr_output_path.exists():
            update_progress("running", "nvdr_processing", 93, "Processing NVDR data...")
            results["nvdr_data"] = db.save_nvdr_trading(str(nvdr_output_path), trade_date)
            if results["nvdr_data"]:
                update_progress("running", "nvdr_saved", 93, "NVDR data saved")
            else:
                update_progress("running", "nvdr_failed", 93, "Failed to save NVDR data to database")
        else:
            error_msg = f"NVDR download failed (exit_code: {nvdr_exit_code})"
            if nvdr_stderr:
                error_msg += f" - {stderr_tail(nvdr_stderr)}"
            update_progress("running", "nvdr_failed", 93, error_msg)
            print(f"❌ NVDR download failed: {error_msg}")
            print(f"   stdout: {nvdr_stdout}")
            print(f"   stderr: {nvdr_stderr}")
            results["nvdr_data"] = False
        
        # Step 4: Download and save Short Sales data
        update_progress("running", "shortsales_downloading", 95, "Downloading Short Sales Excel file...")
        
        short_output_path = OUTPUT_DIR / ts_name("short_sales", "xlsx")
        short_cmd = [sys.executable, "download_short_sales_excel.py", "--out", str(short_output_path)]
        
        # Add Windows-specific flags
        if os.getenv("HEADFUL") == "1":
            short_cmd.append("--headful")
        if os.getenv("NO_SANDBOX") == "1" or sys.platform == "win32":
            short_cmd.append("--no-sandbox")  # Always use --no-sandbox on Windows
        
        short_exit_code, short_stdout, short_stderr = await run_cmd(short_cmd, timeout=60)
        
        if short_exit_code == 0 and short_output_path.exists():
            update_progress("running", "shortsales_processing", 97, "Processing Short Sales data...")
            results["short_sales_data"] = db.save_short_sales_trading(str(short_output_path), trade_date)
            if results["short_sales_data"]:
                update_progress("running", "shortsales_saved", 98, "Short Sales data saved")
            else:
                update_progress("running", "shortsales_failed", 98, "Failed to save Short Sales data to database")
        else:
            error_msg = f"Short Sales download failed (exit_code: {short_exit_code})"
            if short_stderr:
                error_msg += f" - {stderr_tail(short_stderr)}"
            update_progress("running", "shortsales_failed", 98, error_msg)
            print(f"❌ Short Sales download failed: {error_msg}")
            print(f"   stdout: {short_stdout}")
            print(f"   stderr: {short_stderr}")
            results["short_sales_data"] = False
        
        # Final results with detailed analysis
        sector_success = all(results["sector_data"].values()) if results["sector_data"] else False
        total_success = results["investor_data"] and sector_success and results["nvdr_data"] and results["short_sales_data"]
        
        # Create detailed success/failure summary
        success_summary = {
            "investor_data": results["investor_data"],
            "sector_data": f"{sum(results['sector_data'].values())} of {len(results['sector_data'])} sectors" if results["sector_data"] else "No sectors",
            "nvdr_data": results["nvdr_data"],
            "short_sales_data": results["short_sales_data"]
        }
        
        failed_components = []
        if not results["investor_data"]:
            failed_components.append("investor data")
        if not sector_success:
            failed_sectors = [k for k, v in results["sector_data"].items() if not v] if results["sector_data"] else ["all sectors"]
            failed_components.append(f"sector data ({', '.join(failed_sectors)})")
        if not results["nvdr_data"]:
            failed_components.append("NVDR data")
        if not results["short_sales_data"]:
            failed_components.append("short sales data")
        
        if total_success:
            message = "✅ All data saved successfully"
            update_progress("completed", "success", 100, message)
        else:
            message = f"⚠️ Partial success - Failed: {', '.join(failed_components)}"
            update_progress("completed", "partial", 100, message)
        
        return {
            "success": total_success,
            "updated": True,
            "message": message,
            "details": results,
            "summary": success_summary,
            "failed_components": failed_components,
            "trade_date": trade_date.isoformat() if trade_date else None
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = f"Database save failed: {str(e)}"
        
        # Log detailed error information for debugging
        print(f"❌ CRITICAL ERROR in save_to_database:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Traceback: {error_trace}")
        
        update_progress("error", "failed", 0, f"Error: {str(e)}")
        
        # Provide more specific error details for different platforms
        if sys.platform == "win32":
            error_msg += " (Windows detected - check subprocess execution and encoding)"
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database save failed",
                "message": str(e),
                "platform": sys.platform,
                "error_type": type(e).__name__
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
        
        return await save_to_database()
        
    except Exception as e:
        update_progress("error", "failed", 0, f"❌ Test update error: {str(e)}")
        return {
            "success": False,
            "updated": False,
            "message": f"Test update failed: {str(e)}",
            "details": {"error": str(e), "timestamp": datetime.now().isoformat()}
        }


@app.post("/api/debug-components")
async def debug_components():
    """Debug endpoint to test individual components on Windows"""
    debug_results = {
        "platform": sys.platform,
        "python_path": sys.executable,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "working_dir": str(Path.cwd()),
        "scripts_exist": {
            "scrape_investor_data.py": Path("scrape_investor_data.py").exists(),
            "download_nvdr_excel.py": Path("download_nvdr_excel.py").exists(),
            "download_short_sales_excel.py": Path("download_short_sales_excel.py").exists()
        },
        "components": {}
    }
    
    try:
        # Test 1: Investor data scraping
        print("🔍 Testing investor data scraping...")
        csv_path = OUTPUT_DIR / "debug_investor_table.csv"
        json_path = OUTPUT_DIR / "debug_investor_chart.json"
        
        cmd = [
            sys.executable, "scrape_investor_data.py",
            "--market", "SET",
            "--out-table", str(csv_path),
            "--out-json", str(json_path),
            "--allow-missing-chart"
        ]
        
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=30)
        debug_results["components"]["investor_data"] = {
            "exit_code": exit_code,
            "file_exists": csv_path.exists(),
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else "",
            "command": " ".join(cmd)
        }
        
        # Test 2: NVDR download
        print("🔍 Testing NVDR download...")
        nvdr_path = OUTPUT_DIR / "debug_nvdr.xlsx"
        nvdr_cmd = [sys.executable, "download_nvdr_excel.py", "--out", str(nvdr_path)]
        if sys.platform == "win32":
            nvdr_cmd.append("--no-sandbox")
            
        exit_code, stdout, stderr = await run_cmd(nvdr_cmd, timeout=30)
        debug_results["components"]["nvdr_data"] = {
            "exit_code": exit_code,
            "file_exists": nvdr_path.exists(),
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else "",
            "command": " ".join(nvdr_cmd)
        }
        
        # Test 3: Short sales download
        print("🔍 Testing short sales download...")
        short_path = OUTPUT_DIR / "debug_short.xlsx"
        short_cmd = [sys.executable, "download_short_sales_excel.py", "--out", str(short_path)]
        if sys.platform == "win32":
            short_cmd.append("--no-sandbox")
            
        exit_code, stdout, stderr = await run_cmd(short_cmd, timeout=30)
        debug_results["components"]["short_sales_data"] = {
            "exit_code": exit_code,
            "file_exists": short_path.exists(),
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else "",
            "command": " ".join(short_cmd)
        }
        
        # Test 4: Database connection
        print("🔍 Testing database connection...")
        try:
            db = get_proper_db()
            test_result = db.client.table('investor_summary').select('trade_date').limit(1).execute()
            debug_results["components"]["database"] = {
                "connection": "success",
                "table_accessible": True,
                "error": None
            }
        except Exception as db_error:
            debug_results["components"]["database"] = {
                "connection": "failed",
                "table_accessible": False,
                "error": str(db_error)[:200]
            }
        
        return debug_results
        
    except Exception as e:
        debug_results["error"] = str(e)
        return debug_results


@app.post("/api/install-playwright-browsers")
async def install_playwright_browsers():
    """Install Playwright browsers (Windows fix)"""
    if sys.platform != "win32":
        return {"success": False, "message": "This endpoint is only for Windows"}
    
    try:
        print("🔧 Installing Playwright browsers for Windows...")
        
        # Try to install Playwright browsers
        cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=300)  # 5 minute timeout
        
        if exit_code == 0:
            return {
                "success": True,
                "message": "Playwright browsers installed successfully",
                "stdout": stdout,
                "stderr": stderr
            }
        else:
            return {
                "success": False,
                "message": f"Failed to install browsers (exit_code: {exit_code})",
                "stdout": stdout,
                "stderr": stderr
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error installing browsers: {str(e)}"
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
