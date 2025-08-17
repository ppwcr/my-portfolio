-- Create SET Index table in Supabase
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

-- Add RLS (Row Level Security) if needed
-- ALTER TABLE set_index ENABLE ROW LEVEL SECURITY;

-- Sample comment
COMMENT ON TABLE set_index IS 'SET Stock Exchange index data with daily caching';
COMMENT ON COLUMN set_index.trade_date IS 'Trading date for the index data';
COMMENT ON COLUMN set_index.index_name IS 'Name of the index (SET, SET50, etc.)';
COMMENT ON COLUMN set_index.last_value IS 'Last/closing value of the index';
COMMENT ON COLUMN set_index.change_value IS 'Numeric change value';
COMMENT ON COLUMN set_index.change_text IS 'Full change text including percentage';
COMMENT ON COLUMN set_index.volume_thousands IS 'Trading volume in thousands of shares';
COMMENT ON COLUMN set_index.value_million_baht IS 'Trading value in million Baht';