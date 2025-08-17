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
            return float(cleaned)
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
                    
                    'trade_date': trade_date.isoformat() if trade_date else None,
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            if not records:
                print("❌ No valid NVDR records found")
                return False
            
            # Insert to nvdr_trading table
            result = self.client.table('nvdr_trading').insert(records).execute()
            print(f"✅ Saved {len(records)} NVDR trading records")
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
                        
                        'trade_date': trade_date.isoformat() if trade_date else None,
                        'created_at': datetime.now().isoformat()
                    }
                    records.append(record)
            
            if not records:
                print("❌ No valid Short Sales records found")
                return False
            
            # Insert to short_sales_trading table
            result = self.client.table('short_sales_trading').insert(records).execute()
            print(f"✅ Saved {len(records)} Short Sales trading records")
            return True
            
        except Exception as e:
            print(f"❌ Error saving Short Sales trading data: {e}")
            return False
    
    def save_sector_data(self, csv_data: pd.DataFrame, sector_name: str, trade_date: Optional[date] = None) -> bool:
        """Save sector constituents data to Supabase - keeping existing sector_data table"""
        try:
            # Convert DataFrame to list of dictionaries for the existing sector_data table
            records = []
            for _, row in csv_data.iterrows():
                record = {
                    'symbol': str(row.get('Symbol', '')).strip(),
                    'open_price': self._parse_number(row.get('Open', '')),
                    'high_price': self._parse_number(row.get('High', '')),
                    'low_price': self._parse_number(row.get('Low', '')),
                    'last_price': self._parse_number(row.get('Last', '')),
                    'change': str(row.get('Change', '')),
                    'percent_change': str(row.get('% Change', '')),
                    'bid': str(row.get('Bid', '')),
                    'offer': str(row.get('Offer', '')),
                    'volume_shares': self._parse_integer(row.get('Volume (Shares)', '')),
                    'value_baht': self._parse_number(row.get('Value (\'000 Baht)', '')),
                    'sector': sector_name,
                    'trade_date': trade_date.isoformat() if trade_date else None,
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            # Insert data to sector_data table (existing table)
            result = self.client.table('sector_data').insert(records).execute()
            print(f"✅ Saved {len(records)} {sector_name} sector records")
            return True
            
        except Exception as e:
            print(f"❌ Error saving {sector_name} sector data: {e}")
            return False


def get_proper_db():
    """Get proper database manager instance"""
    return ProperDatabaseManager()


if __name__ == "__main__":
    # Test the proper database manager
    db = get_proper_db()
    print("✅ Proper database manager initialized")