#!/usr/bin/env python3
"""
SET/MAI Investor Type Scraper using Jina.ai Public Proxy

Quickstart:
    pip install requests beautifulsoup4
    python scrape_investor_type_simple.py --market SET
    python scrape_investor_type_simple.py --market MAI --out-table mai_data.csv
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date

import requests
from bs4 import BeautifulSoup


def setup_cli() -> argparse.Namespace:
    """Setup command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Scrape SET/MAI Investor Type data using Jina.ai public proxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scrape_investor_type_simple.py --market SET
    python scrape_investor_type_simple.py --market MAI --out-table mai_data.csv
    python scrape_investor_type_simple.py --market SET --timeout 30
        """
    )
    
    parser.add_argument(
        "--market",
        choices=["SET", "MAI"],
        default="SET",
        help="Market to scrape (default: SET)"
    )
    
    parser.add_argument(
        "--out-table",
        type=str,
        help="Output CSV file path (default: investor_table_<MARKET>_simple.csv)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save data to database after scraping"
    )
    
    return parser.parse_args()


def scrape_with_jina_proxy(url: str, timeout: int) -> str:
    """Scrape the page using Jina.ai public proxy."""
    proxy_url = f"https://r.jina.ai/{url}"
    print(f"Scraping {url} via Jina.ai public proxy...")
    
    try:
        response = requests.get(
            proxy_url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error calling Jina.ai proxy: {e}")
        sys.exit(1)


def extract_table_from_html(html: str) -> Optional[Dict[str, Any]]:
    """Extract table data from HTML/markdown content."""
    # Check if this is markdown content from Jina.ai
    if "Markdown Content:" in html:
        print("Detected Jina.ai markdown format")
        return extract_table_from_markdown(html)
    else:
        print("Detected HTML format")
        return extract_table_from_html_raw(html)


def extract_table_from_markdown(content: str) -> Optional[Dict[str, Any]]:
    """Extract table data from Jina.ai markdown format - following VBA logic."""
    lines = split_to_lines(content)
    
    # Find "As of" date and parse it
    as_of = ""
    trade_date = None
    for line in lines:
        if line.lower().startswith("as of"):
            as_of = line[6:].strip()
            # Parse the date to extract actual trade date
            trade_date = parse_as_of_date(as_of)
            break
    
    print(f"As of: {as_of}")
    if trade_date:
        print(f"📅 Parsed trade date: {trade_date}")
    
    # Find the big 16-column header row (like VBA)
    header_idx = -1
    header_needle = "| Type | Buy | % | Sell | % | Net | Buy | % | Sell | % | Net | Buy | % | Sell | % | Net |"
    
    for i, line in enumerate(lines):
        if header_needle.lower() in line.lower():
            header_idx = i
            break
    
    if header_idx == -1:
        print("Could not find header row")
        return None
    
    print(f"Found header at line {header_idx}")
    
    # Get period labels from row above header
    daily_lbl, mtd_lbl, ytd_lbl = find_label_row_above(lines, header_idx)
    print(f"Periods: Daily={daily_lbl}, MTD={mtd_lbl}, YTD={ytd_lbl}")
    
    # Collect the 4 investor rows (like VBA)
    rows = []
    want = ["Local Institutions", "Proprietary Trading", "Foreign Investors", "Local Individuals"]
    found = 0
    
    for i in range(header_idx + 1, min(len(lines), header_idx + 40)):
        line = lines[i].strip()
        
        if not line.startswith("|"):
            break
        
        if is_separator_row(line):
            continue
        
        cells = split_md_row(line)
        if len(cells) < 16:
            continue
        
        investor_type = cells[0]
        if investor_type not in want:
            continue
        
        found += 1
        print(f"Found investor type: {investor_type}")
        
        # Parse the row data (16 columns: Type + 3x5 fields)
        row_data = [investor_type]
        
        # Daily (columns 1-5)
        row_data.extend([str(to_num(cells[1])), str(to_num(cells[2])), str(to_num(cells[3])), str(to_num(cells[4])), str(to_num(cells[5]))])
        
        # MTD (columns 6-10)
        row_data.extend([str(to_num(cells[6])), str(to_num(cells[7])), str(to_num(cells[8])), str(to_num(cells[9])), str(to_num(cells[10]))])
        
        # YTD (columns 11-15)
        row_data.extend([str(to_num(cells[11])), str(to_num(cells[12])), str(to_num(cells[13])), str(to_num(cells[14])), str(to_num(cells[15]))])
        
        rows.append(row_data)
        
        if found == 4:
            break
    
    if found == 4:
        # Create headers based on VBA structure
        headers = ["Type"] + ["Buy", "%", "Sell", "%", "Net"] * 3  # 3 periods
        return {
            "headers": headers,
            "rows": rows,
            "as_of": as_of,
            "trade_date": trade_date,
            "daily_lbl": daily_lbl,
            "mtd_lbl": mtd_lbl,
            "ytd_lbl": ytd_lbl
        }
    
    print(f"Only found {found} investor types, expected 4")
    return None


def split_to_lines(raw: str) -> List[str]:
    """Split text into lines, removing empty lines (like VBA)."""
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return [line.strip() for line in lines if line.strip()]


def split_md_row(s: str) -> List[str]:
    """Split markdown row by | separators (like VBA)."""
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    
    parts = s.split("|")
    return [part.strip() for part in parts if part.strip()]


def is_separator_row(s: str) -> bool:
    """Check if row is a separator (like VBA)."""
    t = s.replace("|", "").replace("-", "").replace(" ", "")
    return len(t) == 0


def find_label_row_above(lines: List[str], header_idx: int) -> tuple:
    """Find the label row above header (like VBA)."""
    for j in range(header_idx - 1, max(0, header_idx - 8), -1):
        s = lines[j].strip()
        if s.startswith("|") and not is_separator_row(s):
            cells = split_md_row(s)
            if len(cells) >= 3:
                return cells[-3], cells[-2], cells[-1]  # Last 3 cells
    
    return "Daily", "Month-to-Date", "Year-to-Date"


def parse_as_of_date(as_of: str) -> Optional[date]:
    """Parse 'As of' date string to date object"""
    if not as_of:
        return None
    
    try:
        from datetime import datetime
        # Try different formats
        formats = [
            "%d %b %Y",      # "21 Aug 2025"
            "%d %B %Y",      # "21 August 2025"
            "%B %d, %Y",     # "August 21, 2025"
            "%Y-%m-%d",      # "2025-08-21"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(as_of.strip(), fmt).date()
            except ValueError:
                continue
        
        print(f"⚠️ Could not parse date: {as_of}")
        return None
    except Exception as e:
        print(f"⚠️ Date parsing error: {e}")
        return None


def to_num(s: str) -> float:
    """Convert string to number (like VBA)."""
    if not s:
        return 0.0
    
    # Handle Unicode minus and other special characters
    t = s.replace('\u2212', '-')  # Unicode minus
    t = t.replace('–', '-')       # En dash
    t = t.replace(',', '')        # Remove commas
    
    try:
        return float(t)
    except ValueError:
        return 0.0


def extract_table_from_html_raw(html: str) -> Optional[Dict[str, Any]]:
    """Extract table data from raw HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the page")
    
    for i, table in enumerate(tables):
        print(f"Checking table {i+1}...")
        
        # Extract headers
        headers = []
        header_row = table.find('thead')
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
        else:
            # Try first row as header
            first_row = table.find('tr')
            if first_row:
                header_cells = first_row.find_all(['th', 'td'])
                headers = [cell.get_text(strip=True) for cell in header_cells]
        
        if headers:
            print(f"  Headers: {headers}")
            
            # Check if this looks like an investor table
            header_text = " ".join(headers).lower()
            thai_keywords = ["ซื้อ", "ขาย", "สุทธิ", "นักลงทุน"]
            english_keywords = ["buy", "sell", "net", "investor"]
            
            if any(keyword in header_text for keyword in thai_keywords + english_keywords):
                print(f"  Found investor table with {len(headers)} columns")
                
                # Extract rows
                rows = []
                body_rows = table.find_all('tr')[1:] if header_row else table.find_all('tr')
                
                for row in body_rows:
                    cells = row.find_all(['th', 'td'])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        if any(cell.strip() for cell in row_data):  # Skip empty rows
                            rows.append(row_data)
                
                print(f"  Found {len(rows)} data rows")
                
                if rows:
                    return {
                        "headers": headers,
                        "rows": rows
                    }
    
    return None


