#!/usr/bin/env python3
"""
SET Sector Index Scraper using Jina Reader Proxy

Quickstart:
  pip install httpx beautifulsoup4 lxml
  python scrape_set_sectors_jina.py --outdir out_set_sectors

Note: This script uses Jina Reader public proxy by prefixing URLs with `https://r.jina.ai/`. 
It does not execute JavaScript; it consumes Jina's extracted markdown/text.
"""

import argparse
import asyncio
import csv
import json
import re
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from datetime import datetime, date

import httpx
from bs4 import BeautifulSoup


class SETSectorScraper:
    """Scraper for SET sector index pages using Jina Reader proxy."""
    
    DEFAULT_SECTORS = [
        "agro", "consump", "fincial", "indus", 
        "propcon", "resourc", "service", "tech"
    ]
    
    BASE_URL = "https://www.set.or.th/en/market/index/set"
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.outdir = Path(args.outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(args.concurrency)
        self.results = []
        
    async def fetch_with_jina(self, url: str, use_text_fallback: bool = False) -> Optional[str]:
        """Fetch URL via Jina Reader proxy with retry logic."""
        proxied_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/markdown,text/plain,*/*",
        }
        
        if self.args.no_cache:
            headers["x-no-cache"] = "true"
            headers["x-cache-tolerance"] = "0"
            
        if use_text_fallback:
            headers["x-respond-with"] = "text"
            
        async with httpx.AsyncClient(timeout=self.args.timeout) as client:
            for attempt in range(3):
                try:
                    async with self.semaphore:
                        response = await client.get(proxied_url, headers=headers)
                        response.raise_for_status()
                        return response.text
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Rate limited - wait longer
                        wait_time = 2 + random.uniform(1, 3)  # Reduced from 10-25s to 3-5s
                        print(f"  Rate limited, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                    elif attempt == 2:
                        print(f"  Failed to fetch {url}: {e}")
                        return None
                    else:
                        await asyncio.sleep(1 + attempt * 0.5 + random.uniform(0, 0.5))  # Much faster backoff
                except httpx.TimeoutException as e:
                    if attempt == 2:
                        print(f"  Failed to fetch {url}: {e}")
                        return None
                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                    
        return None
    
    def extract_sector_metrics(self, content: str, sector: str) -> Dict[str, Any]:
        """Extract sector metrics from markdown/text content."""
        metrics = {"sector": sector.upper()}
        
        # Common patterns for index metrics
        patterns = {
            "index_value": [
                r"Last\s*\n\s*([0-9,]+\.?[0-9]*)",
                r"Index[:\s]*([0-9,]+\.?[0-9]*)",
                r"([0-9,]+\.?[0-9]*)\s*Index",
            ],
            "change": [
                r"Last\s*\n\s*[0-9,]+\.?[0-9]*\s*\n\s*([+-]?[0-9,]+\.?[0-9]*)",
                r"Change[:\s]*([+-]?[0-9,]+\.?[0-9]*)",
                r"([+-]?[0-9,]+\.?[0-9]*)\s*Change",
            ],
            "percent_change": [
                r"\(([+-]?[0-9,]+\.?[0-9]*%)\)",
                r"([+-]?[0-9,]+\.?[0-9]*%)\s*Change",
                r"Change[:\s]*[+-]?[0-9,]+\.?[0-9]*\s*\(([+-]?[0-9,]+\.?[0-9]*%)\)",
            ],
            "total_volume": [
                r"Volume \('000 Shares\)\s*\n\s*([0-9,]+)",
                r"Volume[:\s]*([0-9,]+)",
                r"Total Volume[:\s]*([0-9,]+)",
                r"([0-9,]+)\s*Volume",
            ],
            "total_value": [
                r"Value \(M\.Baht\)\s*\n\s*([0-9,]+\.?[0-9]*)",
                r"Value[:\s]*([0-9,]+)",
                r"Total Value[:\s]*([0-9,]+)",
                r"([0-9,]+)\s*Value",
            ],
            "num_constituents": [
                r"([0-9]+)\s*constituents",
                r"constituents[:\s]*([0-9]+)",
            ],
            "timestamp_hint": [
                r"Last Update\s+([^,\n]+)",
                r"as of\s+([^,\n]+)",
                r"as at\s+([^,\n]+)",
                r"([A-Za-z]+ \d{1,2},? \d{4})",
            ]
        }
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field in ["index_value", "change", "percent_change"]:
                        try:
                            # Try to convert to float, but keep as string if it fails
                            clean_value = value.replace(",", "")
                            if field == "percent_change":
                                clean_value = clean_value.replace("%", "")
                            metrics[field] = str(float(clean_value))  # Convert back to string for consistency
                        except ValueError:
                            metrics[field] = value
                    elif field == "timestamp_hint":
                        metrics[field] = value
                        # Try to parse the timestamp to get actual trade date
                        trade_date = self.parse_timestamp_to_date(value)
                        if trade_date:
                            metrics["trade_date"] = str(trade_date)  # Convert to string for consistency
                    else:
                        metrics[field] = value
                    break
                    
        return metrics
    
    def parse_timestamp_to_date(self, timestamp_str: str) -> Optional[date]:
        """Parse timestamp string to date object"""
        if not timestamp_str:
            return None
        
        try:
            # Try different formats
            formats = [
                "%d %b %Y",           # "21 Aug 2025"
                "%d %B %Y",           # "21 August 2025"
                "%B %d, %Y",          # "August 21, 2025"
                "%Y-%m-%d",           # "2025-08-21"
                "%d/%m/%Y",           # "21/08/2025"
                "%m/%d/%Y",           # "08/21/2025"
                "%d %b %Y %H:%M:%S",  # "21 Aug 2025 15:30:00"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str.strip(), fmt).date()
                except ValueError:
                    continue
            
            print(f"⚠️ Could not parse timestamp: {timestamp_str}")
            return None
        except Exception as e:
            print(f"⚠️ Timestamp parsing error: {e}")
            return None
    
    def parse_markdown_table(self, content: str) -> Optional[List[Dict[str, str]]]:
        """Parse markdown table from content."""
        lines = content.split('\n')
        tables = []
        current_table = []
        in_table = False
        
        for line in lines:
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                current_table.append(line)
                in_table = True
            elif in_table and (not line.strip() or '|' not in line):
                if len(current_table) >= 3:  # Need header + separator + at least one data row
                    tables.append(current_table)
                current_table = []
                in_table = False
                
        # Don't forget the last table
        if in_table and len(current_table) >= 3:
            tables.append(current_table)
            
        # Find the table with symbols
        for table_lines in tables:
            # Parse table
            rows = []
            for line in table_lines:
                if line.strip() == '|' * len(line.strip()):
                    continue  # Skip separator line
                cells = [cell.strip() for cell in line.strip('|').split('|')]
                rows.append(cells)
                
            if len(rows) < 2:
                continue
                
            # Check if this looks like a constituents table
            headers = rows[0]
            if any('symbol' in h.lower() or 'ticker' in h.lower() for h in headers):
                # This is the table we want
                return self._parse_table_rows(rows)
                
        return None
    
    def _parse_table_rows(self, rows: List[List[str]]) -> Optional[List[Dict[str, str]]]:
        """Parse table rows into list of dicts."""
        headers = rows[0]
        
        # Convert to list of dicts
        result = []
        for row in rows[1:]:
            if len(row) == len(headers):
                row_dict = dict(zip(headers, row))
                # Skip empty rows, header rows, or rows without valid symbols
                if (any(cell.strip() for cell in row) and 
                    self._has_symbol(row_dict) and 
                    not self._is_header_row(row_dict)):
                    # Clean up markdown links in symbol column
                    for key, value in row_dict.items():
                        if 'symbol' in key.lower() and value.startswith('[') and ']' in value:
                            full_symbol = value[1:value.find(']')]
                            # Extract base symbol (handle CB, SP, W1, W2, etc. suffixes)
                            base_symbol = self._extract_base_symbol(full_symbol)
                            row_dict[key] = base_symbol
                    result.append(row_dict)
                
        return result if result else None
    
    def _has_symbol(self, row_dict: Dict[str, str]) -> bool:
        """Check if a table row contains a valid symbol."""
        for key, value in row_dict.items():
            if 'symbol' in key.lower() and self._is_symbol(value):
                return True
        return False
    
    def _is_header_row(self, row_dict: Dict[str, str]) -> bool:
        """Check if a table row is a header/separator row that should be skipped."""
        for key, value in row_dict.items():
            if 'symbol' in key.lower():
                # Skip rows with sector names like "SERVICE - Services", "COMM - Commerce"
                if (' - ' in value or 
                    'SERVICE' in value.upper() or 
                    'COMM' in value.upper() or
                    'HELTH' in value.upper() or
                    'MEDIA' in value.upper() or
                    'PROF' in value.upper() or
                    'TOURISM' in value.upper() or
                    'TRANS' in value.upper()):
                    return True
        return False
    
    def parse_text_table(self, content: str) -> Optional[List[Dict[str, str]]]:
        """Parse table from text content using spacing patterns."""
        lines = content.split('\n')
        table_blocks = []
        current_block = []
        
        for line in lines:
            if line.strip():
                # Check if line has multiple columns (2+ spaces or tabs)
                if re.search(r'\S+\s{2,}\S+', line) or '\t' in line:
                    current_block.append(line)
                else:
                    if len(current_block) >= 5:  # Minimum table size
                        table_blocks.append(current_block)
                    current_block = []
            else:
                if len(current_block) >= 5:
                    table_blocks.append(current_block)
                current_block = []
                
        if current_block and len(current_block) >= 5:
            table_blocks.append(current_block)
            
        # Find the best table (most symbols)
        best_table = None
        max_symbols = 0
        
        for block in table_blocks:
            # Try to parse as delimited columns
            parsed = self._parse_delimited_block(block)
            if parsed:
                symbol_count = sum(1 for row in parsed if self._is_symbol(row.get('Symbol', '')))
                if symbol_count > max_symbols:
                    max_symbols = symbol_count
                    best_table = parsed
                    
        return best_table
    
    def _parse_delimited_block(self, lines: List[str]) -> Optional[List[Dict[str, str]]]:
        """Parse a block of lines as delimited columns."""
        if len(lines) < 2:
            return None
            
        # Try to infer column boundaries from first few lines
        sample_lines = lines[:min(5, len(lines))]
        column_positions = []
        
        for line in sample_lines:
            # Find positions of 2+ spaces or tabs
            positions = []
            for match in re.finditer(r'\S+\s{2,}', line):
                positions.append(match.end())
            for match in re.finditer(r'\t', line):
                positions.append(match.start())
            column_positions.extend(positions)
            
        if not column_positions:
            return None
            
        # Use most common positions
        from collections import Counter
        common_positions = [pos for pos, count in Counter(column_positions).most_common(10)]
        common_positions.sort()
        
        # Parse all lines
        parsed_rows = []
        for line in lines:
            row = self._split_at_positions(line, common_positions)
            if len(row) >= 3:  # Minimum columns
                parsed_rows.append(row)
                
        if len(parsed_rows) < 2:
            return None
            
        # Try to identify headers
        first_row = parsed_rows[0]
        headers = []
        for cell in first_row:
            cell_lower = cell.strip().lower()
            if 'symbol' in cell_lower or 'ticker' in cell_lower:
                headers.append('Symbol')
            elif 'last' in cell_lower or 'price' in cell_lower:
                headers.append('Last')
            elif 'change' in cell_lower:
                headers.append('Change')
            elif '%' in cell_lower:
                headers.append('%Chg')
            elif 'volume' in cell_lower:
                headers.append('Volume')
            elif 'value' in cell_lower:
                headers.append('Value')
            else:
                headers.append(f'Col{len(headers)+1}')
                
        # Convert to list of dicts
        result = []
        for row in parsed_rows[1:]:
            if len(row) == len(headers):
                row_dict = dict(zip(headers, [cell.strip() for cell in row]))
                result.append(row_dict)
                
        return result if result else None
    
    def _split_at_positions(self, line: str, positions: List[int]) -> List[str]:
        """Split line at given positions."""
        result = []
        last_pos = 0
        for pos in positions:
            if pos > last_pos:
                result.append(line[last_pos:pos].strip())
                last_pos = pos
        result.append(line[last_pos:].strip())
        return result
    
    def _extract_base_symbol(self, symbol_text: str) -> str:
        """Extract base symbol from text that may contain suffixes like CB, SP, W1, etc."""
        symbol_text = symbol_text.strip()
        
        # Common suffixes to remove
        suffixes = [' CB', ' SP', ' NVDR', '-W1', '-W2', '-W3', '-W4', '-W5', '-W6']
        
        for suffix in suffixes:
            if symbol_text.endswith(suffix):
                symbol_text = symbol_text[:-len(suffix)]
                break
        
        # Also handle cases like "GRAND CB" -> "GRAND"
        if ' ' in symbol_text:
            symbol_text = symbol_text.split()[0]
        
        return symbol_text.strip()
    
    def _is_symbol(self, text: str) -> bool:
        """Check if text looks like a stock symbol."""
        # Handle markdown links like [GFPT CB](...)
        if text.startswith('[') and ']' in text:
            full_symbol = text[1:text.find(']')]
            base_symbol = self._extract_base_symbol(full_symbol)
            return bool(re.match(r'^[A-Z]{2,10}$', base_symbol))  # Increased to 10 for longer symbols
        
        base_symbol = self._extract_base_symbol(text)
        return bool(re.match(r'^[A-Z]{2,10}$', base_symbol))
    
    async def scrape_sector(self, sector: str) -> Dict[str, Any]:
        """Scrape a single sector page."""
        url = f"{self.BASE_URL}/{sector}"
        
        # Try markdown first
        content = await self.fetch_with_jina(url, use_text_fallback=False)
        format_used = "md"
        
        # Fallback to text if needed
        if not content and self.args.format == "auto":
            content = await self.fetch_with_jina(url, use_text_fallback=True)
            format_used = "text"
        elif self.args.format == "text":
            content = await self.fetch_with_jina(url, use_text_fallback=True)
            format_used = "text"
            
        if not content:
            return {"sector": sector.upper(), "error": "Failed to fetch content"}
            
        # Save raw content
        if self.args.save_raw:
            raw_file = self.outdir / f"{sector}.raw.{format_used}"
            raw_file.write_text(content, encoding='utf-8')
            
        # Extract metrics
        metrics = self.extract_sector_metrics(content, sector)
        
        # Parse table
        table_data = None
        if format_used == "md":
            table_data = self.parse_markdown_table(content)
        if not table_data:
            table_data = self.parse_text_table(content)
            
        # Save metrics
        metrics_file = self.outdir / f"{sector}.metrics.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
            
        # Save table if found
        if table_data and not self.args.json_only:
            table_file = self.outdir / f"{sector}.constituents.csv"
            if table_data:
                with open(table_file, 'w', newline='', encoding='utf-8') as f:
                    if table_data:
                        # Add Sector to fieldnames
                        fieldnames = list(table_data[0].keys()) + ['Sector']
                        writer = csv.DictWriter(f, fieldnames=fieldnames, 
                                              delimiter=self.args.csv_delimiter)
                        writer.writeheader()
                        for row in table_data:
                            # Add sector column
                            row['Sector'] = sector
                            writer.writerow(row)
                            
        return {
            "sector": sector,
            "metrics": metrics,
            "table_data": table_data,
            "format_used": format_used
        }
                            
        return {
            "sector": sector,
            "metrics": metrics,
            "table_data": table_data,
            "format_used": format_used
        }
    
    async def run(self):
        """Run the scraper for all sectors."""
        sectors = self.args.sectors.split(',') if self.args.sectors else self.DEFAULT_SECTORS
        
        print(f"Scraping {len(sectors)} SET sector pages...")
        print(f"Output directory: {self.outdir}")
        print(f"Concurrency: {self.args.concurrency}")
        print()
        
        # Process sectors with delays to avoid rate limiting
        results = []
        failed_sectors = []
        
        # First pass: try all sectors quickly
        for i, sector in enumerate(sectors):
            if i > 0:  # Add minimal delay between sectors
                delay = 0.5 + random.uniform(0, 1)  # Very short delay
                print(f"Waiting {delay:.1f}s before next sector...")
                await asyncio.sleep(delay)
            
            result = await self.scrape_sector(sector)
            results.append(result)
            
            # Track failed sectors for retry
            if isinstance(result, Exception) or not result.get("table_data"):
                failed_sectors.append((i, sector))
        
        # Smart retry: only retry failed sectors with slightly longer delays
        if failed_sectors and len(failed_sectors) < len(sectors):  # Don't retry if all failed
            print(f"\nRetrying {len(failed_sectors)} failed sectors...")
            for attempt in range(2):  # Max 2 retry attempts
                still_failed = []
                for idx, sector in failed_sectors:
                    print(f"Retry {attempt + 1}: {sector}")
                    await asyncio.sleep(1 + random.uniform(0, 1))  # Slightly longer delay for retries
                    
                    result = await self.scrape_sector(sector)
                    results[idx] = result  # Replace the failed result
                    
                    # Check if still failed
                    if isinstance(result, Exception) or not result.get("table_data"):
                        still_failed.append((idx, sector))
                
                failed_sectors = still_failed
                if not failed_sectors:
                    print("All retries successful!")
                    break
        
        success_count = 0
        for i, result in enumerate(results):
            sector = sectors[i]
            if isinstance(result, Exception):
                print(f"[ERROR] {sector}  {result}")
                continue
                
            metrics = result.get("metrics", {})
            table_data = result.get("table_data")
            
            if metrics and len(metrics) > 1:  # More than just sector
                index_val = metrics.get("index_value", "N/A")
                change = metrics.get("change", "N/A")
                pct_change = metrics.get("percent_change", "N/A")
                symbol_count = len(table_data) if table_data else 0
                
                print(f"[OK] {sector}  symbols: {symbol_count}  index: {index_val}  change: {change} ({pct_change})")
                success_count += 1
            else:
                print(f"[WARN] {sector}  saved raw only (no metrics/table found)")
                
        print(f"\nCompleted: {success_count}/{len(sectors)} sectors processed successfully")
        
        # Combine all CSV files into one
        if not self.args.json_only:
            self.combine_csv_files()
        
        # Save to database if requested
        if self.args.save_db and success_count > 0:
            await self.save_to_database(results)
        
        # Exit code logic
        if success_count == 0:
            return 2
        return 0
    
    async def save_to_database(self, results: List[Dict[str, Any]]):
        """Save sector data to database"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            from supabase_database import get_proper_db
            import pandas as pd
            
            print("\n💾 Saving sector data to database...")
            db = get_proper_db()
            
            saved_count = 0
            for result in results:
                if not result.get("table_data") or isinstance(result, Exception):
                    continue
                
                sector = result["sector"]
                table_data = result["table_data"]
                metrics = result.get("metrics", {})
                
                # Get trade date from metrics or use today
                detected_date = metrics.get("trade_date")
                if detected_date:
                    # Convert string date back to date object if needed
                    if isinstance(detected_date, str):
                        try:
                            trade_date = datetime.strptime(detected_date, "%Y-%m-%d").date()
                        except ValueError:
                            trade_date = date.today()
                            print(f"⚠️ Invalid date format for {sector}, using today: {trade_date}")
                    else:
                        trade_date = detected_date
                else:
                    trade_date = date.today()
                    print(f"⚠️ No trade date detected for {sector}, using today: {trade_date}")
                
                try:
                    # Convert table data to DataFrame
                    df = pd.DataFrame(table_data)
                    
                    # Check if we have data (market might be closed)
                    if len(df) == 0:
                        print(f"⚠️ No data found for {sector} - market might be closed")
                        # Get latest available date from database
                        latest_date_str = db.get_latest_trade_date("sector_data")
                        if latest_date_str:
                            try:
                                trade_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
                                print(f"📅 Using latest available date from database: {trade_date}")
                            except ValueError:
                                trade_date = date.today()
                                print(f"⚠️ Invalid date format from database, using today: {trade_date}")
                        else:
                            trade_date = date.today()
                            print(f"⚠️ No previous data found, using today: {trade_date}")
                    
                    # Save to database
                    success = db.save_sector_data(df, sector, trade_date)
                    
                    if success:
                        saved_count += 1
                        print(f"✅ Database: Saved {sector} sector data for {trade_date}")
                    else:
                        print(f"❌ Database: Failed to save {sector} sector data")
                        
                except Exception as sector_error:
                    print(f"❌ Database save failed for {sector}: {str(sector_error)}")
            
            if saved_count > 0:
                print(f"✅ Database: Successfully saved {saved_count} sectors")
            else:
                print("❌ Database: No sectors were saved")
                
        except Exception as db_error:
            print(f"❌ Database integration failed: {str(db_error)}")
            # Don't fail the whole operation if database save fails
    
    def combine_csv_files(self):
        """Combine all sector CSV files into a single CSV with category column."""
        import glob
        
        # Find all CSV files
        csv_pattern = str(self.outdir / "*.constituents.csv")
        csv_files = glob.glob(csv_pattern)
        
        if not csv_files:
            print("No CSV files found to combine")
            return
        
        print(f"\nCombining {len(csv_files)} CSV files...")
        
        # Read and combine all CSV files
        all_rows = []
        header_written = False
        
        for csv_file in sorted(csv_files):
            sector = Path(csv_file).stem.split('.')[0]  # Get sector name from filename
            print(f"  Processing {sector}...")
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Write header only once
                if not header_written:
                    fieldnames = reader.fieldnames
                    all_rows.append(fieldnames)
                    header_written = True
                
                # Add all data rows
                for row in reader:
                    if fieldnames:  # Check if fieldnames is not None
                        all_rows.append([row[field] for field in fieldnames])
        
        # Write combined CSV
        combined_file = self.outdir / "combined_set_constituents.csv"
        with open(combined_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=self.args.csv_delimiter)
            writer.writerows(all_rows)
        
        print(f"Combined CSV saved to: {combined_file}")
        print(f"Total rows: {len(all_rows) - 1} (excluding header)")
        print(f"Columns: {', '.join(all_rows[0])}")


def main():
    parser = argparse.ArgumentParser(description="Scrape SET sector index pages using Jina Reader proxy")
    parser.add_argument("--outdir", default="./out_set_sectors", help="Output directory (default: ./out_set_sectors)")
    parser.add_argument("--format", choices=["auto", "md", "text"], default="auto", 
                       help="Response format (default: auto)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass Jina cache")
    parser.add_argument("--concurrency", type=int, default=4, choices=range(1, 9),
                       help="Concurrency limit (default: 4)")
    parser.add_argument("--timeout", type=int, default=20, help="Request timeout in seconds (default: 20)")
    parser.add_argument("--sectors", help="Comma-separated sector slugs (default: all 8 sectors)")
    parser.add_argument("--csv-delimiter", default=",", help="CSV delimiter (default: ,)")
    parser.add_argument("--save-raw", action="store_true", help="Save raw response body")
    parser.add_argument("--json-only", action="store_true", help="Skip CSV if no table detected")
    parser.add_argument("--save-db", action="store_true", help="Save data to database after scraping")
    
    args = parser.parse_args()
    
    scraper = SETSectorScraper(args)
    exit_code = asyncio.run(scraper.run())
    exit(exit_code)


if __name__ == "__main__":
    main()
