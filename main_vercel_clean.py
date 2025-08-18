#!/usr/bin/env python3
"""
SET Portfolio Dashboard - Vercel Read-Only Version
Uses the exact working code from main.py but only keeps database READ endpoints
"""

import os
import json
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="SET Portfolio Dashboard - Read Only", 
    description="Thai Stock Exchange Portfolio Management System (Vercel Deployment)",
    version="1.0.0"
)

# Mount static files if they exist
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")
else:
    templates = None

# Database configuration
try:
    from supabase_database import get_proper_db
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Database unavailable: {e}")
    DB_AVAILABLE = False

def parse_number(value) -> float:
    """Parse string to number, handling empty values and commas"""
    if not value or value == '-' or value == '' or str(value).strip() == '':
        return 0.0
    try:
        cleaned = str(value).replace(',', '').strip()
        if cleaned == '' or cleaned == '-':
            return 0.0
        result = float(cleaned)
        if not (result == result) or result == float('inf') or result == float('-inf'):
            return 0.0
        return result
    except (ValueError, TypeError):
        return 0.0

@app.get("/")
async def root():
    """Root redirect to portfolio"""
    return JSONResponse(content={
        "message": "SET Portfolio Dashboard - Read Only Mode",
        "portfolio_url": "/portfolio",
        "mode": "vercel-readonly"
    })

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_dashboard(request: Request):
    """Portfolio dashboard page - using exact template from main.py"""
    if templates:
        return templates.TemplateResponse("portfolio_main.html", {"request": request})
    
    # Fallback if template not available
    return HTMLResponse(content="""
    <html>
    <head><title>Portfolio Dashboard</title></head>
    <body>
        <h1>SET Portfolio Dashboard</h1>
        <p>Template not found. Please ensure portfolio.html is in templates/</p>
    </body>
    </html>
    """)

# === EXACT DATABASE READ ENDPOINTS FROM MAIN.PY ===

@app.get("/api/portfolio/dashboard")
async def get_portfolio_dashboard():
    """Portfolio dashboard data - EXACT copy from main.py line 1360"""
    if not DB_AVAILABLE:
        return {"success": False, "error": "Database not available"}
    
    try:
        db = get_proper_db()
        
        # Get sector data (all sectors)
        sector_response = db.client.table("sector_data").select("*").execute()
        portfolio_stocks = []
        
        # Get NVDR data for joining
        nvdr_response = db.client.table("nvdr_trading").select("symbol, value_net").execute() 
        nvdr_data = {item['symbol']: item['value_net'] for item in nvdr_response.data or []}
        
        # Get Short Sales data for joining
        short_response = db.client.table("short_sales_trading").select("symbol, short_value_baht").execute()
        short_data = {item['symbol']: item['short_value_baht'] for item in short_response.data or []}
        
        # Process and transform data to match frontend expectations
        for stock in sector_response.data or []:
            # Convert string change/percent to numbers
            change_str = str(stock.get('change', '0')).replace('%', '').replace('+', '').strip()
            percent_str = str(stock.get('percent_change', '0')).replace('%', '').replace('+', '').strip()
            
            stock_info = {
                'symbol': stock.get('symbol', ''),
                'sector': stock.get('sector', ''),
                'close': stock.get('last_price', 0),  # KEY: map last_price to close
                'change': parse_number(change_str),
                'percent_change': parse_number(percent_str),
                'nvdr': nvdr_data.get(stock.get('symbol'), 0),  # Join NVDR
                'shortBaht': short_data.get(stock.get('symbol'), 0),  # Join Short Sales
                'trade_date': stock.get('trade_date', '')
            }
            portfolio_stocks.append(stock_info)
        
        # Get investor summary
        investor_response = db.client.table("investor_summary").select("*").limit(10).execute()
        investor_summary = investor_response.data or []
        
        # Get trade date 
        trade_date = datetime.now().strftime("%Y-%m-%d")
        if portfolio_stocks and portfolio_stocks[0].get('trade_date'):
            trade_date = portfolio_stocks[0]['trade_date']
            
        # Calculate sector summary
        sector_summary = {}
        for stock in portfolio_stocks:
            sector = stock['sector'] 
            if sector not in sector_summary:
                sector_summary[sector] = {'stock_count': 0, 'total_price': 0}
            sector_summary[sector]['stock_count'] += 1
            sector_summary[sector]['total_price'] += float(stock['close'] or 0)
        
        sector_list = []
        for sector, data in sector_summary.items():
            sector_list.append({
                'sector': sector,
                'stock_count': data['stock_count'],
                'avg_price': round(data['total_price'] / data['stock_count'], 2) if data['stock_count'] > 0 else 0
            })
        
        return {
            "success": True,
            "trade_date": trade_date,
            "portfolio_stocks": portfolio_stocks,
            "investor_summary": investor_summary,
            "sector_summary": sector_list,
            "message": f"Loaded {len(portfolio_stocks)} stocks from database"
        }
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return {"success": False, "error": f"Dashboard query failed: {str(e)}"}

