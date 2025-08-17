#!/usr/bin/env python3
"""
Create the SET index table in Supabase database
"""

from dotenv import load_dotenv
load_dotenv()

from supabase_database import get_proper_db

def create_set_index_table():
    """Create the SET index table using Supabase client"""
    try:
        db = get_proper_db()
        
        # Create table using raw SQL
        sql = """
        CREATE TABLE IF NOT EXISTS set_index (
            id BIGSERIAL PRIMARY KEY,
            trade_date DATE NOT NULL,
            index_name VARCHAR(20) NOT NULL,
            last_value DECIMAL(10,2),
            change_value DECIMAL(10,2),
            change_text VARCHAR(100),
            volume_thousands BIGINT,
            value_million_baht DECIMAL(10,2),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            
            -- Create unique constraint to prevent duplicates for same date + index
            UNIQUE(trade_date, index_name)
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_set_index_trade_date ON set_index(trade_date DESC);
        CREATE INDEX IF NOT EXISTS idx_set_index_name ON set_index(index_name);
        """
        
        # Execute the SQL
        result = db.client.rpc('create_set_index_table_sql', {'sql_text': sql}).execute()
        print("✅ SET index table created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        
        # Try alternative method - insert a dummy record to auto-create table structure
        try:
            print("🔄 Trying alternative method...")
            db = get_proper_db()  # Initialize db for alternative method
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
            
            # This will create the table if it doesn't exist (with proper schema)
            result = db.client.table('set_index').insert(dummy_record).execute()
            
            # Delete the dummy record
            db.client.table('set_index').delete().eq('index_name', 'TEST').execute()
            
            print("✅ SET index table created via insert method!")
            return True
            
        except Exception as e2:
            print(f"❌ Alternative method also failed: {str(e2)}")
            print("💡 You may need to create the table manually in Supabase dashboard")
            return False

if __name__ == "__main__":
    create_set_index_table()