import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import MobileScraper from '../services/mobileScraper';

const ScrapingScreen = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [stockSymbol, setStockSymbol] = useState('PTT');
  const [savedData, setSavedData] = useState([]);

  useEffect(() => {
    loadSavedData();
  }, []);

  const loadSavedData = async () => {
    try {
      const keys = await MobileScraper.getAllKeys();
      const dataPromises = keys.map(async (key) => {
        const data = await MobileScraper.loadData(key);
        return { key, data };
      });
      const allData = await Promise.all(dataPromises);
      setSavedData(allData);
    } catch (error) {
      console.error('Load saved data error:', error);
    }
  };

  const handleScrapeMarket = async () => {
    setLoading(true);
    try {
      const marketData = await MobileScraper.scrapeMarketSummary();
      setResults([{ type: 'Market Summary', data: marketData }]);
      
      // Save to local storage
      await MobileScraper.saveData('scraper_market', marketData);
      loadSavedData();
      
      Alert.alert('Success', 'Market data scraped successfully!');
    } catch (error) {
      Alert.alert('Error', `Failed to scrape market data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScrapeStock = async () => {
    if (!stockSymbol.trim()) {
      Alert.alert('Error', 'Please enter a stock symbol');
      return;
    }

    setLoading(true);
    try {
      const stockData = await MobileScraper.scrapeStockQuote(stockSymbol.toUpperCase());
      setResults([{ type: 'Stock Quote', data: stockData }]);
      
      // Save to local storage
      await MobileScraper.saveData(`scraper_stock_${stockSymbol}`, stockData);
      loadSavedData();
      
      Alert.alert('Success', `Stock ${stockSymbol} scraped successfully!`);
    } catch (error) {
      Alert.alert('Error', `Failed to scrape stock data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScrapeSector = async (sectorSlug) => {
    setLoading(true);
    try {
      const sectorData = await MobileScraper.scrapeSectorData(sectorSlug);
      setResults([{ type: 'Sector Data', data: sectorData }]);
      
      // Save to local storage
      await MobileScraper.saveData(`scraper_sector_${sectorSlug}`, sectorData);
      loadSavedData();
      
      Alert.alert('Success', `Sector ${sectorSlug} scraped successfully!`);
    } catch (error) {
      Alert.alert('Error', `Failed to scrape sector data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScrapeMultiple = async () => {
    const symbols = ['PTT', 'AOT', 'BBL', 'KBANK', 'CPALL'];
    setLoading(true);
    try {
      const stocksData = await MobileScraper.scrapeMultipleStocks(symbols);
      setResults([{ type: 'Multiple Stocks', data: stocksData }]);
      
      // Save to local storage
      await MobileScraper.saveData('scraper_multiple', stocksData);
      loadSavedData();
      
      Alert.alert('Success', `Scraped ${stocksData.length} stocks successfully!`);
    } catch (error) {
      Alert.alert('Error', `Failed to scrape multiple stocks: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearData = async () => {
    Alert.alert(
      'Clear All Data',
      'This will delete all saved scraping data. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await MobileScraper.clearAllData();
              setSavedData([]);
              setResults([]);
              Alert.alert('Success', 'All data cleared!');
            } catch (error) {
              Alert.alert('Error', 'Failed to clear data');
            }
          },
        },
      ]
    );
  };

  const formatData = (data) => {
    if (typeof data === 'object') {
      return JSON.stringify(data, null, 2);
    }
    return String(data);
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>📱 Mobile Web Scraping</Text>
      <Text style={styles.subtitle}>
        Scrape SET data directly on mobile device
      </Text>

      {/* Scraping Controls */}
      <View style={styles.controlsSection}>
        <Text style={styles.sectionTitle}>Scraping Actions</Text>
        
        <TouchableOpacity
          style={[styles.actionButton, loading && styles.buttonDisabled]}
          onPress={handleScrapeMarket}
          disabled={loading}
        >
          <Text style={styles.actionButtonText}>📊 Scrape Market Summary</Text>
        </TouchableOpacity>

        <View style={styles.stockInputSection}>
          <TextInput
            style={styles.stockInput}
            value={stockSymbol}
            onChangeText={setStockSymbol}
            placeholder="Enter stock symbol (e.g., PTT)"
            autoCapitalize="characters"
            maxLength={10}
          />
          <TouchableOpacity
            style={[styles.actionButton, loading && styles.buttonDisabled]}
            onPress={handleScrapeStock}
            disabled={loading}
          >
            <Text style={styles.actionButtonText}>📈 Scrape Stock</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={[styles.actionButton, loading && styles.buttonDisabled]}
          onPress={handleScrapeMultiple}
          disabled={loading}
        >
          <Text style={styles.actionButtonText}>📊 Scrape Top 5 Stocks</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, loading && styles.buttonDisabled]}
          onPress={() => handleScrapeSector('tech')}
          disabled={loading}
        >
          <Text style={styles.actionButtonText}>💻 Scrape Tech Sector</Text>
        </TouchableOpacity>
      </View>

      {/* Loading Indicator */}
      {loading && (
        <View style={styles.loadingSection}>
          <ActivityIndicator size="large" color="#2196F3" />
          <Text style={styles.loadingText}>Scraping data...</Text>
        </View>
      )}

      {/* Recent Results */}
      {results.length > 0 && (
        <View style={styles.resultsSection}>
          <Text style={styles.sectionTitle}>Latest Results</Text>
          {results.map((result, index) => (
            <View key={index} style={styles.resultCard}>
              <Text style={styles.resultType}>{result.type}</Text>
              <Text style={styles.resultData}>
                {formatData(result.data).substring(0, 500)}
                {formatData(result.data).length > 500 ? '...' : ''}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Saved Data */}
      <View style={styles.savedSection}>
        <Text style={styles.sectionTitle}>
          Saved Data ({savedData.length} datasets)
        </Text>
        
        {savedData.length > 0 ? (
          <>
            {savedData.map((item, index) => (
              <View key={index} style={styles.savedItem}>
                <Text style={styles.savedKey}>{item.key}</Text>
                <Text style={styles.savedTimestamp}>
                  {new Date(item.data?.timestamp).toLocaleString()}
                </Text>
              </View>
            ))}
            
            <TouchableOpacity
              style={styles.clearButton}
              onPress={handleClearData}
            >
              <Text style={styles.clearButtonText}>🗑️ Clear All Data</Text>
            </TouchableOpacity>
          </>
        ) : (
          <Text style={styles.noDataText}>No saved data yet</Text>
        )}
      </View>

      {/* Instructions */}
      <View style={styles.instructionsSection}>
        <Text style={styles.sectionTitle}>How Mobile Scraping Works</Text>
        <Text style={styles.instructionText}>
          • Uses JavaScript fetch() and Cheerio for HTML parsing{'\n'}
          • Stores data locally on device using AsyncStorage{'\n'}
          • Works offline once data is cached{'\n'}
          • No Python required - pure JavaScript{'\n'}
          • Can handle CORS with proxy services{'\n'}
          • Suitable for real-time data updates
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 24,
  },
  controlsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  actionButton: {
    backgroundColor: '#2196F3',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  stockInputSection: {
    marginBottom: 8,
  },
  stockInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    backgroundColor: 'white',
    fontSize: 16,
    marginBottom: 8,
  },
  loadingSection: {
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 8,
    fontSize: 16,
    color: '#666',
  },
  resultsSection: {
    marginBottom: 24,
  },
  resultCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  resultType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
  },
  resultData: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#666',
    backgroundColor: '#f8f8f8',
    padding: 8,
    borderRadius: 4,
  },
  savedSection: {
    marginBottom: 24,
  },
  savedItem: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  savedKey: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  savedTimestamp: {
    fontSize: 12,
    color: '#666',
  },
  clearButton: {
    backgroundColor: '#F44336',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  clearButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  noDataText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
    padding: 20,
  },
  instructionsSection: {
    marginBottom: 32,
  },
  instructionText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
  },
});

export default ScrapingScreen;