#!/usr/bin/env python3
"""
SET Data Export API - FastAPI backend for Vercel deployment

This is a Vercel-compatible version of the main application with:
- Removed Playwright dependencies (not supported on Vercel)
- Optimized for serverless environment
- Simplified file operations
"""

import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple
import json

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import pandas as pd
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import database functions
try:
    from supabase_database import get_proper_db
    HAS_DB = True
except ImportError:
    HAS_DB = False
    print("Warning: Database module not available")

import requests
try:
    import yfinance as yf
    HAS_YF = True
except Exception:
    HAS_YF = False
    print("Warning: yfinance not available")

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

# Create output directories (for Vercel, use /tmp)
OUTPUT_DIR = Path("/tmp/_out") if os.environ.get("VERCEL") else Path("_out")
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "investor").mkdir(exist_ok=True)


def ts_name(prefix: str, ext: str) -> str:
    """Generate timestamped filename like prefix_YYYYMMDD_HHMMSS.ext"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{ext}"


def ensure_dir(path: Path) -> None:
    """Ensure directory exists, create if needed"""
    path.mkdir(parents=True, exist_ok=True)


def update_progress(status: str, step: str, progress: int, message: str, details: dict = None):
    """Update global progress data"""
    global progress_data
    progress_data.update({
        "status": status,
        "step": step,
        "progress": progress,
        "message": message,
        "details": details or {}
    })


@app.get("/")
async def root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/portfolio")
async def portfolio_page(request: Request):
    """Portfolio dashboard page"""
    return templates.TemplateResponse("portfolio.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": "vercel"
    }


@app.get("/api/progress")
async def get_progress():
    """Get current progress status"""
    return progress_data


@app.get("/api/symbol/{symbol}")
async def get_symbol_data(symbol: str):
    """Get stock data for a specific symbol using yfinance"""
    if not HAS_YF:
        raise HTTPException(status_code=503, detail="yfinance not available")
    
    try:
        with yfinance_lock:
            ticker = yf.Ticker(f"{symbol}.BK")
            info = ticker.info
            
            # Get historical data for the last 30 days
            hist = ticker.history(period="30d")
            
            if hist.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            change = latest['Close'] - prev['Close']
            change_percent = (change / prev['Close']) * 100 if prev['Close'] > 0 else 0
            
            # Prepare chart data
            chart_data = []
            for date, row in hist.iterrows():
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            return {
                'symbol': symbol,
                'latest': {
                    'close': float(latest['Close']),
                    'change': float(change),
                    'change_percent': float(change_percent),
                    'volume': int(latest['Volume']),
                    'date': latest.name.strftime('%Y-%m-%d')
                },
                'info': {
                    'name': info.get('longName', symbol),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'market_cap': info.get('marketCap', 0)
                },
                'chart_data': chart_data
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data for {symbol}: {str(e)}")


@app.get("/api/symbol/{symbol}/series")
async def get_symbol_series(symbol: str):
    """Get time series data for a symbol"""
    return await get_symbol_data(symbol)


@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio data - simplified for Vercel"""
    try:
        # For Vercel deployment, return a simplified portfolio structure
        # In production, you would integrate with your database
        
        portfolio_symbols = ["PTT", "SCB", "CPALL", "ADVANC", "AOT"]
        
        portfolio_stocks = []
        for symbol in portfolio_symbols:
            try:
                # Get data for each symbol
                symbol_data = await get_symbol_data(symbol)
                latest = symbol_data['latest']
                
                portfolio_stocks.append({
                    'symbol': symbol,
                    'close': latest['close'],
                    'change': latest['change'],
                    'percent_change': latest['change_percent'],
                    'sector': symbol_data['info']['sector'],
                    'nvdr': 0,  # Placeholder - would come from database
                    'shortBaht': 0,  # Placeholder - would come from database
                })
            except Exception as e:
                print(f"Error getting data for {symbol}: {e}")
                # Add placeholder data
                portfolio_stocks.append({
                    'symbol': symbol,
                    'close': 0,
                    'change': 0,
                    'percent_change': 0,
                    'sector': '',
                    'nvdr': 0,
                    'shortBaht': 0,
                })
        
        return JSONResponse(content={
            'portfolio_symbols': portfolio_symbols,
            'portfolio_stocks': portfolio_stocks,
            'trade_date': datetime.now().strftime('%Y-%m-%d')
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
        symbol_data = await get_symbol_data(symbol)
        latest_data = symbol_data['latest']
        
        if latest_data['close'] > 0:
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
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating symbol data: {str(e)}")


# Note: Excel download endpoints are disabled for Vercel deployment
# as they require Playwright which is not supported in serverless environments

@app.get("/api/status")
async def get_status():
    """Get application status and capabilities"""
    return {
        "status": "running",
        "environment": "vercel",
        "capabilities": {
            "yfinance": HAS_YF,
            "database": HAS_DB,
            "excel_downloads": False,  # Disabled on Vercel
            "web_scraping": True
        },
        "timestamp": datetime.now().isoformat()
    }


# For local development
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
