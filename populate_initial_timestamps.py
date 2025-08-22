#!/usr/bin/env python3
"""
Populate initial timestamps from existing data
This script populates the data_timestamps table with data from existing tables.
Run this after creating the data_timestamps table in Supabase.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def populate_initial_timestamps():
    """Populate the data_timestamps table with initial data from existing tables"""
    try:
        from supabase_database import get_proper_db
        
        print("🔍 Populating initial timestamps from existing data...")
        db = get_proper_db()
        
        # Get latest dates from each table
        data_sources = [
            ('sector_data', 'sector_data'),
            ('investor_summary', 'investor_summary'),
            ('nvdr_trading', 'nvdr_trading'),
            ('short_sales_trading', 'short_sales_trading'),
            ('set_index', 'set_index')
        ]
        
        success_count = 0
        total_count = len(data_sources)
        
        for source_name, table_name in data_sources:
            try:
                print(f"📊 Processing {source_name}...")
                
                # Get latest trade date and record count
                result = db.client.table(table_name).select('trade_date').order('trade_date', desc=True).limit(1).execute()
                
                if result.data:
                    latest_date_str = result.data[0]['trade_date']
                    
                    # Convert string date to date object
                    from datetime import datetime
                    latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
                    
                    # Get record count for this date
                    count_result = db.client.table(table_name).select('trade_date').eq('trade_date', latest_date_str).execute()
                    record_count = len(count_result.data) if count_result.data else 0
                    
                    # Update timestamp
                    success = db.update_data_timestamp(source_name, latest_date, record_count)
                    if success:
                        print(f"✅ Updated {source_name}: {latest_date} ({record_count} records)")
                        success_count += 1
                    else:
                        print(f"⚠️ Failed to update {source_name}")
                else:
                    print(f"⚠️ No data found for {source_name}")
                    
            except Exception as e:
                print(f"⚠️ Error processing {source_name}: {e}")
        
        print(f"✅ Timestamps population completed! {success_count}/{total_count} sources updated.")
        
        # Verify the results
        print("\n🔍 Verifying results...")
        timestamps = db.get_latest_data_timestamps()
        
        if timestamps:
            print("✅ Current timestamps:")
            for source, data in timestamps.items():
                print(f"   {source}: {data['latest_trade_date']} ({data['record_count']} records)")
        else:
            print("⚠️ No timestamps found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error populating timestamps: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initial Timestamps Population Script")
    print("=" * 50)
    
    success = populate_initial_timestamps()
    if success:
        print("\n✅ Population completed successfully!")
    else:
        print("\n❌ Population failed!")
        sys.exit(1)
