-- Create portfolio_holdings table for storing user portfolio data by date
-- This table allows users to track their holdings (quantity, avg cost) for different dates

CREATE TABLE portfolio_holdings (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_cost_price NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    cost NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    trade_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure each symbol can only have one entry per date
    UNIQUE(symbol, trade_date)
);

-- Create indexes for better query performance
CREATE INDEX idx_portfolio_holdings_symbol ON portfolio_holdings(symbol);
CREATE INDEX idx_portfolio_holdings_trade_date ON portfolio_holdings(trade_date);
CREATE INDEX idx_portfolio_holdings_symbol_date ON portfolio_holdings(symbol, trade_date);

-- Create a trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_portfolio_holdings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_portfolio_holdings_updated_at
    BEFORE UPDATE ON portfolio_holdings
    FOR EACH ROW
    EXECUTE FUNCTION update_portfolio_holdings_updated_at();

-- Sample data insertion (optional - for testing)
-- INSERT INTO portfolio_holdings (symbol, quantity, avg_cost_price, cost, trade_date) VALUES
-- ('AAPL', 100, 150.00, 15000.00, '2025-08-19'),
-- ('AOT', 500, 72.50, 36250.00, '2025-08-19'),
-- ('PTT', 200, 35.75, 7150.00, '2025-08-19');