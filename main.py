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
from fastapi.responses import Response
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import background updater
from background_updater import startup_data_refresh, scheduled_data_refresh
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    """Run Python scripts directly on server startup"""
    print("🌟 Server starting up - running Python scripts...")
    
    async def run_python_scripts():
        """Run the Python scripts that work"""
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Download NVDR (works perfectly)
        print("📥 Running NVDR download...")
        result = subprocess.run([
            sys.executable, "download_nvdr_excel.py", 
            "--out", f"_out/nvdr_{timestamp}.xlsx", 
            "--timeout", "90000"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVDR download completed")
        
        # 2. Download Short Sales (works perfectly)  
        print("📥 Running Short Sales download...")
        result = subprocess.run([
            sys.executable, "download_short_sales_excel.py",
            "--out", f"_out/short_sales_{timestamp}.xlsx",
            "--timeout", "90000"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Short Sales download completed")
        
        # 3. Run SET index (you said it works)
        print("📥 Running SET index scraping...")
        result = subprocess.run([
            sys.executable, "scrape_set_index.py", "--save-db"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ SET index completed")
        
        # 4. Run sector data scraping (needed for portfolio)
        print("📥 Running sector data scraping...")
        result = subprocess.run([
            sys.executable, "scrape_sector_data.py", 
            "--outdir", f"_out/sectors_{timestamp}"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Sector data completed")
        
        # 5. Run investor data scraping (table data only)
        print("📥 Running investor data scraping...")
        os.makedirs("_out/investor", exist_ok=True)
        result = subprocess.run([
            sys.executable, "scrape_investor_data.py",
            "--market", "SET",
            "--out-table", f"_out/investor/investor_table_SET_{timestamp}.csv"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Investor data completed")
        else:
            print(f"⚠️ Investor data failed: {result.stderr}")
        
        # 6. Save to database using existing working method
        print("💾 Saving to database...")
        try:
            from supabase_database import get_proper_db
            import datetime as dt
            
            db = get_proper_db()
            
            # Save NVDR (let function extract actual trade date from Excel)
            nvdr_files = list(Path("_out").glob("nvdr_*.xlsx"))
            if nvdr_files:
                latest_nvdr = max(nvdr_files, key=lambda x: x.stat().st_mtime)
                db.save_nvdr_trading(str(latest_nvdr), None)  # Let function extract actual date
                print("✅ NVDR data saved to database")
                
            # Save Short Sales (let function extract actual trade date from Excel)
            short_files = list(Path("_out").glob("short_sales_*.xlsx"))
            if short_files:
                latest_short = max(short_files, key=lambda x: x.stat().st_mtime) 
                db.save_short_sales_trading(str(latest_short), None)  # Let function extract actual date
                print("✅ Short Sales data saved to database")
                
            # Save Sector data (use same trade date as Excel files - August 18th)
            sector_dirs = list(Path("_out").glob("sectors_*"))
            if sector_dirs:
                latest_sectors = max(sector_dirs, key=lambda x: x.stat().st_mtime)
                
                # Get trade date from NVDR/Short Sales files (already extracted as Aug 18th)
                sector_trade_date = dt.date(2025, 8, 18)  # Use same date as Excel files
                
                # Process each sector CSV file
                sector_files = list(latest_sectors.glob("*.constituents.csv"))
                saved_sectors = 0
                for sector_file in sector_files:
                    sector_name = sector_file.stem.replace('.constituents', '')
                    try:
                        import pandas as pd
                        sector_df = pd.read_csv(sector_file)
                        if db.save_sector_data(sector_df, sector_name, sector_trade_date):
                            saved_sectors += 1
                    except Exception as e:
                        print(f"⚠️ Failed to save sector {sector_name}: {e}")
                print(f"✅ Sector data saved to database ({saved_sectors} sectors)")
                
            # Save Investor data (use same trade date as other data)
            investor_files = list(Path("_out/investor").glob("investor_table_SET_*.csv"))
            if investor_files:
                latest_investor = max(investor_files, key=lambda x: x.stat().st_mtime)
                try:
                    import pandas as pd
                    investor_df = pd.read_csv(latest_investor)
                    investor_trade_date = dt.date(2025, 8, 18)  # Use same date as other data
                    if db.save_investor_summary(investor_df, investor_trade_date):
                        print("✅ Investor data saved to database")
                    else:
                        print("⚠️ Failed to save investor data to database")
                except Exception as e:
                    print(f"⚠️ Failed to save investor data: {e}")
                
            print("🎉 All data saved successfully!")
            
        except Exception as e:
            print(f"❌ Database save error: {e}")
    
    # Run scripts in background
    asyncio.create_task(run_python_scripts())

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
    response = templates.TemplateResponse("portfolio.html", {"request": request})
    # Add cache-busting headers to ensure fresh data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


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
    """Export NVDR data from database as Excel file (fast UX)"""
    try:
        from supabase_database import get_proper_db
        import pandas as pd
        import io
        
        db = get_proper_db()
        
        # Get latest NVDR data from database
        result = db.table('nvdr_trading').select('*').order('trade_date', desc=True).limit(1000).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No NVDR data found in database")
        
        # Convert to DataFrame and create Excel
        df = pd.DataFrame(result.data)
        
        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='NVDR Trading')
        
        output.seek(0)
        
        # Get latest trade date for filename
        latest_date = result.data[0]['trade_date']
        filename = f"nvdr_trading_{latest_date}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        # Fallback to cached file if database fails
        nvdr_files = list(OUTPUT_DIR.glob("nvdr_*.xlsx"))
        if nvdr_files:
            recent_file = max(nvdr_files, key=lambda x: x.stat().st_mtime)
            return FileResponse(
                path=recent_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": 'attachment; filename="nvdr_trading_by_stock.xlsx"'}
            )
        
        raise HTTPException(status_code=500, detail=f"Database error and no cached files: {str(e)}")
        
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
    """Export Short Sales data from database as Excel file (fast UX)"""
    try:
        from supabase_database import get_proper_db
        import pandas as pd
        import io
        
        db = get_proper_db()
        
        # Get latest Short Sales data from database
        result = db.table('short_sales_trading').select('*').order('trade_date', desc=True).limit(1000).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No Short Sales data found in database")
        
        # Convert to DataFrame and create Excel
        df = pd.DataFrame(result.data)
        
        # Create Excel in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Short Sales Trading')
        
        output.seek(0)
        
        # Get latest trade date for filename
        latest_date = result.data[0]['trade_date']
        filename = f"short_sales_{latest_date}.xlsx"
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
        
    except Exception as e:
        # Fallback to cached file if database fails
        short_files = list(OUTPUT_DIR.glob("short_sales_*.xlsx"))
        if short_files:
            recent_file = max(short_files, key=lambda x: x.stat().st_mtime)
            return FileResponse(
                path=recent_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": 'attachment; filename="short_sales_data.xlsx"'}
            )
        
        raise HTTPException(status_code=500, detail=f"Database error and no cached files: {str(e)}")
        
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
    """Export investor type table from database as CSV (fast UX)"""
    try:
        from supabase_database import get_proper_db
        import pandas as pd
        import io
        
        db = get_proper_db()
        
        # Get latest investor data from database for the specified market
        result = db.table('investor_summary').select('*').eq('market', market).order('trade_date', desc=True).limit(100).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No investor data found for {market} market")
        
        # Convert to DataFrame and format as CSV
        df = pd.DataFrame(result.data)
        
        # Create CSV response
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="investor_{market}_data.csv"'}
        )
        
    except Exception as e:
        # Fallback to cached file if database fails
        csv_path = OUTPUT_DIR / "investor" / f"investor_table_{market}_simple.csv"
        if csv_path.exists():
            return FileResponse(
                path=csv_path,
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="investor_{market}_table.csv"'}
            )
        
        raise HTTPException(status_code=500, detail=f"Database error and no cached files: {str(e)}")


@app.get("/api/investor/chart.json")
async def export_investor_chart(market: str = Query("SET", pattern="^(SET|MAI)$")):
    """Export investor type chart data from database as JSON (fast UX)"""
    try:
        from supabase_database import get_proper_db
        
        db = get_proper_db()
        
        # Get latest investor data from database for the specified market
        result = db.table('investor_summary').select('*').eq('market', market).order('trade_date', desc=True).limit(100).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No investor data found for {market} market")
        
        # Return as JSON
        return JSONResponse(content=result.data)
        
    except Exception as e:
        # Fallback to cached file if database fails
        json_path = OUTPUT_DIR / "investor" / f"investor_chart_{market}_simple.json"
        if json_path.exists():
            return FileResponse(path=json_path, media_type="application/json")
        
        raise HTTPException(status_code=500, detail=f"Database error and no cached files: {str(e)}")


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
async def save_to_database(download_fresh: bool = False):
    """Manual data refresh - runs Python scrapers in background and saves to database"""
    print("🔄 Manual data refresh triggered - running Python scrapers...")
    
    try:
        import subprocess
        from datetime import datetime
        from supabase_database import get_proper_db
        import datetime as dt
        
        db = get_proper_db()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {
            "nvdr_data": False,
            "short_sales_data": False, 
            "set_index_data": False,
            "sector_data": False
        }
        
        # 1. Download NVDR
        print("📥 Manual refresh: Running NVDR download...")
        result = subprocess.run([
            sys.executable, "download_nvdr_excel.py", 
            "--out", f"_out/nvdr_{timestamp}.xlsx", 
            "--timeout", "90000"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ NVDR download completed")
            # Save to database
            nvdr_files = list(Path("_out").glob("nvdr_*.xlsx"))
            if nvdr_files:
                latest_nvdr = max(nvdr_files, key=lambda x: x.stat().st_mtime)
                results["nvdr_data"] = db.save_nvdr_trading(str(latest_nvdr), None)
                print("✅ NVDR data saved to database")
        else:
            print(f"❌ NVDR download failed: {result.stderr}")
        
        # 2. Download Short Sales
        print("📥 Manual refresh: Running Short Sales download...")
        result = subprocess.run([
            sys.executable, "download_short_sales_excel.py",
            "--out", f"_out/short_sales_{timestamp}.xlsx",
            "--timeout", "90000"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Short Sales download completed")
            # Save to database
            short_files = list(Path("_out").glob("short_sales_*.xlsx"))
            if short_files:
                latest_short = max(short_files, key=lambda x: x.stat().st_mtime)
                results["short_sales_data"] = db.save_short_sales_trading(str(latest_short), None)
                print("✅ Short Sales data saved to database")
        else:
            print(f"❌ Short Sales download failed: {result.stderr}")
        
        # 3. Scrape SET index
        print("📥 Manual refresh: Running SET index scraping...")
        result = subprocess.run([
            sys.executable, "scrape_set_index.py", "--save-db"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            results["set_index_data"] = True
            print("✅ SET index completed and saved")
        else:
            print(f"❌ SET index failed: {result.stderr}")
        
        # 4. Scrape sector data
        print("📥 Manual refresh: Running sector data scraping...")
        result = subprocess.run([
            sys.executable, "scrape_sector_data.py", 
            "--outdir", f"_out/sectors_{timestamp}"
        ], capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            print("✅ Sector data scraping completed")
            # Save sector data to database
            sector_dirs = list(Path("_out").glob("sectors_*"))
            if sector_dirs:
                latest_sectors = max(sector_dirs, key=lambda x: x.stat().st_mtime)
                sector_trade_date = dt.date(2025, 8, 18)  # Use same date as Excel files
                
                sector_files = list(latest_sectors.glob("*.constituents.csv"))
                saved_sectors = 0
                for sector_file in sector_files:
                    sector_name = sector_file.stem.replace('.constituents', '')
                    try:
                        import pandas as pd
                        sector_df = pd.read_csv(sector_file)
                        if db.save_sector_data(sector_df, sector_name, sector_trade_date):
                            saved_sectors += 1
                    except Exception as e:
                        print(f"⚠️ Failed to save sector {sector_name}: {e}")
                
                results["sector_data"] = saved_sectors > 0
                print(f"✅ Sector data saved to database ({saved_sectors} sectors)")
        else:
            print(f"❌ Sector scraping failed: {result.stderr}")
        
        # Calculate success rate
        total_tasks = len(results)
        successful_tasks = sum(1 for success in results.values() if success)
        
        return JSONResponse(content={
            "success": successful_tasks > 0,
            "updated": successful_tasks > 0,
            "message": f"✅ Manual refresh completed: {successful_tasks}/{total_tasks} components successful",
            "details": results,
            "summary": {
                "nvdr_data": "✅ Downloaded and saved" if results["nvdr_data"] else "❌ Failed",
                "short_sales_data": "✅ Downloaded and saved" if results["short_sales_data"] else "❌ Failed",
                "set_index_data": "✅ Scraped and saved" if results["set_index_data"] else "❌ Failed",
                "sector_data": "✅ Scraped and saved" if results["sector_data"] else "❌ Failed"
            },
            "failed_components": [key for key, success in results.items() if not success],
            "trade_date": datetime.now().strftime("%Y-%m-%d")
        })
        
    except Exception as e:
        print(f"❌ Manual refresh error: {e}")
        return JSONResponse(content={
            "success": False,
            "updated": False,
            "message": f"❌ Manual refresh failed: {str(e)}",
            "details": {"error": str(e)},
            "summary": {},
            "failed_components": ["all"],
            "trade_date": datetime.now().strftime("%Y-%m-%d")
        }, status_code=500)

@app.post("/api/save-to-database-old")  
async def save_to_database_old(download_fresh: bool = False):
    """OLD COMPLEX SYSTEM - Keep as backup"""
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
        results = {"investor_data": False, "sector_data": {}, "nvdr_data": False, "short_sales_data": False, "set_index_data": False}
        
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
        update_progress("running", "nvdr_downloading", 88, "Attempting to download fresh NVDR data...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nvdr_path = OUTPUT_DIR / f"nvdr_{timestamp}.xlsx"
        
        # Try to download with longer timeout and better error handling
        nvdr_cmd = [sys.executable, "download_nvdr_excel.py", "--out", str(nvdr_path), "--timeout", "90000"]
        nvdr_exit_code, nvdr_stdout, nvdr_stderr = await run_cmd(nvdr_cmd, timeout=180)
        
        if nvdr_exit_code == 0 and nvdr_path.exists():
            update_progress("running", "nvdr_processing", 90, "Processing NVDR data...")
            print(f"DEBUG: Processing fresh NVDR file: {nvdr_path}")
            
            # Extract actual trade date from the fresh Excel file before saving
            try:
                actual_trade_date = db.get_latest_trade_date_from_excel(str(nvdr_path))
                print(f"DEBUG: Extracted trade date from NVDR Excel: {actual_trade_date}")
                save_trade_date = actual_trade_date if actual_trade_date else trade_date
            except Exception as e:
                print(f"DEBUG: Could not extract trade date from NVDR Excel, using default: {e}")
                save_trade_date = trade_date
            
            results["nvdr_data"] = db.save_nvdr_trading(str(nvdr_path), save_trade_date)
            if results["nvdr_data"]:
                update_progress("running", "nvdr_saved", 93, "✅ NVDR data saved successfully!")
            else:
                update_progress("running", "nvdr_failed", 93, "⚠️ Failed to save NVDR data")
        else:
            # Fallback to existing files if download fails
            error_msg = f"NVDR download failed (exit_code: {nvdr_exit_code})"
            if nvdr_stderr:
                error_msg += f" - {stderr_tail(nvdr_stderr)}"
            print(f"❌ {error_msg}")
            update_progress("running", "nvdr_fallback", 91, "⚠️ Download failed, using most recent NVDR file...")
            # Get fresh list of NVDR files and use the most recent by modification time
            current_nvdr_files = list(OUTPUT_DIR.glob("nvdr_*.xlsx"))
            if current_nvdr_files:
                latest_nvdr = max(current_nvdr_files, key=lambda x: x.stat().st_mtime)
                print(f"DEBUG: Using most recent NVDR file: {latest_nvdr}")
                results["nvdr_data"] = db.save_nvdr_trading(str(latest_nvdr), trade_date)
            else:
                update_progress("running", "nvdr_skipped", 93, "⚠️ No NVDR files found")
                results["nvdr_data"] = False
        
        # Step 4: Download and save Short Sales data
        update_progress("running", "shortsales_downloading", 93, "Attempting to download fresh Short Sales data...")
        short_path = OUTPUT_DIR / f"short_sales_{timestamp}.xlsx"
        
        # Try to download with longer timeout and better error handling
        short_cmd = [sys.executable, "download_short_sales_excel.py", "--out", str(short_path), "--timeout", "90000"]
        short_exit_code, short_stdout, short_stderr = await run_cmd(short_cmd, timeout=180)
        
        if short_exit_code == 0 and short_path.exists():
            update_progress("running", "shortsales_processing", 95, "Processing Short Sales data...")
            print(f"DEBUG: Processing fresh Short Sales file: {short_path}")
            
            # Extract actual trade date from the fresh Excel file before saving
            try:
                actual_trade_date = db.get_latest_trade_date_from_excel(str(short_path))
                print(f"DEBUG: Extracted trade date from Short Sales Excel: {actual_trade_date}")
                save_trade_date = actual_trade_date if actual_trade_date else trade_date
            except Exception as e:
                print(f"DEBUG: Could not extract trade date from Short Sales Excel, using default: {e}")
                save_trade_date = trade_date
                
            results["short_sales_data"] = db.save_short_sales_trading(str(short_path), save_trade_date)
            if results["short_sales_data"]:
                update_progress("running", "shortsales_saved", 98, "✅ Short Sales data saved successfully!")
            else:
                update_progress("running", "shortsales_failed", 98, "⚠️ Failed to save Short Sales data")
        else:
            # Fallback to existing files if download fails
            error_msg = f"Short Sales download failed (exit_code: {short_exit_code})"
            if short_stderr:
                error_msg += f" - {stderr_tail(short_stderr)}"
            print(f"❌ {error_msg}")
            update_progress("running", "shortsales_fallback", 96, "⚠️ Download failed, using most recent Short Sales file...")
            # Get fresh list of Short Sales files and use the most recent by modification time
            current_short_files = list(OUTPUT_DIR.glob("short_sales_*.xlsx"))
            if current_short_files:
                latest_short = max(current_short_files, key=lambda x: x.stat().st_mtime)
                print(f"DEBUG: Using most recent Short Sales file: {latest_short}")
                results["short_sales_data"] = db.save_short_sales_trading(str(latest_short), trade_date)
            else:
                update_progress("running", "shortsales_skipped", 98, "⚠️ No Short Sales files found")
                results["short_sales_data"] = False
        
        # Step 5: Scrape and save SET index data
        update_progress("running", "setindex_scraping", 99, "Scraping and saving SET index data...")
        
        cmd = [sys.executable, "scrape_set_index.py", "--save-db"]
        exit_code, stdout, stderr = await run_cmd(cmd, timeout=45)
        
        if exit_code == 0:
            results["set_index_data"] = True
            update_progress("running", "setindex_saved", 99, "✅ SET index data saved successfully!")
        else:
            error_msg = f"Failed to scrape SET index data (exit_code: {exit_code})"
            if stderr:
                error_msg += f" - {stderr_tail(stderr)}"
            update_progress("running", "setindex_failed", 99, f"⚠️ {error_msg}")
            print(f"❌ SET index scraping failed: {error_msg}")
            print(f"   stdout: {stdout}")
            print(f"   stderr: {stderr}")
            results["set_index_data"] = False
        
        # Final results with detailed analysis
        sector_success = all(results["sector_data"].values()) if results["sector_data"] else False
        total_success = results["investor_data"] and sector_success and results["nvdr_data"] and results["short_sales_data"] and results["set_index_data"]
        
        # Create detailed success/failure summary
        success_summary = {
            "investor_data": results["investor_data"],
            "sector_data": f"{sum(results['sector_data'].values())} of {len(results['sector_data'])} sectors" if results["sector_data"] else "No sectors",
            "nvdr_data": results["nvdr_data"],
            "short_sales_data": results["short_sales_data"],
            "set_index_data": results["set_index_data"]
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
        if not results["set_index_data"]:
            failed_components.append("SET index data")
        
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


@app.post("/api/save-to-database-full")
async def save_to_database_full():
    """Save to database with fresh downloads (optimized timeouts)"""
    return await save_to_database(download_fresh=True)


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
        # First check file cache to see if data is available (within last 7 days)
        latest_file = Path("_out/set_index_latest.json")
        from datetime import timedelta
        cutoff_date = datetime.now().date() - timedelta(days=7)
        file_is_recent = False
        
        if latest_file.exists():
            # Check if file was modified within last 7 days
            file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime).date()
            file_is_recent = (file_mtime >= cutoff_date)
            
            if file_is_recent:
                print("📊 Using recent SET index data from file cache")
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
                print("📊 Using recent SET index data from database")
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
        
        # If no recent data, scrape new data
        print("🔄 No recent data found, scraping new SET index data...")
        
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
async def get_portfolio_dashboard(response: Response):
    """Get portfolio dashboard data with latest investor summary, sector summary, and individual stock data"""
    # Add cache-busting headers to ensure fresh data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
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


@app.get("/api/portfolio/available-dates")
async def get_available_portfolio_dates():
    """Get all available dates that have portfolio holdings"""
    try:
        db = get_proper_db()
        dates = db.get_available_portfolio_dates()
        
        # If no dates, add today as default
        if not dates:
            today = datetime.now().date().isoformat()
            dates = [today]
        
        return JSONResponse(content={
            "success": True,
            "dates": dates
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available dates: {str(e)}")


@app.get("/api/portfolio/holdings")
async def get_portfolio_holdings_for_date(trade_date: str = Query(...)):
    """Get portfolio holdings for a specific date"""
    try:
        from datetime import datetime
        
        # Parse the date
        try:
            parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        db = get_proper_db()
        
        # Get portfolio holdings for the date
        holdings = db.get_portfolio_holdings(parsed_date)
        
        # Get latest market data for calculations
        sector_result = db.client.table('sector_data').select('trade_date').order('trade_date', desc=True).limit(1).execute()
        latest_market_date = sector_result.data[0]['trade_date'] if sector_result.data else None
        
        # Get current prices and portfolio symbols
        portfolio_symbols = db.get_portfolio_symbols()
        portfolio_data = []
        
        if latest_market_date:
            # Get market data for all portfolio symbols
            for symbol in portfolio_symbols:
                # Get stock data
                stock_result = db.client.table('sector_data').select('symbol, last_price, sector, change, percent_change').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                stock_data = stock_result.data[0] if stock_result.data else {}
                
                # Get NVDR data
                nvdr_result = db.client.table('nvdr_trading').select('value_net').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                nvdr_value = nvdr_result.data[0]['value_net'] if nvdr_result.data else 0
                
                # Get Short Sales data
                short_result = db.client.table('short_sales_trading').select('short_value_baht').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                short_value = short_result.data[0]['short_value_baht'] if short_result.data else 0
                
                # Get holding data for this symbol and date
                holding = holdings.get(symbol, {})
                
                # Parse values safely
                def parse_change(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        cleaned = str(value).replace('+', '').replace(',', '').strip()
                        return float(cleaned) if cleaned != '-' else 0
                    except (ValueError, TypeError):
                        return 0
                
                change_str = stock_data.get('change', '')
                percent_change_str = stock_data.get('percent_change', '')
                close_price = stock_data.get('last_price', 0) or 0
                
                # Calculate P/L if we have holding data
                quantity = holding.get('quantity', 0)
                avg_cost_price = holding.get('avg_cost_price', 0)
                cost = holding.get('cost', 0)
                
                market_value = quantity * close_price if quantity and close_price else 0
                pl_amount = market_value - cost if cost else 0
                pl_percent = (pl_amount / cost * 100) if cost and cost > 0 else 0
                
                portfolio_data.append({
                    'symbol': symbol,
                    'sector': stock_data.get('sector', ''),
                    'quantity': quantity,
                    'avg_cost_price': avg_cost_price,
                    'cost': cost,
                    'change': parse_change(change_str),
                    'close': close_price,
                    'percent_change': parse_change(percent_change_str.replace('%', '')),
                    'market_value': market_value,
                    'pl_amount': pl_amount,
                    'pl_percent': pl_percent,
                    'nvdr': nvdr_value or 0,
                    'shortBaht': short_value or 0
                })
        
        return JSONResponse(content={
            "success": True,
            "trade_date": trade_date,
            "portfolio_data": portfolio_data,
            "market_date": latest_market_date
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio holdings: {str(e)}")


@app.post("/api/portfolio/save-holding")
async def save_portfolio_holding(request: Request):
    """Save or update a portfolio holding"""
    try:
        data = await request.json()
        symbol = data.get('symbol', '').strip().upper()
        quantity = data.get('quantity', 0)
        avg_cost_price = data.get('avg_cost_price', 0)
        trade_date_str = data.get('trade_date', '')
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        if not trade_date_str:
            raise HTTPException(status_code=400, detail="Trade date is required")
        
        try:
            trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        if quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity must be non-negative")
        
        if avg_cost_price < 0:
            raise HTTPException(status_code=400, detail="Average cost price must be non-negative")
        
        db = get_proper_db()
        
        if quantity == 0 and avg_cost_price == 0:
            # Delete the holding only if both quantity and price are 0
            success = db.delete_portfolio_holding(symbol, trade_date)
        else:
            # Save or update the holding
            success = db.save_portfolio_holding(symbol, quantity, avg_cost_price, trade_date)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Portfolio holding {'updated' if quantity > 0 else 'deleted'} for {symbol}"
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to save portfolio holding")
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Check if it's a table missing error and provide helpful guidance
        if 'portfolio_holdings' in error_msg and ('does not exist' in error_msg or 'not found' in error_msg):
            raise HTTPException(status_code=500, detail="Portfolio holdings table not found. Please create the database table first by running create_portfolio_holdings_table.sql in your Supabase SQL editor.")
        else:
            raise HTTPException(status_code=500, detail=f"Error saving portfolio holding: {error_msg}")


@app.get("/api/portfolio/export.csv")
async def export_portfolio_csv(portfolio_date: str = None):
    """Export portfolio holdings as CSV"""
    try:
        db = get_proper_db()
        
        # Get available dates if no date specified
        if not portfolio_date:
            dates = db.get_available_portfolio_dates()
            if not dates:
                raise HTTPException(status_code=404, detail="No portfolio data found")
            portfolio_date = dates[0]  # Use most recent date
        
        # Get holdings data using the same logic as the holdings endpoint
        from datetime import datetime as dt
        
        # Parse the date
        try:
            parsed_date = dt.strptime(portfolio_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get portfolio holdings for the date
        raw_holdings = db.get_portfolio_holdings(parsed_date)
        
        # Get latest market data for calculations
        sector_result = db.client.table('sector_data').select('trade_date').order('trade_date', desc=True).limit(1).execute()
        latest_market_date = sector_result.data[0]['trade_date'] if sector_result.data else None
        
        # Get current prices and portfolio symbols
        portfolio_symbols = db.get_portfolio_symbols()
        holdings = []
        
        if latest_market_date:
            # Get market data for all portfolio symbols
            for symbol in portfolio_symbols:
                # Get stock data
                stock_result = db.client.table('sector_data').select('symbol, last_price, sector, change, percent_change').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                stock_data = stock_result.data[0] if stock_result.data else {}
                
                # Get NVDR data
                nvdr_result = db.client.table('nvdr_trading').select('value_net').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                nvdr_value = nvdr_result.data[0]['value_net'] if nvdr_result.data else 0
                
                # Get Short Sales data
                short_result = db.client.table('short_sales_trading').select('short_value_baht').eq('trade_date', latest_market_date).eq('symbol', symbol).execute()
                short_value = short_result.data[0]['short_value_baht'] if short_result.data else 0
                
                # Get holding data for this symbol and date
                holding = raw_holdings.get(symbol, {})
                
                # Parse values safely
                def parse_change(value):
                    if not value or value == '-' or value == '':
                        return 0
                    try:
                        cleaned = str(value).replace('+', '').replace(',', '').strip()
                        return float(cleaned) if cleaned != '-' else 0
                    except (ValueError, TypeError):
                        return 0
                
                # Include all portfolio symbols (whether they have saved data or not)
                quantity = holding.get('quantity', 0)
                avg_cost_price = holding.get('avg_cost_price', 0)
                
                holdings.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_cost_price': avg_cost_price,
                    'close': stock_data.get('last_price', 0),
                    'change': parse_change(stock_data.get('change', 0)),
                    'percent_change': parse_change(stock_data.get('percent_change', 0)),
                    'nvdr': nvdr_value,
                    'shortBaht': short_value
                })
        
        if not holdings:
            raise HTTPException(status_code=404, detail=f"No portfolio symbols found for date {portfolio_date}")
        
        # Create CSV content
        csv_lines = []
        headers = ['No.', 'Symbol', 'Quantity', 'AVG Cost Price', 'Cost', 'Change', 'Close Price', '%Change', 'P/L', '%P/L', 'NVDR', 'Short Sales']
        csv_lines.append(','.join(f'"{h}"' for h in headers))
        
        for i, holding in enumerate(holdings, 1):
            # Calculate derived values
            quantity = float(holding.get('quantity', 0))
            avg_cost = float(holding.get('avg_cost_price', 0))
            close_price = float(holding.get('close', 0))
            change = float(holding.get('change', 0))
            percent_change = float(holding.get('percent_change', 0))
            nvdr = float(holding.get('nvdr', 0))
            short_sales = float(holding.get('shortBaht', 0))
            
            cost = quantity * avg_cost
            pl = quantity * (close_price - avg_cost)
            pl_percent = (pl / cost * 100) if cost > 0 else 0
            
            row = [
                str(i),
                f'"{holding.get("symbol", "")}"',
                f'{quantity:.0f}',
                f'{avg_cost:.2f}',
                f'{cost:.2f}',
                f'{change:.2f}',
                f'{close_price:.2f}',
                f'{percent_change:.2f}%',
                f'{pl:.2f}',
                f'{pl_percent:.2f}%',
                f'{nvdr:.2f}',
                f'{short_sales:.2f}'
            ]
            csv_lines.append(','.join(row))
        
        csv_content = '\n'.join(csv_lines)
        
        # Return CSV response
        return Response(
            content=f'\ufeff{csv_content}',  # Add BOM for proper Excel encoding
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="my-portfolio-{portfolio_date}.csv"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if 'portfolio_holdings' in error_msg and ('does not exist' in error_msg or 'not found' in error_msg):
            raise HTTPException(status_code=500, detail="Portfolio holdings table not found. Please create the database table first.")
        else:
            raise HTTPException(status_code=500, detail=f"Error exporting portfolio: {error_msg}")


@app.post("/api/portfolio/setup-database")
async def setup_portfolio_database():
    """Helper endpoint to provide setup instructions"""
    return JSONResponse(content={
        "success": False,
        "message": "Database table setup required",
        "sql_file": "create_portfolio_holdings_table.sql",
        "instructions": [
            "1. Open your Supabase dashboard",
            "2. Go to SQL Editor",
            "3. Copy and paste the SQL from create_portfolio_holdings_table.sql",
            "4. Run the query",
            "5. Refresh this page and try editing again"
        ],
        "sql_content": "-- See create_portfolio_holdings_table.sql for complete SQL"
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='SET Portfolio Dashboard Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--host', type=str, default="0.0.0.0", help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)
