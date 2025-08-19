// Supabase client for React Native - Direct database access
import { createClient } from '@supabase/supabase-js';

// Supabase credentials for SET Portfolio Mobile App
const SUPABASE_URL = 'https://dnaxnvxuhzsmkapjguwb.supabase.co';
const SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuYXhudnh1aHpzbWthcGpndXdiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTQwNDc5MSwiZXhwIjoyMDcwOTgwNzkxfQ.sW9MBvYiEDWarshySYzThmJe9GKn09orVxsNrVe_i8c';

class SupabaseService {
  constructor() {
    if (SUPABASE_URL === 'your_supabase_project_url' || SUPABASE_SERVICE_KEY === 'your_supabase_service_key') {
      console.warn('⚠️  Supabase credentials not configured. Using demo data.');
      this.client = null;
      this.demoMode = true;
    } else {
      this.client = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
      this.demoMode = false;
    }
  }

  // Portfolio Summary Data
  async getPortfolioSummary() {
    if (this.demoMode) {
      return this.getDemoPortfolioSummary();
    }

    try {
      // Fetch sector data for portfolio overview
      const { data: sectorData, error: sectorError } = await this.client
        .from('sector_data')
        .select('*')
        .order('trade_date', { ascending: false })
        .limit(1000);

      if (sectorError) {
        console.error('Error fetching sector data:', sectorError);
        return this.getDemoPortfolioSummary();
      }

      // Calculate portfolio summary from sector data
      const totalStocks = sectorData.length;
      const totalValue = sectorData.reduce((sum, item) => sum + (item.value_baht || 0), 0);
      const positiveChanges = sectorData.filter(item => 
        item.change && item.change.includes('+')).length;
      const avgChangePercent = sectorData.length > 0 ? 
        sectorData.reduce((sum, item) => {
          const change = parseFloat((item.percent_change || '0').replace('%', '').replace('+', ''));
          return sum + (isNaN(change) ? 0 : change);
        }, 0) / sectorData.length : 0;

      return {
        total_holdings: totalStocks,
        market_value: Math.round(totalValue),
        day_change: positiveChanges - (totalStocks - positiveChanges), // Net gainers vs losers
        day_change_percent: avgChangePercent,
        last_updated: sectorData[0]?.trade_date || new Date().toISOString(),
        source: 'Supabase Database'
      };
    } catch (error) {
      console.error('Supabase portfolio summary error:', error);
      return this.getDemoPortfolioSummary();
    }
  }

  // Portfolio Dashboard Data (Holdings)
  async getDashboardData() {
    if (this.demoMode) {
      return this.getDemoDashboardData();
    }

    try {
      // Fetch sector data to show as holdings (all symbols)
      const { data: sectorData, error } = await this.client
        .from('sector_data')
        .select('*')
        .order('last_price', { ascending: false })
        .limit(1000);

      if (error) {
        console.error('Error fetching sector data:', error);
        return this.getDemoDashboardData();
      }

      // Transform sector data into portfolio holdings format (only last price)
      const holdings = sectorData.map(item => ({
        symbol: item.symbol || 'N/A',
        name: item.symbol || 'Unknown',
        sector: item.sector || 'Unknown', 
        last_price: item.last_price || 0,
        change: item.change || '0.00',
        percent_change: item.percent_change || '0.00%',
        volume: item.volume_shares || 0,
        value_baht: item.value_baht || 0,
        trade_date: item.trade_date
      }));

      return {
        holdings: holdings,
        summary: await this.getPortfolioSummary(),
        last_updated: new Date().toISOString(),
        source: 'Supabase Database'
      };
    } catch (error) {
      console.error('Supabase dashboard error:', error);
      return this.getDemoDashboardData();
    }
  }

  // Investor Data by Market
  async getInvestorData(market = 'SET') {
    if (this.demoMode) {
      return this.getDemoInvestorData(market);
    }

    try {
      const { data, error } = await this.client
        .from('investor_summary')
        .select('*')
        .eq('market', market.toUpperCase())
        .order('trade_date', { ascending: false })
        .limit(30);

      if (error) {
        console.error('Error fetching investor data:', error);
        return this.getDemoInvestorData(market);
      }

      return {
        market: market,
        data: data,
        chart_data: this.formatInvestorChartData(data),
        last_updated: new Date().toISOString(),
        source: 'Supabase Database'
      };
    } catch (error) {
      console.error('Supabase investor data error:', error);
      return this.getDemoInvestorData(market);
    }
  }

  // Sector Constituents
  async getSectorConstituents(sectorSlug) {
    if (this.demoMode) {
      return this.getDemoSectorData(sectorSlug);
    }

    try {
      const { data, error } = await this.client
        .from('latest_sector_data')
        .select('*')
        .ilike('sector', `%${sectorSlug}%`)
        .order('last_price', { ascending: false })
        .limit(50);

      if (error) {
        console.error('Error fetching sector data:', error);
        return this.getDemoSectorData(sectorSlug);
      }

      return {
        sector: sectorSlug,
        constituents: data,
        total_stocks: data.length,
        last_updated: new Date().toISOString(),
        source: 'Supabase Database'
      };
    } catch (error) {
      console.error('Supabase sector data error:', error);
      return this.getDemoSectorData(sectorSlug);
    }
  }

