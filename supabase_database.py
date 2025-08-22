#!/usr/bin/env python3
"""
Updated database operations with proper schemas that match the actual data structure
"""
import os
import pandas as pd
from datetime import datetime, date
from typing import Optional, Dict, Any
from supabase import create_client, Client


class ProperDatabaseManager:
    """Database manager with schemas that match actual data structure"""
    
    def __init__(self):
        # Try to get from environment variables first
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        
        # Require environment variables to be set
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
        
        self.client: Client = create_client(self.url, self.key)
    
    def _parse_number(self, value: str) -> Optional[float]:
        """Parse string to number, handling empty values and commas"""
        if not value or value == '-' or value == '' or str(value).strip() == '':
            return None
        try:
            cleaned = str(value).replace(',', '').strip()
            if cleaned == '' or cleaned == '-':
                return None
            
            result = float(cleaned)
            
            # Check for invalid float values that are not JSON compliant
            if not (result == result):  # Check for NaN
                print(f"⚠️  DEBUG: Found NaN value when parsing '{value}' -> '{cleaned}'")
                return None
            if result == float('inf') or result == float('-inf'):
                print(f"⚠️  DEBUG: Found infinity value when parsing '{value}' -> '{cleaned}' = {result}")
                return None
                
            return result
        except (ValueError, TypeError):
            return None
    
    def _parse_integer(self, value: str) -> Optional[int]:
        """Parse string to integer, handling empty values and commas"""
        if not value or value == '-' or value == '' or str(value).strip() == '':
            return None
        try:
            cleaned = str(value).replace(',', '').strip()
            if cleaned == '' or cleaned == '-':
                return None
            return int(float(cleaned))  # Convert to float first, then to int
        except (ValueError, TypeError):
            return None
    
    def save_investor_summary(self, csv_data: pd.DataFrame, trade_date: Optional[date] = None) -> bool:
        """Save investor summary data with proper structure"""
        try:
            print(f"📊 Processing investor summary data: {csv_data.shape}")
            
            records = []
            for _, row in csv_data.iterrows():
                record = {
                    'investor_type': str(row.iloc[0]).strip(),
                    
                    # Period 1 (columns 1-5)
                    'period1_buy_value': self._parse_number(row.iloc[1]) if len(row) > 1 else None,
                    'period1_buy_percent': self._parse_number(row.iloc[2]) if len(row) > 2 else None,
                    'period1_sell_value': self._parse_number(row.iloc[3]) if len(row) > 3 else None,
                    'period1_sell_percent': self._parse_number(row.iloc[4]) if len(row) > 4 else None,
                    'period1_net_value': self._parse_number(row.iloc[5]) if len(row) > 5 else None,
                    
                    # Period 2 (columns 6-10)
                    'period2_buy_value': self._parse_number(row.iloc[6]) if len(row) > 6 else None,
                    'period2_buy_percent': self._parse_number(row.iloc[7]) if len(row) > 7 else None,
                    'period2_sell_value': self._parse_number(row.iloc[8]) if len(row) > 8 else None,
                    'period2_sell_percent': self._parse_number(row.iloc[9]) if len(row) > 9 else None,
                    'period2_net_value': self._parse_number(row.iloc[10]) if len(row) > 10 else None,
                    
                    # Period 3 (columns 11-15)
                    'period3_buy_value': self._parse_number(row.iloc[11]) if len(row) > 11 else None,
                    'period3_buy_percent': self._parse_number(row.iloc[12]) if len(row) > 12 else None,
                    'period3_sell_value': self._parse_number(row.iloc[13]) if len(row) > 13 else None,
                    'period3_sell_percent': self._parse_number(row.iloc[14]) if len(row) > 14 else None,
                    'period3_net_value': self._parse_number(row.iloc[15]) if len(row) > 15 else None,
                    
                    'trade_date': trade_date.isoformat() if trade_date else None,
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            # Insert to investor_summary table
            result = self.client.table('investor_summary').insert(records).execute()
            print(f"✅ Saved {len(records)} investor summary records")
            
            # Update timestamp
            if trade_date:
                self.update_data_timestamp('investor_summary', trade_date, len(records))
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving investor summary: {e}")
            return False
    
    def save_nvdr_trading(self, excel_path: str, trade_date: Optional[date] = None) -> bool:
        """Save NVDR trading data with proper structure"""
        try:
            from excel_file_parser import RobustExcelParser
            
            parser = RobustExcelParser()
            df = parser.parse_excel_file(excel_path)
            
            if df is None:
                print("❌ Could not read NVDR Excel file")
                return False
            
            print(f"📊 Processing NVDR data: {df.shape}")
            
            # Extract actual trade date from Excel file
            actual_trade_date = trade_date
            for idx, row in df.iterrows():
                for cell in row:
                    if pd.notna(cell) and 'As of' in str(cell):
                        # Extract date from "As of 15 Aug 2025" format
                        import re
                        date_match = re.search(r'As of (\d{1,2} \w+ \d{4})', str(cell))
                        if date_match:
                            try:
                                import datetime as dt
                                actual_trade_date = dt.datetime.strptime(date_match.group(1), "%d %b %Y").date()
                                print(f"📅 Found actual trade date in Excel: {actual_trade_date}")
                                break
                            except:
                                pass
                if actual_trade_date != trade_date:
                    break
                if idx > 5:  # Only check first few rows
                    break
            
            # Find data starting point (look for 'Symbol' row)
            data_start_row = None
            for idx, row in df.iterrows():
                if any('Symbol' in str(cell) for cell in row if pd.notna(cell)):
                    data_start_row = idx + 1  # Data starts after header row
                    break
            
            if data_start_row is None:
                print("❌ Could not find Symbol column in NVDR data")
                return False
            
            # Process data rows
            records = []
            for idx in range(data_start_row, len(df)):
                row = df.iloc[idx]
                symbol = str(row.iloc[0]).strip() if len(row) > 0 and pd.notna(row.iloc[0]) else ''
                
                if not symbol or symbol == '':
                    continue
                
                record = {
                    'symbol': symbol,
                    
                    # Volume data (columns 1-5)
                    'volume_buy': self._parse_integer(row.iloc[1]) if len(row) > 1 else None,
                    'volume_sell': self._parse_integer(row.iloc[2]) if len(row) > 2 else None,
                    'volume_total': self._parse_integer(row.iloc[3]) if len(row) > 3 else None,
                    'volume_net': self._parse_integer(row.iloc[4]) if len(row) > 4 else None,
                    'volume_percent': self._parse_number(row.iloc[5]) if len(row) > 5 else None,
                    
                    # Value data (columns 6-10)
                    'value_buy': self._parse_integer(row.iloc[6]) if len(row) > 6 else None,
                    'value_sell': self._parse_integer(row.iloc[7]) if len(row) > 7 else None,
                    'value_total': self._parse_integer(row.iloc[8]) if len(row) > 8 else None,
                    'value_net': self._parse_integer(row.iloc[9]) if len(row) > 9 else None,
                    'value_percent': self._parse_number(row.iloc[10]) if len(row) > 10 else None,
                    
                    'trade_date': actual_trade_date.isoformat() if actual_trade_date else None,
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            if not records:
                print("❌ No valid NVDR records found")
                return False
            
            # Insert to nvdr_trading table
            result = self.client.table('nvdr_trading').insert(records).execute()
            print(f"✅ Saved {len(records)} NVDR trading records")
            
            # Update timestamp
            if actual_trade_date:
                self.update_data_timestamp('nvdr_trading', actual_trade_date, len(records))
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving NVDR trading data: {e}")
            return False
    
    def save_short_sales_trading(self, excel_path: str, trade_date: Optional[date] = None) -> bool:
        """Save short sales trading data with proper structure"""
        try:
            from excel_file_parser import RobustExcelParser
            
            parser = RobustExcelParser()
            df = parser.parse_excel_file(excel_path)
            
            if df is None:
                print("❌ Could not read Short Sales Excel file")
                return False
            
            print(f"📊 Processing Short Sales data: {df.shape}")
            
            # Extract actual trade date from Excel file
            actual_trade_date = trade_date
            for idx, row in df.iterrows():
                for cell in row:
                    if pd.notna(cell):
                        cell_str = str(cell)
                        # Check for English format: "As of 15 Aug 2025"
                        if 'As of' in cell_str:
                            import re
                            date_match = re.search(r'As of (\d{1,2} \w+ \d{4})', cell_str)
                            if date_match:
                                try:
                                    import datetime as dt
                                    actual_trade_date = dt.datetime.strptime(date_match.group(1), "%d %b %Y").date()
                                    print(f"📅 Found actual trade date in Short Sales Excel: {actual_trade_date}")
                                    break
                                except:
                                    pass
                        # Check for Thai format: "15 ส.ค. 2568" (Buddhist year)
                        elif 'ส.ค.' in cell_str or 'วันที่' in cell_str:
                            import re
                            date_match = re.search(r'(\d{1,2})\s*ส\.ค\.\s*(\d{4})', cell_str)
                            if date_match:
                                try:
                                    day = int(date_match.group(1))
                                    buddhist_year = int(date_match.group(2))
                                    # Convert Buddhist year to Gregorian year
                                    gregorian_year = buddhist_year - 543
                                    # August is month 8
                                    import datetime as dt
                                    actual_trade_date = dt.date(gregorian_year, 8, day)
                                    print(f"📅 Found actual trade date in Short Sales Excel (Thai): {actual_trade_date}")
                                    break
                                except:
                                    pass
                if actual_trade_date != trade_date:
                    break
                if idx > 10:  # Check more rows for Thai format
                    break
            
            # Find stock symbol rows (exclude Thai headers)
            records = []
            for idx, row in df.iterrows():
                symbol = str(row.iloc[0]).strip() if len(row) > 0 and pd.notna(row.iloc[0]) else ''
                
                # Check if it's a valid stock symbol (2+ letters, all caps, no Thai)
                if (len(symbol) >= 2 and 
                    symbol.isalpha() and 
                    symbol.isupper() and
                    not any(thai_char in symbol for thai_char in 'กขคงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ')):
                    
                    record = {
                        'symbol': symbol,
                        
                        # Short sales volume (columns 1-3)
                        'short_volume_local': self._parse_integer(row.iloc[1]) if len(row) > 1 else None,
                        'short_volume_nvdr': self._parse_integer(row.iloc[2]) if len(row) > 2 else None,
                        'short_volume_total': self._parse_integer(row.iloc[3]) if len(row) > 3 else None,
                        
                        # Short sales value and percentage (columns 4-5)
                        'short_value_baht': self._parse_integer(row.iloc[4]) if len(row) > 4 else None,
                        'short_percentage': self._parse_number(row.iloc[5]) if len(row) > 5 else None,
                        
                        # Outstanding positions (columns 6-8)
                        'outstanding_local': self._parse_integer(row.iloc[6]) if len(row) > 6 else None,
                        'outstanding_nvdr': self._parse_integer(row.iloc[7]) if len(row) > 7 else None,
                        'outstanding_total': self._parse_integer(row.iloc[8]) if len(row) > 8 else None,
                        'outstanding_percentage': self._parse_number(row.iloc[9]) if len(row) > 9 else None,
                        
                        'trade_date': actual_trade_date.isoformat() if actual_trade_date else None,
                        'created_at': datetime.now().isoformat()
                    }
                    records.append(record)
            
            if not records:
                print("❌ No valid Short Sales records found")
                return False
            
            # Insert to short_sales_trading table
            result = self.client.table('short_sales_trading').insert(records).execute()
            print(f"✅ Saved {len(records)} Short Sales trading records")
            
            # Update timestamp
            if actual_trade_date:
                self.update_data_timestamp('short_sales_trading', actual_trade_date, len(records))
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving Short Sales trading data: {e}")
            return False
    
    def save_sector_data(self, csv_data: pd.DataFrame, sector_name: str, trade_date: Optional[date] = None) -> bool:
        """Save sector constituents data to Supabase - keeping existing sector_data table"""
        try:
            print(f"🔍 DEBUG: Processing {len(csv_data)} rows for {sector_name} sector")
            
            # Convert DataFrame to list of dictionaries for the existing sector_data table
            records = []
            grand_found = False
            for _, row in csv_data.iterrows():
                symbol = str(row['Symbol'] if 'Symbol' in row else '').strip()
                last_price = self._parse_number(row['Last'] if 'Last' in row else '')
                
                record = {
                    'symbol': symbol,
                    'open_price': self._parse_number(row['Open'] if 'Open' in row else ''),
                    'high_price': self._parse_number(row['High'] if 'High' in row else ''),
                    'low_price': self._parse_number(row['Low'] if 'Low' in row else ''),
                    'last_price': last_price,
                    'change': str(row['Change'] if 'Change' in row else ''),
                    'percent_change': str(row['% Change'] if '% Change' in row else ''),
                    'bid': str(row['Bid'] if 'Bid' in row else ''),
                    'offer': str(row['Offer'] if 'Offer' in row else ''),
                    'volume_shares': self._parse_integer(row['Volume (Shares)'] if 'Volume (Shares)' in row else ''),
                    'value_baht': self._parse_number(row['Value (\'000 Baht)'] if 'Value (\'000 Baht)' in row else ''),
                    'sector': sector_name,
                    'trade_date': trade_date.isoformat() if trade_date else None,
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
                
                # Track if GRAND is found
                if symbol == 'GRAND':
                    grand_found = True
                    print(f"✅ DEBUG: GRAND record created for database: symbol={symbol}, last_price={last_price}, sector={sector_name}")
            
            if sector_name == 'service' and not grand_found:
                print(f"❌ DEBUG: GRAND NOT found when processing {sector_name} sector records")
            
            print(f"🔍 DEBUG: Created {len(records)} records for {sector_name} sector")
            
            # Clear existing records for this sector and trade_date first
            delete_result = self.client.table('sector_data').delete().eq('sector', sector_name).eq('trade_date', trade_date.isoformat() if trade_date else None).execute()
            print(f"🗑️  DEBUG: Deleted {len(delete_result.data) if delete_result.data else 0} existing {sector_name} records for {trade_date}")
            
            # Insert data to sector_data table (existing table)
            result = self.client.table('sector_data').insert(records).execute()
            inserted_count = len(result.data) if result.data else 0
            print(f"✅ DEBUG: Inserted {inserted_count} {sector_name} sector records into database")
            
            # Update timestamp (only for the first sector to avoid duplicates)
            if trade_date and sector_name == 'SET':  # Use SET as the primary sector for timestamp
                self.update_data_timestamp('sector_data', trade_date, inserted_count)
            
            # Verify GRAND was actually inserted
            if sector_name == 'service' and grand_found:
                verify_result = self.client.table('sector_data').select('symbol, last_price').eq('symbol', 'GRAND').eq('trade_date', trade_date.isoformat() if trade_date else None).execute()
                if verify_result.data:
                    print(f"✅ DEBUG: GRAND verified in database: {verify_result.data[0]}")
                else:
                    print(f"❌ DEBUG: GRAND NOT found in database after insert!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving {sector_name} sector data: {e}")
            import traceback
            print(f"💥 DEBUG: Full traceback: {traceback.format_exc()}")
            return False
    
    def _create_set_index_table(self) -> bool:
        """Create the SET index table if it doesn't exist"""
        try:
            # Try to create table by inserting a dummy record (Supabase will auto-create schema)
            dummy_record = {
                'trade_date': '2025-01-01',
                'index_name': 'TEST',
                'last_value': 0,
                'change_value': 0,
                'change_text': 'test',
                'volume_thousands': 0,
                'value_million_baht': 0,
                'created_at': '2025-01-01T00:00:00Z'
            }
            
            # Insert dummy record (this creates the table with proper schema)
            result = self.client.table('set_index').insert(dummy_record).execute()
            
            # Delete the dummy record
            self.client.table('set_index').delete().eq('index_name', 'TEST').execute()
            
            print("✅ SET index table created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error creating SET index table: {str(e)}")
            return False
    
    def save_set_index_data(self, data: list) -> dict:
        """Save SET index data to the database"""
        try:
            if not data:
                return {"status": "success", "message": "No index data to save", "saved_count": 0}
            
            # Get current date for trade_date
            trade_date = datetime.now().date()
            
            # Check if data for today already exists (this will also test if table exists)
            try:
                existing = self.client.table('set_index').select('*').eq('trade_date', trade_date.isoformat()).execute()
            except Exception as table_error:
                # If table doesn't exist, try to create it
                error_msg = str(table_error).lower()
                if 'does not exist' in error_msg or 'relation' in error_msg:
                    print("📊 SET index table doesn't exist, attempting to create it...")
                    success = self._create_set_index_table()
                    if not success:
                        raise Exception("Failed to create SET index table")
                    # Try again after creating table
                    existing = self.client.table('set_index').select('*').eq('trade_date', trade_date.isoformat()).execute()
                else:
                    raise table_error
            
            if existing.data:
                # Delete existing data for today before inserting new data
                delete_result = self.client.table('set_index').delete().eq('trade_date', trade_date.isoformat()).execute()
                print(f"🗑️ Deleted {len(existing.data)} existing records for {trade_date}")
            
            # Prepare records for insertion
            records = []
            for item in data:
                # Parse change value to extract numeric part
                change_str = str(item.get('change', ''))
                change_value = None
                if change_str and change_str != '-':
                    # Extract the first number (including sign) from change string
                    import re
                    change_match = re.search(r'([+-]?\d+\.?\d*)', change_str)
                    if change_match:
                        change_value = self._parse_number(change_match.group(1))
                
                record = {
                    'trade_date': trade_date.isoformat(),
                    'index_name': str(item.get('index', '')).strip(),
                    'last_value': self._parse_number(item.get('last', '')),
                    'change_value': change_value,
                    'change_text': change_str,
                    'volume_thousands': self._parse_integer(item.get('volume', '')) if item.get('volume') not in ['-', ''] else None,
                    'value_million_baht': self._parse_number(item.get('value', '')) if item.get('value') not in ['-', ''] else None,
                    'created_at': datetime.now().isoformat()
                }
                
                # Only add record if index_name is not empty
                if record['index_name']:
                    records.append(record)
            
            if not records:
                return {"status": "success", "message": "No valid index data to save", "saved_count": 0}
            
            # Insert new records
            result = self.client.table('set_index').insert(records).execute()
            
            saved_count = len(result.data) if result.data else len(records)
            print(f"✅ Saved {saved_count} SET index records for {trade_date}")
            
            # Update timestamp
            self.update_data_timestamp('set_index', trade_date, saved_count)
            
            return {
                "status": "success", 
                "message": f"Successfully saved {saved_count} SET index records",
                "saved_count": saved_count,
                "trade_date": trade_date.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error saving SET index data: {str(e)}")
            raise e
    
    def get_latest_set_index_data(self) -> dict:
        """Get the latest SET index data from database"""
        try:
            # Get the most recent trade_date
            latest_date_result = self.client.table('set_index').select('trade_date').order('trade_date', desc=True).limit(1).execute()
            
            if not latest_date_result.data:
                return {"status": "success", "data": [], "trade_date": None, "message": "No SET index data found"}
            
            latest_date = latest_date_result.data[0]['trade_date']
            
            # Get all indices for the latest date
            result = self.client.table('set_index').select('*').eq('trade_date', latest_date).order('index_name', desc=False).execute()
            
            if not result.data:
                return {"status": "success", "data": [], "trade_date": latest_date, "message": "No data for latest date"}
            
            # Convert database format back to API format
            data = []
            for record in result.data:
                data.append({
                    'index': record['index_name'],
                    'last': str(record['last_value']) if record['last_value'] is not None else '',
                    'change': record['change_text'] or '',
                    'volume': str(int(record['volume_thousands'])) if record['volume_thousands'] is not None else '-',
                    'value': str(record['value_million_baht']) if record['value_million_baht'] is not None else '-'
                })
            
            return {
                "status": "success",
                "data": data,
                "trade_date": latest_date,
                "record_count": len(data)
            }
            
        except Exception as e:
            print(f"❌ Error getting SET index data: {str(e)}")
            return {"status": "error", "data": [], "trade_date": None, "error": str(e)}
    
    def is_set_index_data_fresh(self) -> bool:
        """Check if SET index data exists (any recent data available)"""
        try:
            # Check if we have any data in the last 7 days
            from datetime import timedelta
            cutoff_date = (datetime.now().date() - timedelta(days=7)).isoformat()
            result = self.client.table('set_index').select('trade_date').gte('trade_date', cutoff_date).limit(1).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"❌ Error checking SET index data freshness: {str(e)}")
            return False
    
    def add_portfolio_symbol(self, symbol: str) -> bool:
        """Add a symbol to user's portfolio"""
        try:
            record = {
                'symbol': symbol.upper().strip(),
                'added_at': datetime.now().isoformat()
            }
            
            # First check if symbol already exists
            existing = self.client.table('portfolio_symbols').select('*').eq('symbol', symbol.upper().strip()).execute()
            if existing.data:
                print(f"📋 Symbol {symbol} already in portfolio")
                return True
            
            # Insert new portfolio symbol
            result = self.client.table('portfolio_symbols').insert(record).execute()
            print(f"✅ Added {symbol} to portfolio")
            return True
            
        except Exception as e:
            error_msg = str(e)
            if 'relation "public.portfolio_symbols" does not exist' in error_msg or 'table "portfolio_symbols" does not exist' in error_msg:
                print(f"❌ Portfolio table doesn't exist. Please create 'portfolio_symbols' table in Supabase with columns: symbol (text), added_at (timestamptz)")
                print("   SQL: CREATE TABLE portfolio_symbols (id SERIAL PRIMARY KEY, symbol TEXT UNIQUE NOT NULL, added_at TIMESTAMPTZ DEFAULT NOW());")
            else:
                print(f"❌ Error adding {symbol} to portfolio: {e}")
            return False
    
    def remove_portfolio_symbol(self, symbol: str) -> dict:
        """Remove a symbol from user's portfolio - returns dict with success status and message"""
        try:
            symbol_upper = symbol.upper().strip()
            
            # Check if symbol has any holdings in portfolio_holdings table
            holdings_result = self.client.table('portfolio_holdings').select('trade_date, quantity').eq('symbol', symbol_upper).execute()
            
            if holdings_result.data:
                # Found holdings - prevent deletion
                total_holdings = sum(holding['quantity'] for holding in holdings_result.data if holding['quantity'] > 0)
                if total_holdings > 0:
                    dates_with_holdings = [holding['trade_date'] for holding in holdings_result.data if holding['quantity'] > 0]
                    return {
                        'success': False,
                        'error': f"Cannot remove {symbol} - it has {total_holdings} shares across {len(dates_with_holdings)} dates. Please sell all shares first."
                    }
            
            # No holdings found, safe to remove
            result = self.client.table('portfolio_symbols').delete().eq('symbol', symbol_upper).execute()
            print(f"✅ Removed {symbol} from portfolio (no holdings found)")
            return {'success': True, 'message': f"Removed {symbol} from portfolio"}
            
        except Exception as e:
            print(f"❌ Error removing {symbol} from portfolio: {e}")
            return {'success': False, 'error': f"Database error: {str(e)}"}
    
    def get_portfolio_symbols(self) -> list:
        """Get all symbols in user's portfolio sorted A-Z"""
        try:
            result = self.client.table('portfolio_symbols').select('*').order('symbol', desc=False).execute()
            symbols = [item['symbol'] for item in result.data] if result.data else []
            print(f"📋 Retrieved {len(symbols)} portfolio symbols (sorted A-Z)")
            return symbols
            
        except Exception as e:
            print(f"❌ Error retrieving portfolio symbols: {e}")
            return []
    
    def get_missing_sector_symbols(self) -> list:
        """Find symbols that have NVDR/Short Sales data but no sector data"""
        try:
            # Get all symbols with NVDR data
            nvdr_result = self.client.table('nvdr_trading').select('symbol').execute()
            nvdr_symbols = set(item['symbol'] for item in nvdr_result.data) if nvdr_result.data else set()
            
            # Get all symbols with Short Sales data  
            short_result = self.client.table('short_sales_trading').select('symbol').execute()
            short_symbols = set(item['symbol'] for item in short_result.data) if short_result.data else set()
            
            # Get all symbols with sector data
            sector_result = self.client.table('sector_data').select('symbol').execute()
            sector_symbols = set(item['symbol'] for item in sector_result.data) if sector_result.data else set()
            
            # Find symbols that have trading data but no sector data
            trading_symbols = nvdr_symbols.union(short_symbols)
            missing_symbols = trading_symbols - sector_symbols
            
            print(f"📊 Found {len(missing_symbols)} symbols with trading data but no sector data: {sorted(missing_symbols)[:10]}...")
            return sorted(missing_symbols)
            
        except Exception as e:
            print(f"❌ Error finding missing sector symbols: {e}")
            return []
    
    def save_portfolio_holding(self, symbol: str, quantity: int, avg_cost_price: float, trade_date: date) -> bool:
        """Save or update a portfolio holding for a specific date"""
        try:
            # Check if holding already exists for this symbol and date
            existing = self.client.table('portfolio_holdings').select('*').eq('symbol', symbol.upper().strip()).eq('trade_date', trade_date.isoformat()).execute()
            
            record = {
                'symbol': symbol.upper().strip(),
                'quantity': quantity,
                'avg_cost_price': avg_cost_price,
                'cost': quantity * avg_cost_price,
                'trade_date': trade_date.isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing holding
                result = self.client.table('portfolio_holdings').update(record).eq('symbol', symbol.upper().strip()).eq('trade_date', trade_date.isoformat()).execute()
                print(f"✅ Updated portfolio holding: {symbol}")
            else:
                # Insert new holding
                record['created_at'] = datetime.now().isoformat()
                result = self.client.table('portfolio_holdings').insert(record).execute()
                print(f"✅ Added new portfolio holding: {symbol}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if 'relation "public.portfolio_holdings" does not exist' in error_msg or 'table "portfolio_holdings" does not exist' in error_msg:
                print(f"❌ Portfolio holdings table doesn't exist. Please create 'portfolio_holdings' table in Supabase.")
                print("   SQL: CREATE TABLE portfolio_holdings (")
                print("     id SERIAL PRIMARY KEY,")
                print("     symbol TEXT NOT NULL,")
                print("     quantity INTEGER NOT NULL,")
                print("     avg_cost_price NUMERIC(10,2) NOT NULL,")
                print("     cost NUMERIC(15,2) NOT NULL,")
                print("     trade_date DATE NOT NULL,")
                print("     created_at TIMESTAMPTZ DEFAULT NOW(),")
                print("     updated_at TIMESTAMPTZ DEFAULT NOW(),")
                print("     UNIQUE(symbol, trade_date)")
                print("   );")
            else:
                print(f"❌ Error saving portfolio holding: {e}")
            return False
    
    def get_portfolio_holdings(self, trade_date: date) -> dict:
        """Get portfolio holdings for a specific date - EXACT date match only"""
        try:
            result = self.client.table('portfolio_holdings').select('*').eq('trade_date', trade_date.isoformat()).order('symbol', desc=False).execute()
            
            holdings = {}
            if result.data:
                for holding in result.data:
                    holdings[holding['symbol']] = {
                        'quantity': holding['quantity'],
                        'avg_cost_price': holding['avg_cost_price'],
                        'cost': holding['cost']
                    }
            
            print(f"📋 Retrieved {len(holdings)} portfolio holdings for {trade_date} (exact date)")
            return holdings
            
        except Exception as e:
            print(f"❌ Error retrieving portfolio holdings: {e}")
            return {}
    
    def get_portfolio_holdings_with_persistence(self, trade_date: date) -> dict:
        """Get portfolio holdings with CRUD timestamp logic - holdings persist until changed - OPTIMIZED"""
        try:
            # Get all portfolio symbols
            portfolio_symbols = self.get_portfolio_symbols()
            if not portfolio_symbols:
                print(f"📋 No portfolio symbols found")
                return {}
            
            # OPTIMIZATION: Single query to get all holdings for all symbols at once
            # Get all holdings for portfolio symbols on or before target date
            result = self.client.table('portfolio_holdings').select('*').in_('symbol', portfolio_symbols).lte('trade_date', trade_date.isoformat()).order('symbol').order('trade_date', desc=True).execute()
            
            if not result.data:
                print(f"📋 No portfolio holdings found for any symbols")
                return {}
            
            # Group by symbol and take the most recent (first) holding for each symbol
            holdings = {}
            for holding in result.data:
                symbol = holding['symbol']
                if symbol not in holdings:  # First (most recent) holding for this symbol
                    holdings[symbol] = {
                        'quantity': holding['quantity'],
                        'avg_cost_price': holding['avg_cost_price'],
                        'cost': holding['cost'],
                        'effective_date': holding['trade_date']  # Track when this holding was set
                    }
            
            print(f"📋 Retrieved {len(holdings)} portfolio holdings for {trade_date} (with persistence, optimized)")
            
            return holdings
            
        except Exception as e:
            print(f"❌ Error retrieving portfolio holdings with persistence: {e}")
            return {}
    
    def get_available_portfolio_dates(self) -> list:
        """Get all available dates that have portfolio holdings"""
        try:
            result = self.client.table('portfolio_holdings').select('trade_date').order('trade_date', desc=True).execute()
            
            dates = list(set(item['trade_date'] for item in result.data)) if result.data else []
            dates.sort(reverse=True)  # Most recent first
            
            print(f"📅 Found {len(dates)} dates with portfolio holdings")
            return dates
            
        except Exception as e:
            print(f"❌ Error retrieving portfolio dates: {e}")
            return []
    
    def delete_portfolio_holding(self, symbol: str, trade_date: date) -> bool:
        """Delete a portfolio holding for a specific symbol and date"""
        try:
            result = self.client.table('portfolio_holdings').delete().eq('symbol', symbol.upper().strip()).eq('trade_date', trade_date.isoformat()).execute()
            print(f"✅ Deleted portfolio holding: {symbol} for {trade_date}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting portfolio holding: {e}")
            return False
    
    def update_data_timestamp(self, data_source: str, trade_date: date, record_count: int = 0, status: str = 'active', error_message: str = None) -> bool:
        """Update the latest timestamp for a data source"""
        try:
            from datetime import datetime
            
            update_data = {
                'latest_trade_date': trade_date.isoformat(),
                'latest_created_at': datetime.now().isoformat(),
                'record_count': record_count,
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            # Try to update existing record first, if it fails, insert new one
            try:
                result = self.client.table('data_timestamps').update(update_data).eq('data_source', data_source).execute()
                if not result.data:
                    # No existing record found, insert new one
                    result = self.client.table('data_timestamps').insert({
                        'data_source': data_source,
                        **update_data
                    }).execute()
            except Exception as e:
                # If update fails, try insert
                result = self.client.table('data_timestamps').insert({
                    'data_source': data_source,
                    **update_data
                }).execute()
            
            print(f"✅ Updated timestamp for {data_source}: {trade_date} ({record_count} records)")
            return True
            
        except Exception as e:
            print(f"❌ Error updating timestamp for {data_source}: {e}")
            return False
    
    def get_latest_data_timestamps(self) -> dict:
        """Get the latest timestamps for all data sources"""
        try:
            result = self.client.table('data_timestamps').select('*').eq('status', 'active').execute()
            
            timestamps = {}
            if result.data:
                for item in result.data:
                    timestamps[item['data_source']] = {
                        'latest_trade_date': item['latest_trade_date'],
                        'latest_created_at': item['latest_created_at'],
                        'record_count': item['record_count'],
                        'status': item['status'],
                        'updated_at': item['updated_at']
                    }
            
            return timestamps
            
        except Exception as e:
            print(f"❌ Error getting latest timestamps: {e}")
            return {}
    
    def get_latest_trade_date(self, data_source: str) -> str:
        """Get the latest trade date for a specific data source"""
        try:
            result = self.client.table('data_timestamps').select('latest_trade_date').eq('data_source', data_source).eq('status', 'active').execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['latest_trade_date']
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting latest trade date for {data_source}: {e}")
            return None


def get_proper_db():
    """Get proper database manager instance"""
    return ProperDatabaseManager()


if __name__ == "__main__":
    # Test the proper database manager
    db = get_proper_db()
    print("✅ Proper database manager initialized")