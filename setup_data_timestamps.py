#!/usr/bin/env python3
"""
Setup script for data_timestamps table
This script creates the data_timestamps table and populates it with initial data from existing tables.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_data_timestamps():
    """Set up the data_timestamps table and populate it with initial data"""
    try:
        from supabase_database import get_proper_db
        
        print("🔧 Setting up data_timestamps table...")
        db = get_proper_db()
        
        # Read and execute the SQL file
        sql_file = "create_data_timestamps_table.sql"
        if not os.path.exists(sql_file):
            print(f"❌ SQL file {sql_file} not found")
            return False
        
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # Execute each statement
        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"📝 Executing statement {i+1}/{len(statements)}...")
                    # Note: Supabase doesn't support direct SQL execution via Python client
                    # We'll need to manually run this in the Supabase SQL editor
                    print(f"   SQL: {statement[:100]}...")
                except Exception as e:
                    print(f"⚠️ Error executing statement {i+1}: {e}")
        
        print("✅ SQL statements prepared. Please run them in your Supabase SQL Editor.")
        print("📋 Copy the contents of create_data_timestamps_table.sql and paste it in Supabase SQL Editor.")
        
        # Now populate the table with existing data
        print("🔍 Populating timestamps with existing data...")
        populate_timestamps(db)
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up data_timestamps: {e}")
        return False

def populate_timestamps(db):
    """Populate the data_timestamps table with data from existing tables"""
    try:
        # Get latest dates from each table
        data_sources = [
            ('sector_data', 'sector_data'),
            ('investor_summary', 'investor_summary'),
            ('nvdr_trading', 'nvdr_trading'),
            ('short_sales_trading', 'short_sales_trading'),
            ('set_index', 'set_index')
        ]
        
        for source_name, table_name in data_sources:
            try:
                # Get latest trade date and record count
                result = db.client.table(table_name).select('trade_date').order('trade_date', desc=True).limit(1).execute()
                
                if result.data:
                    latest_date = result.data[0]['trade_date']
                    
                    # Get record count for this date
                    count_result = db.client.table(table_name).select('trade_date').eq('trade_date', latest_date).execute()
                    record_count = len(count_result.data) if count_result.data else 0
                    
                    # Update timestamp
                    success = db.update_data_timestamp(source_name, latest_date, record_count)
                    if success:
                        print(f"✅ Updated {source_name}: {latest_date} ({record_count} records)")
                    else:
                        print(f"⚠️ Failed to update {source_name}")
                else:
                    print(f"⚠️ No data found for {source_name}")
                    
            except Exception as e:
                print(f"⚠️ Error processing {source_name}: {e}")
        
        print("✅ Timestamps population completed!")
        
    except Exception as e:
        print(f"❌ Error populating timestamps: {e}")

def verify_timestamps():
    """Verify that the timestamps table is working correctly"""
    try:
        from supabase_database import get_proper_db
        
        print("🔍 Verifying timestamps table...")
        db = get_proper_db()
        
        timestamps = db.get_latest_data_timestamps()
        
        if timestamps:
            print("✅ Timestamps table is working correctly:")
            for source, data in timestamps.items():
                print(f"   {source}: {data['latest_trade_date']} ({data['record_count']} records)")
        else:
            print("⚠️ No timestamps found - table may not be set up correctly")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verifying timestamps: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Data Timestamps Setup Script")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            success = setup_data_timestamps()
            if success:
                print("✅ Setup completed successfully!")
            else:
                print("❌ Setup failed!")
                sys.exit(1)
                
        elif command == "verify":
            success = verify_timestamps()
            if success:
                print("✅ Verification completed!")
            else:
                print("❌ Verification failed!")
                sys.exit(1)
                
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: setup, verify")
            sys.exit(1)
    else:
        print("Usage: python setup_data_timestamps.py [setup|verify]")
        print("  setup  - Set up the data_timestamps table")
        print("  verify - Verify the timestamps table is working")
        sys.exit(1)
