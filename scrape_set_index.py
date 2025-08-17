#!/usr/bin/env python3
"""
SET Index Data Scraper

Scrapes SET index data from the SET website using Jina.ai proxy
and saves it to a JSON file for the portfolio dashboard.
"""

import re
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fetch_set_index_data(jina_proxy_url="http://r.jina.ai/"):
    """Fetch SET index data using Jina.ai proxy"""
    
    # Target URL to scrape
    target_url = "https://www.set.or.th/en/home"
    full_url = f"{jina_proxy_url}{target_url}"
    
    try:
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        content = response.text
        
        # Extract the table data using regex patterns
        index_data = []
        
        # Look for the table with index data
        table_pattern = r'\| Index \| Last \| Change \| Volume.*?\| Value.*?\|.*?\n(.*?)(?=\n\n|\n [A-Z]|\n\|(?!\s*\[))'
        table_match = re.search(table_pattern, content, re.DOTALL)
        
        if table_match:
            table_content = table_match.group(1)
            
            # Parse each row
            rows = table_content.strip().split('\n')
            for row in rows:
                if '|' in row and not row.strip().startswith('|---') and not row.strip() == '| --- | --- | --- | --- | --- |':
                    parts = [p.strip() for p in row.split('|') if p.strip()]
                    if len(parts) >= 5:
                        index_name = parts[0]
                        # Remove markdown link syntax and clean up
                        if '](' in index_name:
                            index_name = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', index_name)
                        index_name = index_name.strip()
                        
                        # Skip invalid entries
                        if index_name in ['---', '', 'Index']:
                            continue
                        
                        last = parts[1]
                        change = parts[2]
                        volume = parts[3].replace(',', '')
                        value = parts[4]
                        
                        index_data.append({
                            'index': index_name,
                            'last': last,
                            'change': change,
                            'volume': volume,
                            'value': value
                        })
        
        # Also look for SETTRI data separately
        settri_pattern = r'\| \[?SETTRI\]?.*?\| ([\d,]+\.[\d]+) \| ([+-]?[\d,]+\.[\d]+.*?) \|'
        settri_match = re.search(settri_pattern, content)
        if settri_match:
            index_data.append({
                'index': 'SETTRI',
                'last': settri_match.group(1),
                'change': settri_match.group(2),
                'volume': '-',
                'value': '-'
            })
        
        # Extract timestamp - this will be used by all scrapers  
        timestamp_pattern = r'Last Update (\d{1,2} \w+ \d{4} \d{2}:\d{2}:\d{2})'
        timestamp_match = re.search(timestamp_pattern, content)
        set_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime("%d %b %Y %H:%M:%S")
        
        # Parse SET timestamp to datetime for other scrapers to use
        set_datetime = None
        if timestamp_match:
            try:
                set_datetime = datetime.strptime(timestamp_match.group(1), "%d %b %Y %H:%M:%S")
            except ValueError:
                pass
        
        return {
            'success': True,
            'data': index_data,
            'timestamp': set_timestamp,
            'set_datetime': set_datetime.isoformat() if set_datetime else None,
            'scraped_at': datetime.now().isoformat()
        }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f"Request failed: {str(e)}",
            'data': [],
            'timestamp': None,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Parsing failed: {str(e)}",
            'data': [],
            'timestamp': None,
            'scraped_at': datetime.now().isoformat()
        }


def save_index_data(data, output_dir="_out"):
    """Save the scraped index data to JSON file"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"set_index_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Also save as latest
    latest_filename = output_path / "set_index_latest.json"
    with open(latest_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename


def main():
    parser = argparse.ArgumentParser(description='Scrape SET index data')
    parser.add_argument('--outdir', default='_out', help='Output directory for scraped data')
    parser.add_argument('--proxy', default='http://r.jina.ai/', help='Jina proxy URL')
    parser.add_argument('--save-db', action='store_true', help='Save data to database')
    args = parser.parse_args()
    
    print("Scraping SET index data...")
    data = fetch_set_index_data(args.proxy)
    
    if data['success']:
        filename = save_index_data(data, args.outdir)
        print(f"✓ Successfully scraped {len(data['data'])} indices")
        print(f"✓ Data saved to: {filename}")
        print(f"✓ Timestamp: {data['timestamp']}")
        
        # Save to database if requested
        if args.save_db:
            try:
                from supabase_database import get_proper_db
                print("💾 Saving to database...")
                db = get_proper_db()
                db_result = db.save_set_index_data(data['data'])
                print(f"✓ Database: {db_result['message']}")
            except Exception as e:
                print(f"❌ Database save failed: {str(e)}")
                # Don't fail the whole operation if database save fails
        
        # Print summary
        for item in data['data']:
            print(f"  {item['index']}: {item['last']} ({item['change']})")
    else:
        print(f"✗ Failed to scrape data: {data['error']}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())