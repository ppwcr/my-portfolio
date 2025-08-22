-- Create data_timestamps table for tracking latest available data dates
-- This table allows the web application to know which dates have the most recent data for each source

CREATE TABLE data_timestamps (
    id SERIAL PRIMARY KEY,
    data_source TEXT NOT NULL UNIQUE,  -- 'sector_data', 'investor_summary', 'nvdr_trading', 'short_sales_trading', 'set_index'
    latest_trade_date DATE NOT NULL,
    latest_created_at TIMESTAMPTZ NOT NULL,
    record_count INTEGER DEFAULT 0,  -- Number of records for this date
    status TEXT DEFAULT 'active',  -- 'active', 'processing', 'error'
    error_message TEXT,  -- Error message if status is 'error'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_data_timestamps_source ON data_timestamps(data_source);
CREATE INDEX idx_data_timestamps_date ON data_timestamps(latest_trade_date);
CREATE INDEX idx_data_timestamps_status ON data_timestamps(status);

-- Create a trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_data_timestamps_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_data_timestamps_updated_at
    BEFORE UPDATE ON data_timestamps
    FOR EACH ROW
    EXECUTE FUNCTION update_data_timestamps_updated_at();

-- Insert initial records for all data sources
INSERT INTO data_timestamps (data_source, latest_trade_date, latest_created_at, record_count, status) VALUES
('sector_data', CURRENT_DATE, NOW(), 0, 'active'),
('investor_summary', CURRENT_DATE, NOW(), 0, 'active'),
('nvdr_trading', CURRENT_DATE, NOW(), 0, 'active'),
('short_sales_trading', CURRENT_DATE, NOW(), 0, 'active'),
('set_index', CURRENT_DATE, NOW(), 0, 'active')
ON CONFLICT (data_source) DO NOTHING;

-- Create a view for easy access to latest timestamps
CREATE OR REPLACE VIEW latest_data_timestamps AS
SELECT 
    data_source,
    latest_trade_date,
    latest_created_at,
    record_count,
    status,
    error_message,
    updated_at
FROM data_timestamps 
WHERE status = 'active'
ORDER BY data_source;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT ON latest_data_timestamps TO anon;
-- GRANT SELECT ON latest_data_timestamps TO authenticated;
