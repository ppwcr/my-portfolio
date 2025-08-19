#!/usr/bin/env python3
"""
Simple script to create the portfolio_holdings table in Supabase
Run this script to set up the database table for portfolio edit mode.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def create_portfolio_table():
    """Create the portfolio_holdings table in Supabase"""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(url, key)
        
        print("🔧 Creating portfolio_holdings table...")
        
        # SQL to create the table
        create_sql = """
        CREATE TABLE IF NOT EXISTS portfolio_holdings (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            avg_cost_price NUMERIC(10,2) NOT NULL DEFAULT 0.00,
            cost NUMERIC(15,2) NOT NULL DEFAULT 0.00,
            trade_date DATE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(symbol, trade_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_symbol ON portfolio_holdings(symbol);
        CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_trade_date ON portfolio_holdings(trade_date);
        CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_symbol_date ON portfolio_holdings(symbol, trade_date);
        """
        
        # Create the trigger function
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_portfolio_holdings_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        DROP TRIGGER IF EXISTS trigger_update_portfolio_holdings_updated_at ON portfolio_holdings;
        CREATE TRIGGER trigger_update_portfolio_holdings_updated_at
            BEFORE UPDATE ON portfolio_holdings
            FOR EACH ROW
            EXECUTE FUNCTION update_portfolio_holdings_updated_at();
        """
        
        # Execute the SQL using Supabase RPC (if available) or direct SQL execution
        print("📄 Note: This script shows the SQL needed. Please run it manually in Supabase SQL Editor:")
        print()
        print("=" * 80)
        print(create_sql)
        print(trigger_sql)
        print("=" * 80)
        print()
        print("🔗 To run this SQL:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the SQL above")
        print("4. Click 'Run' to execute")
        print()
        print("✅ After running the SQL, your portfolio edit mode will work!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🏗️  Portfolio Holdings Table Setup")
    print("=" * 40)
    create_portfolio_table()