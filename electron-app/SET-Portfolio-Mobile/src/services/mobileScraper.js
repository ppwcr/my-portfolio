// Mobile Web Scraping Service for SET Portfolio - React Native Compatible
import AsyncStorage from '@react-native-async-storage/async-storage';
import { XMLParser } from 'fast-xml-parser';

class MobileScraper {
  constructor() {
    this.baseUrl = 'https://www.set.or.th';
    this.userAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15';
    this.parser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
      textNodeName: 'text',
    });
  }

  // Fetch HTML with mobile user agent
  async fetchHTML(url, options = {}) {
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'User-Agent': this.userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.text();
    } catch (error) {
      console.error('Fetch error:', error);
      throw error;
    }
  }

  // Parse HTML using regex and string methods (React Native compatible)
  parseHTML(html, selector) {
    try {
      // Simple HTML parsing using regex - not as robust as Cheerio but works in RN
      if (selector.includes('class=')) {
        const className = selector.match(/class="([^"]+)"/)?.[1];
        if (className) {
          const regex = new RegExp(`<[^>]*class="[^"]*${className}[^"]*"[^>]*>(.*?)<\/[^>]+>`, 'gis');
          const matches = html.match(regex);
          return matches || [];
        }
      }
      
      if (selector.includes('id=')) {
        const idName = selector.match(/id="([^"]+)"/)?.[1];
        if (idName) {
          const regex = new RegExp(`<[^>]*id="${idName}"[^>]*>(.*?)<\/[^>]+>`, 'gis');
          const matches = html.match(regex);
          return matches || [];
        }
      }

      // Generic tag search
      const tagName = selector.replace(/[<>]/g, '');
      const regex = new RegExp(`<${tagName}[^>]*>(.*?)<\/${tagName}>`, 'gis');
      const matches = html.match(regex);
      return matches || [];
    } catch (error) {
      console.error('Parse error:', error);
      return [];
    }
  }

  // Extract text content from HTML
  extractText(htmlString) {
    try {
      // Remove HTML tags and get text content
      const text = htmlString.replace(/<[^>]*>/g, '').trim();
      return text;
    } catch (error) {
      console.error('Extract text error:', error);
      return '';
    }
  }

  // Extract table data from HTML
  extractTableData(html) {
    try {
      const tables = this.parseHTML(html, 'table');
      const tableData = [];

      tables.forEach(table => {
        const rows = this.parseHTML(table, 'tr');
        rows.forEach(row => {
          const cells = this.parseHTML(row, 'td');
          if (cells.length > 0) {
            const rowData = cells.map(cell => this.extractText(cell));
            tableData.push(rowData);
          }
        });
      });

      return tableData;
    } catch (error) {
      console.error('Extract table error:', error);
      return [];
    }
  }

  // Scrape SET Market Summary
  async scrapeMarketSummary() {
    try {
      console.log('📊 Scraping SET market summary...');
      
      // For demo purposes, let's use a simpler approach or mock data
      // In production, you'd parse the actual SET website HTML
      
      const marketData = {
        setIndex: '1,234.56',
        setChange: '+12.34',
        setPercentChange: '+1.02%',
        volume: '45,678,901',
        value: '67,890.12',
        timestamp: new Date().toISOString(),
        source: 'Mobile Scraper Demo',
      };

      console.log('✅ Market summary scraped:', marketData);
      return marketData;

    } catch (error) {
      console.error('❌ Market summary scrape failed:', error);
      
      // Return demo data if scraping fails
      return {
        setIndex: '1,234.56 (Demo)',
        setChange: '+12.34',
        setPercentChange: '+1.02%',
        volume: '45,678,901',
        value: '67,890.12 Million',
        timestamp: new Date().toISOString(),
        source: 'Demo Data - Scraping Failed',
        error: error.message,
      };
    }
  }

  // Scrape Stock Quote
  async scrapeStockQuote(symbol) {
    try {
      console.log(`📈 Scraping stock quote for ${symbol}...`);
      
      // For demo purposes, generate realistic demo data
      const basePrice = Math.random() * 100 + 10;
      const change = (Math.random() - 0.5) * 10;
      const percentChange = (change / basePrice) * 100;

      const stockData = {
        symbol: symbol.toUpperCase(),
        lastPrice: basePrice.toFixed(2),
        change: change.toFixed(2),
        percentChange: percentChange.toFixed(2) + '%',
        volume: Math.floor(Math.random() * 1000000).toLocaleString(),
        high: (basePrice + Math.random() * 5).toFixed(2),
        low: (basePrice - Math.random() * 5).toFixed(2),
        timestamp: new Date().toISOString(),
        source: 'Mobile Scraper Demo',
      };

      console.log(`✅ Stock ${symbol} scraped:`, stockData);
      return stockData;

    } catch (error) {
      console.error(`❌ Stock ${symbol} scrape failed:`, error);
      return {
        symbol: symbol.toUpperCase(),
        lastPrice: '0.00',
        change: '0.00',
        percentChange: '0.00%',
        volume: '0',
        high: '0.00',
        low: '0.00',
        timestamp: new Date().toISOString(),
        source: 'Demo Data - Error',
        error: error.message,
      };
    }
  }

  // Scrape Sector Data
  async scrapeSectorData(sectorSlug) {
    try {
      console.log(`🏭 Scraping sector data for ${sectorSlug}...`);
      
      // Generate demo sector data
      const sectorStocks = [
        'ADVANC', 'AOT', 'AWC', 'BANPU', 'BBL', 'BDMS', 'BEM', 'BGRIM',
        'BH', 'BTS', 'CBG', 'CENTEL', 'CHG', 'CK', 'CKP', 'COM7',
        'CPALL', 'CPF', 'CPN', 'CRC', 'DELTA', 'DTAC', 'EA', 'EGCO'
      ];

      const stocks = sectorStocks.slice(0, 8).map(symbol => {
        const basePrice = Math.random() * 200 + 20;
        const change = (Math.random() - 0.5) * 20;
        return {
          symbol,
          lastPrice: basePrice.toFixed(2),
          change: change.toFixed(2),
          percentChange: ((change / basePrice) * 100).toFixed(2) + '%',
          volume: Math.floor(Math.random() * 1000000).toLocaleString(),
        };
      });

      const sectorData = {
        sector: sectorSlug,
        stocks,
        timestamp: new Date().toISOString(),
        source: 'Mobile Scraper Demo',
      };

      console.log(`✅ Sector ${sectorSlug} scraped: ${stocks.length} stocks`);
      return sectorData;

    } catch (error) {
      console.error(`❌ Sector ${sectorSlug} scrape failed:`, error);
      return {
        sector: sectorSlug,
        stocks: [],
        timestamp: new Date().toISOString(),
        source: 'Demo Data - Error',
        error: error.message,
      };
    }
  }

  // Scrape Multiple Stocks
  async scrapeMultipleStocks(symbols) {
    try {
      console.log(`📊 Scraping ${symbols.length} stocks...`);
      
      const results = await Promise.allSettled(
        symbols.map(symbol => this.scrapeStockQuote(symbol))
      );

      const stocks = results
        .filter(result => result.status === 'fulfilled')
        .map(result => result.value);

      const failed = results
        .filter(result => result.status === 'rejected')
        .length;

      console.log(`✅ Scraped ${stocks.length} stocks, ${failed} failed`);
      return stocks;

    } catch (error) {
      console.error('❌ Multiple stocks scrape failed:', error);
      throw error;
    }
  }

  // Real scraping method using fetch (for actual implementation)
  async scrapeRealData(url, config = {}) {
    try {
      console.log(`🕷️ Real scraping: ${url}`);
      
      const html = await this.fetchHTML(url);
      const tableData = this.extractTableData(html);
      
      return {
        url,
        tableData,
        timestamp: new Date().toISOString(),
        source: 'Real Mobile Scraping',
      };
    } catch (error) {
      console.error('Real scraping failed:', error);
      throw error;
    }
  }

  // Save scraped data locally
  async saveData(key, data) {
    try {
      const jsonData = JSON.stringify(data);
      await AsyncStorage.setItem(key, jsonData);
      console.log(`💾 Data saved to ${key}`);
    } catch (error) {
      console.error('❌ Save data failed:', error);
      throw error;
    }
  }

  // Load saved data
  async loadData(key) {
    try {
      const jsonData = await AsyncStorage.getItem(key);
      if (jsonData) {
        const data = JSON.parse(jsonData);
        console.log(`📂 Data loaded from ${key}`);
        return data;
      }
      return null;
    } catch (error) {
      console.error('❌ Load data failed:', error);
      return null;
    }
  }

  // Get all saved data keys
  async getAllKeys() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys.filter(key => key.startsWith('scraper_'));
    } catch (error) {
      console.error('❌ Get keys failed:', error);
      return [];
    }
  }

  // Clear all saved data
  async clearAllData() {
    try {
      const keys = await this.getAllKeys();
      await AsyncStorage.multiRemove(keys);
      console.log(`🗑️ Cleared ${keys.length} saved datasets`);
    } catch (error) {
      console.error('❌ Clear data failed:', error);
      throw error;
    }
  }

  // Use Jina.ai proxy for CORS-free scraping
  async scrapeWithJina(url) {
    try {
      const jinaUrl = `https://r.jina.ai/${url}`;
      const response = await fetch(jinaUrl, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': this.userAgent,
        },
      });

      const data = await response.json();
      return data.content || data.text;
    } catch (error) {
      console.error('Jina scrape failed:', error);
      throw error;
    }
  }
}

export default new MobileScraper();