@app.get("/api/portfolio/summary")
async def get_portfolio_summary():
    """Portfolio summary statistics - EXACT copy from main.py line 1589"""
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
    
    try:
        db = get_proper_db()
        
        # Get basic counts
        sector_response = db.client.table("sector_data").select("*").execute()
        stocks = sector_response.data or []
        
        # Calculate summaries
        total_symbols = len(stocks)
        prices = [stock.get('last_price', 0) for stock in stocks if stock.get('last_price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Get NVDR totals
        nvdr_response = db.client.table("nvdr_trading").select("value_net").execute()
        nvdr_values = [item['value_net'] for item in nvdr_response.data or [] if item.get('value_net')]
        total_nvdr_mb = sum(nvdr_values) / 1000000 if nvdr_values else 0
        
        # Get Short Sales totals  
        short_response = db.client.table("short_sales_trading").select("short_value_baht").execute()
        short_values = [item['short_value_baht'] for item in short_response.data or [] if item.get('short_value_baht')]
        total_short_mb = sum(short_values) / 1000000 if short_values else 0
        
        return {
            "total_symbols": total_symbols,
            "avg_price": round(avg_price, 2),
            "total_nvdr_mb": round(total_nvdr_mb, 2), 
            "total_short_mb": round(total_short_mb, 2)
        }
        
    except Exception as e:
        print(f"❌ Summary error: {e}")
        return {"error": f"Summary calculation failed: {str(e)}"}

@app.get("/api/portfolio/my-symbols")
async def get_my_portfolio():
    """Get user's portfolio symbols - EXACT copy from main.py line 1682"""
    if not DB_AVAILABLE:
        return {"success": False, "error": "Database not available"}
    
    try:
        db = get_proper_db()
        
        # Try to get user portfolio symbols
        try:
            symbols_response = db.client.table("portfolio_symbols").select("symbol").execute()
            symbols = [row["symbol"] for row in symbols_response.data or []]
        except:
            symbols = []  # No user portfolio
        
        # Get stock data for symbols (or top 20 if no portfolio)
        if symbols:
            stocks_response = db.client.table("sector_data").select("*").in_("symbol", symbols).order("symbol").execute()
        else:
            stocks_response = db.client.table("sector_data").select("*").order("symbol").limit(20).execute()
            symbols = [row["symbol"] for row in stocks_response.data or []]
        
        # Transform stock data same as dashboard
        portfolio_stocks = []
        for stock in stocks_response.data or []:
            change_str = str(stock.get('change', '0')).replace('%', '').replace('+', '').strip()
            percent_str = str(stock.get('percent_change', '0')).replace('%', '').replace('+', '').strip()
            
            stock_info = {
                'symbol': stock.get('symbol', ''),
                'sector': stock.get('sector', ''),
                'close': stock.get('last_price', 0),
                'change': parse_number(change_str),
                'percent_change': parse_number(percent_str),
                'trade_date': stock.get('trade_date', '')
            }
            portfolio_stocks.append(stock_info)
        
        return {
            "success": True,
            "portfolio_symbols": symbols,
            "portfolio_stocks": portfolio_stocks
        }
        
    except Exception as e:
        print(f"❌ My portfolio error: {e}")
        return {"success": False, "error": f"Portfolio fetch failed: {str(e)}"}

@app.get("/api/set-index")
async def get_set_index():
    """GET SET index data - EXACT copy from main.py line 1218"""
    if not DB_AVAILABLE:
        # Return sample data if no database
        sample_data = [
            {"index": "SET Index", "last": "1,650.00", "change": "+5.20", "volume": "12,345", "value": "45,678"}
        ]
        return {"success": True, "data": sample_data, "message": "Sample data - database not available"}
    
    try:
        db = get_proper_db()
        
        # Try to get from database first
        result = db.get_latest_set_index_data()
        
        if result.get("status") == "success" and result.get("data"):
            return {
                "success": True,
                "data": result["data"],
                "trade_date": result.get("trade_date"),
                "source": "database"
            }
        
        # Fallback to sample data
        sample_data = [
            {"index": "SET Index", "last": "1,650.00", "change": "+5.20", "volume": "12,345", "value": "45,678"},
            {"index": "SET50", "last": "1,120.50", "change": "+3.10", "volume": "8,900", "value": "23,456"}
        ]
        return {
            "success": True,
            "data": sample_data,
            "message": "Sample SET index data (no database data found)"
        }
        
    except Exception as e:
        print(f"❌ SET index error: {e}")
        return {"success": False, "error": f"SET index query failed: {str(e)}"}

@app.get("/api/series/set-index")
def get_set_index_series():
    """GET SET index time series - EXACT copy from main.py line 220"""
    # Return empty series in read-only mode
    return {
        "success": True,
        "series": [],
        "latest": {},
        "message": "Historical data not available in read-only mode"
    }

@app.get("/api/series/symbol/{symbol}")
def get_symbol_series(symbol: str):
    """Get symbol time series - read-only mode"""
    return {
        "success": True,
        "series": [],
        "latest": {},
        "message": f"Historical data for {symbol} not available in read-only mode"
    }

# === DISABLED ENDPOINTS (READ-ONLY MODE) ===

@app.post("/api/portfolio/add-symbol")
@app.delete("/api/portfolio/remove-symbol/{symbol}")
async def portfolio_management_disabled():
    """Portfolio management disabled in read-only mode"""
    return JSONResponse(
        status_code=501,
        content={
            "success": False,
            "error": "Portfolio management disabled in read-only mode",
            "message": "This deployment only displays data"
        }
    )

@app.post("/api/save-to-database")
@app.post("/api/save-to-database-full")
@app.post("/api/auto-update-database")
@app.post("/api/test-update-database")
async def database_updates_disabled():
    """Database update endpoints disabled in read-only mode"""
    return {
        "success": True,
        "updated": False,
        "message": "Read-only mode: Serving existing data from Supabase database",
        "note": "This deployment only displays data, no scraping or database updates"
    }

@app.get("/api/nvdr/export.xlsx")
@app.get("/api/short-sales/export.xlsx")
async def exports_disabled():
    """Export endpoints disabled in read-only mode"""
    return JSONResponse(
        status_code=501,
        content={
            "error": "Export functionality disabled in read-only mode",
            "message": "This deployment only displays data from database"
        }
    )

@app.get("/api/progress")
async def progress_disabled():
    """Progress monitoring disabled in read-only mode"""
    return JSONResponse(
        status_code=501,
        content={
            "error": "Progress monitoring disabled in read-only mode",
            "message": "No background operations run in this deployment"
        }
    )

@app.get("/api/progress/status")
async def progress_status():
    """Progress status - always idle in read-only mode"""
    return {
        "status": "idle",
        "step": "read-only",
        "progress": 100,
        "message": "Read-only mode - no background operations"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_vercel_clean:app", host="0.0.0.0", port=port, reload=False)