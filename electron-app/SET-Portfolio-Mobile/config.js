// Configuration for the SET Portfolio Mobile App

// API Configuration
// Change this to your deployed FastAPI server URL
export const API_CONFIG = {
  // For development - your local server
  LOCAL_URL: 'http://localhost:8000',
  
  // For production - replace with your deployed server URL
  // Examples:
  // PRODUCTION_URL: 'https://your-api.herokuapp.com',
  // PRODUCTION_URL: 'https://your-api.vercel.app',
  // PRODUCTION_URL: 'https://your-domain.com/api',
  PRODUCTION_URL: 'http://localhost:8000', // Update this for production
  
  // Automatically use local for development, production for release
  get BASE_URL() {
    return __DEV__ ? this.LOCAL_URL : this.PRODUCTION_URL;
  },
  
  // Request timeout in milliseconds
  TIMEOUT: 10000,
  
  // Retry configuration
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
};

// App Configuration
export const APP_CONFIG = {
  NAME: 'SET Portfolio Manager',
  VERSION: '1.0.0',
  DESCRIPTION: 'Mobile app for Stock Exchange of Thailand portfolio management',
  
  // Feature flags
  FEATURES: {
    PUSH_NOTIFICATIONS: true,
    AUTO_REFRESH: true,
    OFFLINE_MODE: false,
    BIOMETRIC_AUTH: false,
  },
  
  // UI Configuration
  UI: {
    PRIMARY_COLOR: '#2196F3',
    SECONDARY_COLOR: '#4CAF50',
    ERROR_COLOR: '#F44336',
    WARNING_COLOR: '#FF9800',
    SUCCESS_COLOR: '#4CAF50',
  },
  
  // Data refresh intervals (in milliseconds)
  REFRESH_INTERVALS: {
    DASHBOARD: 30000,    // 30 seconds
    SECTORS: 60000,      // 1 minute
    INVESTOR_DATA: 60000, // 1 minute
  },
};

// Market Configuration
export const MARKET_CONFIG = {
  TRADING_HOURS: {
    MORNING_START: '10:00',
    MORNING_END: '12:30',
    AFTERNOON_START: '14:30',
    AFTERNOON_END: '16:30',
    TIMEZONE: 'Asia/Bangkok',
  },
  
  SUPPORTED_MARKETS: ['SET', 'MAI'],
  
  SECTORS: [
    { name: 'Agriculture & Food Industry', slug: 'agro', icon: '🌾' },
    { name: 'Consumer Products', slug: 'consump', icon: '🛒' },
    { name: 'Financials', slug: 'fincial', icon: '🏦' },
    { name: 'Industrial', slug: 'indus', icon: '🏭' },
    { name: 'Property & Construction', slug: 'propcon', icon: '🏗️' },
    { name: 'Resources', slug: 'resourc', icon: '⛏️' },
    { name: 'Services', slug: 'service', icon: '🔧' },
    { name: 'Technology', slug: 'tech', icon: '💻' },
  ],
};

export default {
  API_CONFIG,
  APP_CONFIG,
  MARKET_CONFIG,
};