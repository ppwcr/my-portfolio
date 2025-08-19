// API service for SET Portfolio - Now using direct Supabase connection
import { API_CONFIG } from '../../config';
import SupabaseService from './supabaseClient';

class PortfolioAPI {
  constructor(baseUrl = API_CONFIG.BASE_URL) {
    this.baseUrl = baseUrl;
    this.timeout = API_CONFIG.TIMEOUT;
    this.maxRetries = API_CONFIG.MAX_RETRIES;
    this.retryDelay = API_CONFIG.RETRY_DELAY;
    this.useSupabase = true; // Use Supabase directly instead of FastAPI
  }

  async fetchWithTimeout(url, options = {}, timeout = this.timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // Portfolio Dashboard Data
  async getDashboardData() {
    if (this.useSupabase) {
      return await SupabaseService.getDashboardData();
    }
    
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/api/portfolio/dashboard`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Fallback to Supabase if FastAPI fails
      return await SupabaseService.getDashboardData();
    }
  }

  async getPortfolioSummary() {
    if (this.useSupabase) {
      return await SupabaseService.getPortfolioSummary();
    }
    
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/api/portfolio/summary`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching portfolio summary:', error);
      // Fallback to Supabase if FastAPI fails
      return await SupabaseService.getPortfolioSummary();
    }
  }

  // Sector Data
  async getSectorConstituents(sectorSlug) {
    if (this.useSupabase) {
      return await SupabaseService.getSectorConstituents(sectorSlug);
    }
    
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/sector/constituents.csv?slug=${sectorSlug}`
      );
      return await response.text();
    } catch (error) {
      console.error('Error fetching sector constituents:', error);
      // Fallback to Supabase if FastAPI fails
      return await SupabaseService.getSectorConstituents(sectorSlug);
    }
  }

  // Investor Data
  async getInvestorData(market = 'SET') {
    if (this.useSupabase) {
      return await SupabaseService.getInvestorData(market);
    }
    
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/investor/chart.json?market=${market}`
      );
      return await response.json();
    } catch (error) {
      console.error('Error fetching investor data:', error);
      // Fallback to Supabase if FastAPI fails
      return await SupabaseService.getInvestorData(market);
    }
  }

  async getInvestorTable(market = 'SET') {
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/investor/table.csv?market=${market}`
      );
      return await response.text();
    } catch (error) {
      console.error('Error fetching investor table:', error);
      throw error;
    }
  }

  // Progress/Status
  async getProgressStatus() {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/api/progress/status`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching progress status:', error);
      throw error;
    }
  }

  // Export Functions
  async downloadNVDRExcel() {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/api/nvdr/export.xlsx`);
      return await response.blob();
    } catch (error) {
      console.error('Error downloading NVDR Excel:', error);
      throw error;
    }
  }

  async downloadShortSalesExcel() {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/api/short-sales/export.xlsx`);
      return await response.blob();
    } catch (error) {
      console.error('Error downloading Short Sales Excel:', error);
      throw error;
    }
  }

  // Database Operations
  async saveToDatabase() {
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/save-to-database`,
        { method: 'POST' }
      );
      return await response.json();
    } catch (error) {
      console.error('Error saving to database:', error);
      throw error;
    }
  }
}

export default new PortfolioAPI();