def parse_investor_data_lines(lines: List[str]) -> Optional[Dict[str, Any]]:
    """Parse investor data from text lines."""
    headers = ["นักลงทุน", "ข้อมูล"]
    rows = []
    
    for line in lines:
        # Try to extract investor type and data
        for keyword in ["สถาบันการเงิน", "ต่างชาติ", "บุคคลธรรมดา", "บริษัทหลักทรัพย์", "รวม"]:
            if keyword in line:
                # Extract the data after the keyword
                parts = line.split(keyword)
                if len(parts) > 1:
                    data = parts[1].strip()
                    rows.append([keyword, data])
                    break
    
    if rows:
        return {
            "headers": headers,
            "rows": rows
        }
    
    return None




def save_csv(table_data: Dict[str, Any], filepath: str) -> None:
    """Save table data to CSV file."""
    if not table_data:
        print("No table data to save")
        return
    
    headers = table_data.get("headers", [])
    rows = table_data.get("rows", [])
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)
    
    print(f"Saved CSV to {filepath} with {len(rows)} rows")




def main():
    """Main scraping function using Jina.ai public proxy."""
    args = setup_cli()
    
    # Setup default output path
    if not args.out_table:
        args.out_table = f"investor_table_{args.market}_simple.csv"
    
    # Build URL - use English version like VBA
    url = f"https://www.set.or.th/en/market/statistics/investor-type?market={args.market}"
    
    try:
        # Scrape with Jina.ai public proxy
        html_content = scrape_with_jina_proxy(url, args.timeout)
        
        # Extract table data
        table_data = extract_table_from_html(html_content)
        if table_data:
            # Save CSV file
            save_csv(table_data, args.out_table)
            print("Scraping completed successfully!")
            
            # Save to database if requested
            if args.save_db:
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    
                    from supabase_database import get_proper_db
                    import pandas as pd
                    
                    print("💾 Saving to database...")
                    db = get_proper_db()
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(table_data["rows"], columns=table_data["headers"])
                    
                    # Check if we have data (market might be closed)
                    if len(df) == 0:
                        print("⚠️ No data found - market might be closed")
                        # Get latest available date from database
                        latest_date_str = db.get_latest_trade_date("investor_summary")
                        if latest_date_str:
                            from datetime import datetime
                            try:
                                trade_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
                                print(f"📅 Using latest available date from database: {trade_date}")
                            except ValueError:
                                from datetime import date
                                trade_date = date.today()
                                print(f"⚠️ Invalid date format from database, using today: {trade_date}")
                        else:
                            from datetime import date
                            trade_date = date.today()
                            print(f"⚠️ No previous data found, using today: {trade_date}")
                    else:
                        # Use detected trade date or fall back to today
                        detected_date = table_data.get("trade_date")
                        if detected_date:
                            # Convert string date back to date object if needed
                            if isinstance(detected_date, str):
                                from datetime import datetime
                                try:
                                    trade_date = datetime.strptime(detected_date, "%Y-%m-%d").date()
                                except ValueError:
                                    from datetime import date
                                    trade_date = date.today()
                                    print(f"⚠️ Invalid date format, using today: {trade_date}")
                            else:
                                trade_date = detected_date
                        else:
                            from datetime import date
                            trade_date = date.today()
                            print(f"⚠️ No trade date detected, using today: {trade_date}")
                    
                    # Save to database
                    success = db.save_investor_summary(df, trade_date)
                    
                    if success:
                        print(f"✅ Database: Saved investor data for {trade_date}")
                    else:
                        print("❌ Database: Failed to save investor data")
                        
                except Exception as db_error:
                    print(f"❌ Database save failed: {str(db_error)}")
                    # Don't fail the whole operation if database save fails
            
        else:
            print("ERROR: No table data found")
            sys.exit(2)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
