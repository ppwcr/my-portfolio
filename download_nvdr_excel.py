#!/usr/bin/env python3
"""
SET NVDR Trading-by-Stock Excel Downloader

Quickstart:
    pip install playwright
    python -m playwright install
    python download_nvdr_excel.py [--out out.xlsx] [--timeout 20000] [--no-sandbox] [--headful]

Downloads the "Export Excel" file from the SET NVDR Trading-by-Stock page.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, date

from playwright.sync_api import sync_playwright, Page, Browser, Download


def setup_logging():
    """Configure logging for progress messages."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def handle_consent_banner(page: Page, timeout: int = 5000):
    """Handle cookie/consent banners if they appear."""
    try:
        # Look for consent buttons in Thai and English
        consent_selectors = [
            'button:has-text("ยอมรับ")',
            'button:has-text("ยอมรับทั้งหมด")',
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            '[role="button"]:has-text("ยอมรับ")',
            '[role="button"]:has-text("Accept")',
            '[role="button"]:has-text("Agree")'
        ]
        
        for selector in consent_selectors:
            try:
                if page.locator(selector).is_visible(timeout=1000):
                    page.locator(selector).click()
                    logging.info("Dismissed consent banner")
                    return True
            except:
                continue
                
    except Exception as e:
        logging.debug(f"Consent banner handling failed (expected): {e}")
    
    return False


def find_export_button(page: Page, strategy: int = 1) -> Optional[str]:
    """
    Find the export button using different strategies.
    
    Args:
        page: Playwright page object
        strategy: 1=accessible roles, 2=text locators, 3=href fallback
    
    Returns:
        Selector string if found, None otherwise
    """
    if strategy == 1:
        # Strategy 1: Accessible roles
        role_selectors = [
            '[role="button"]:has-text("Excel")',
            '[role="link"]:has-text("Excel")',
            '[role="button"]:has-text("ส่งออก")',
            '[role="link"]:has-text("ส่งออก")',
            '[role="button"]:has-text("ดาวน์โหลด")',
            '[role="link"]:has-text("ดาวน์โหลด")'
        ]
        
        for selector in role_selectors:
            try:
                if page.locator(selector).is_visible():
                    logging.info(f"Found export button using accessible role: {selector}")
                    return selector
            except:
                continue
    
    elif strategy == 2:
        # Strategy 2: Text-based locators
        text_selectors = [
            'button:has-text("Excel")',
            'a:has-text("Excel")',
            'button:has-text("ส่งออก")',
            'a:has-text("ส่งออก")',
            'button:has-text("ดาวน์โหลด")',
            'a:has-text("ดาวน์โหลด")'
        ]
        
        for selector in text_selectors:
            try:
                if page.locator(selector).is_visible():
                    logging.info(f"Found export button using text locator: {selector}")
                    return selector
            except:
                continue
    
    elif strategy == 3:
        # Strategy 3: Href fallback
        try:
            # Look for visible links that end with .xlsx or contain "excel"
            excel_links = page.locator('a[href*="excel"], a[href*=".xlsx"], a[href*="ส่งออก"], a[href*="ดาวน์โหลด"]')
            for i in range(excel_links.count()):
                link = excel_links.nth(i)
                if link.is_visible():
                    href = link.get_attribute('href')
                    if href and (href.endswith('.xlsx') or 'excel' in href.lower() or 'ส่งออก' in href or 'ดาวน์โหลด' in href):
                        logging.info(f"Found export button using href fallback: {href}")
                        return f'a[href="{href}"]'
        except:
            pass
    
    return None


def download_nvdr_excel(
    output_path: str = "nvdr_trading_by_stock.xlsx",
    timeout: int = 20000,
    no_sandbox: bool = False,
    headful: bool = False
) -> int:
    """
    Download the SET NVDR Trading-by-Stock Excel file.
    
    Args:
        output_path: Path to save the downloaded file
        timeout: Timeout in milliseconds
        no_sandbox: Whether to run Chromium without sandbox
        headful: Whether to run in headful mode
    
    Returns:
        Exit code (0=success, 2=button not found, 3=download/save failure)
    """
    target_url = "https://www.set.or.th/th/market/statistics/nvdr/trading-by-stock"
    
    with sync_playwright() as p:
        # Configure browser launch options
        launch_options = {
            "headless": not headful
        }
        
        if no_sandbox:
            launch_options["args"] = ["--no-sandbox", "--disable-setuid-sandbox"]
        
        browser: Browser = p.chromium.launch(**launch_options)
        page = browser.new_page(accept_downloads=True)
        
        try:
            # Block resource types for speed optimization
            page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot,css}", lambda route: route.abort())
            
            logging.info(f"Navigating to {target_url}")
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout)
            
            # Handle consent banner
            handle_consent_banner(page)
            
            # Wait for page to be fully loaded
            page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Try to find export button with different strategies
            export_selector = None
            for strategy in [1, 2, 3]:
                export_selector = find_export_button(page, strategy)
                if export_selector:
                    break
            
            if not export_selector:
                logging.error("Export button not found after trying all strategies")
                return 2
            
            # Wait for the export button to be ready
            page.wait_for_selector(export_selector, timeout=timeout)
            
            # Set up download expectation
            logging.info("Waiting for download to start...")
            with page.expect_download(timeout=timeout) as download_info:
                page.click(export_selector)
            
            download: Download = download_info.value
            
            # Save the file
            output_file = Path(output_path)
            download.save_as(output_file)
            
            logging.info(f"Download completed successfully: {output_file.absolute()}")
            return 0
            
        except Exception as e:
            if "timeout" in str(e).lower():
                logging.error(f"Timeout occurred: {e}")
                return 3
            elif "download" in str(e).lower():
                logging.error(f"Download failed: {e}")
                return 3
            else:
                logging.error(f"Unexpected error: {e}")
                raise
        finally:
            browser.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download SET NVDR Trading-by-Stock Excel file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_nvdr_excel.py
  python download_nvdr_excel.py --out my_file.xlsx
  python download_nvdr_excel.py --timeout 30000 --no-sandbox
  python download_nvdr_excel.py --headful
        """
    )
    
    parser.add_argument(
        "--out",
        default="nvdr_trading_by_stock.xlsx",
        help="Output file path (default: nvdr_trading_by_stock.xlsx)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=20000,
        help="Timeout in milliseconds (default: 20000)"
    )
    
    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Run Chromium without sandbox"
    )
    
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run in headful mode (default: headless)"
    )
    
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Save data to database after download"
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        exit_code = download_nvdr_excel(
            output_path=args.out,
            timeout=args.timeout,
            no_sandbox=args.no_sandbox,
            headful=args.headful
        )
        
        # Save to database if requested and download was successful
        if exit_code == 0 and args.save_db:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                from supabase_database import get_proper_db
                
                logging.info("💾 Saving to database...")
                db = get_proper_db()
                
                # Save to database (let the function extract actual date from Excel)
                success = db.save_nvdr_trading(args.out, None)
                
                if success:
                    logging.info("✅ Database: NVDR data saved successfully")
                else:
                    logging.error("❌ Database: Failed to save NVDR data")
                    
            except Exception as db_error:
                logging.error(f"❌ Database save failed: {str(db_error)}")
                # Don't fail the whole operation if database save fails
        
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logging.info("Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
