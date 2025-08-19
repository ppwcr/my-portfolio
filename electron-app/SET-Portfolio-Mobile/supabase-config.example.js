// Copy this file to 'supabase-config.js' and add your real Supabase credentials
// Then update the import in src/services/supabaseClient.js

export const SUPABASE_CONFIG = {
  // Get these from your Supabase project settings
  url: 'your_supabase_project_url',
  anonKey: 'your_supabase_anon_key',
  
  // Example:
  // url: 'https://abcdefghijklmnop.supabase.co',
  // anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
};

// Tables that the mobile app will read from:
// - investor_summary: Investor type data (SET/MAI markets)
// - sector_data: Sector constituent data for 8 SET sectors
// - nvdr_trading: NVDR trading-by-stock data
// - short_sales_trading: Short sales data

// Note: The mobile app only reads data, it doesn't write to the database
// All scraping and data updates should be done through your main FastAPI app