  // Helper method to format investor data for charts
  formatInvestorChartData(data) {
    return data.map(item => ({
      date: item.trade_date,
      institutions: item.institution_buy_volume || 0,
      foreign: item.foreign_buy_volume || 0,
      local: item.local_buy_volume || 0,
      total_value: item.total_buy_value || 0
    }));
  }

  // Demo Data Methods (when Supabase is not configured)
  getDemoPortfolioSummary() {
    return {
      total_holdings: 15,
      market_value: 2450000,
      day_change: 34500,
      day_change_percent: 1.43,
      last_updated: new Date().toISOString(),
      source: 'Demo Data - Configure Supabase for real data'
    };
  }

  getDemoDashboardData() {
    const demoStocks = [
      { symbol: 'PTT', name: 'PTT Public Company Limited', sector: 'Energy', last_price: 35.50, change: 1.25, percent_change: 3.65 },
      { symbol: 'KBANK', name: 'Kasikornbank Public Company Limited', sector: 'Banking', last_price: 142.00, change: -2.50, percent_change: -1.73 },
      { symbol: 'AOT', name: 'Airports of Thailand Public Company Limited', sector: 'Transportation', last_price: 68.25, change: 0.75, percent_change: 1.11 },
      { symbol: 'CPALL', name: 'CP ALL Public Company Limited', sector: 'Commerce', last_price: 58.00, change: -1.00, percent_change: -1.69 },
      { symbol: 'BBL', name: 'Bangkok Bank Public Company Limited', sector: 'Banking', last_price: 134.50, change: 2.00, percent_change: 1.51 }
    ];

    return {
      holdings: demoStocks,
      summary: this.getDemoPortfolioSummary(),
      last_updated: new Date().toISOString(),
      source: 'Demo Data - Configure Supabase for real data'
    };
  }

  getDemoInvestorData(market) {
    const demoData = Array.from({ length: 10 }, (_, i) => ({
      trade_date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      market: market,
      institution_buy_volume: Math.floor(Math.random() * 1000000),
      foreign_buy_volume: Math.floor(Math.random() * 800000),
      local_buy_volume: Math.floor(Math.random() * 1200000),
      total_buy_value: Math.floor(Math.random() * 5000000)
    }));

    return {
      market: market,
      data: demoData,
      chart_data: this.formatInvestorChartData(demoData),
      last_updated: new Date().toISOString(),
      source: 'Demo Data - Configure Supabase for real data'
    };
  }

  getDemoSectorData(sectorSlug) {
    const demoStocks = [
      { symbol: 'ADVANC', security_name: 'Advanced Info Service', sector_name: sectorSlug, weight: 15.2, last_price: 234.0 },
      { symbol: 'TRUE', security_name: 'True Corporation', sector_name: sectorSlug, weight: 8.7, last_price: 4.12 },
      { symbol: 'DTAC', security_name: 'Total Access Communication', sector_name: sectorSlug, weight: 6.3, last_price: 45.25 },
      { symbol: 'INTUCH', security_name: 'Intouch Holdings', sector_name: sectorSlug, weight: 4.1, last_price: 78.50 }
    ];

    return {
      sector: sectorSlug,
      constituents: demoStocks,
      total_stocks: demoStocks.length,
      last_updated: new Date().toISOString(),
      source: 'Demo Data - Configure Supabase for real data'
    };
  }

  // GET SET Index Data
  async getSetIndexData() {
    if (this.demoMode) {
      return this.getDemoSetIndexData();
    }

    try {
      const { data, error } = await this.client
        .from('set_index')
        .select('*')
        .order('trade_date', { ascending: false })
        .limit(10);

      if (error) {
        console.error('Error fetching SET index data:', error);
        return this.getDemoSetIndexData();
      }

      return {
        set_index: data || [],
        last_updated: new Date().toISOString(),
        source: 'Supabase Database'
      };
    } catch (error) {
      console.error('Supabase SET index error:', error);
      return this.getDemoSetIndexData();
    }
  }

  getDemoSetIndexData() {
    return {
      set_index: [
        { index_name: 'SET', last_value: 1425.67, change_text: '+12.45 (+0.88%)', volume_thousands: 45230, value_million_baht: 52340 },
        { index_name: 'SET50', last_value: 952.34, change_text: '+8.12 (+0.86%)', volume_thousands: 38450, value_million_baht: 41200 },
        { index_name: 'SET100', last_value: 1890.45, change_text: '+15.67 (+0.84%)', volume_thousands: 42100, value_million_baht: 48900 }
      ],
      last_updated: new Date().toISOString(),
      source: 'Demo Data - Configure Supabase for real data'
    };
  }

  // Check connection status
  async testConnection() {
    if (this.demoMode) {
      return {
        connected: false,
        message: 'Demo mode - Supabase not configured',
        demo: true
      };
    }

    try {
      const { data, error } = await this.client
        .from('investor_summary')
        .select('trade_date')
        .limit(1);

      return {
        connected: !error,
        message: error ? `Connection failed: ${error.message}` : 'Connected to Supabase',
        demo: false,
        data_available: data && data.length > 0
      };
    } catch (error) {
      return {
        connected: false,
        message: `Connection error: ${error.message}`,
        demo: false
      };
    }
  }
}

export default new SupabaseService();