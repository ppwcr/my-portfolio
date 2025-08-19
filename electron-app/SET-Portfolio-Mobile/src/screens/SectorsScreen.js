import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import PortfolioAPI from '../services/api';

const SectorsScreen = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSector, setSelectedSector] = useState(null);
  const [sectorData, setSectorData] = useState(null);

  const sectors = [
    { name: 'Agriculture & Food Industry', slug: 'agro', icon: '🌾' },
    { name: 'Consumer Products', slug: 'consump', icon: '🛒' },
    { name: 'Financials', slug: 'fincial', icon: '🏦' },
    { name: 'Industrial', slug: 'indus', icon: '🏭' },
    { name: 'Property & Construction', slug: 'propcon', icon: '🏗️' },
    { name: 'Resources', slug: 'resourc', icon: '⛏️' },
    { name: 'Services', slug: 'service', icon: '🔧' },
    { name: 'Technology', slug: 'tech', icon: '💻' },
  ];

  const loadSectorData = async (sectorSlug) => {
    try {
      const csvData = await PortfolioAPI.getSectorConstituents(sectorSlug);
      
      // Parse CSV data (simple parsing)
      const lines = csvData.split('\n');
      const headers = lines[0]?.split(',') || [];
      const stocks = lines.slice(1)
        .filter(line => line.trim())
        .map(line => {
          const values = line.split(',');
          const stock = {};
          headers.forEach((header, index) => {
            stock[header.trim()] = values[index]?.trim() || '';
          });
          return stock;
        });

      setSectorData({ sector: sectorSlug, stocks });
    } catch (error) {
      Alert.alert('Error', 'Failed to load sector data');
      console.error('Sector data error:', error);
    }
  };

  const handleSectorPress = (sector) => {
    setSelectedSector(sector);
    loadSectorData(sector.slug);
  };

  const onRefresh = () => {
    setRefreshing(true);
    if (selectedSector) {
      loadSectorData(selectedSector.slug);
    }
    setRefreshing(false);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {!selectedSector ? (
        <>
          <Text style={styles.title}>SET Sectors</Text>
          <Text style={styles.subtitle}>
            Select a sector to view constituent stocks
          </Text>
          
          <View style={styles.sectorsGrid}>
            {sectors.map((sector) => (
              <TouchableOpacity
                key={sector.slug}
                style={styles.sectorCard}
                onPress={() => handleSectorPress(sector)}
              >
                <Text style={styles.sectorIcon}>{sector.icon}</Text>
                <Text style={styles.sectorName}>{sector.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </>
      ) : (
        <>
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => {
                setSelectedSector(null);
                setSectorData(null);
              }}
            >
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            <Text style={styles.sectorTitle}>
              {selectedSector.icon} {selectedSector.name}
            </Text>
          </View>

          {sectorData && (
            <>
              <Text style={styles.stockCount}>
                {sectorData.stocks.length} constituent stocks
              </Text>
              
              {sectorData.stocks.map((stock, index) => (
                <View key={index} style={styles.stockItem}>
                  <Text style={styles.stockSymbol}>
                    {stock.symbol || stock.Symbol || 'N/A'}
                  </Text>
                  <Text style={styles.stockPrice}>
                    ฿{stock.last_price || stock.price || '0.00'}
                  </Text>
                  <Text style={[
                    styles.stockChange,
                    {
                      color: (stock.change || 0) >= 0 ? '#4CAF50' : '#F44336'
                    }
                  ]}>
                    {(stock.change || 0) >= 0 ? '+' : ''}{stock.change || '0.00'}
                  </Text>
                </View>
              ))}
            </>
          )}
        </>
      )}
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
  sectorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  sectorCard: {
    width: '48%',
    backgroundColor: 'white',
    padding: 20,
    marginBottom: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectorIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  sectorName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  header: {
    marginBottom: 16,
  },
  backButton: {
    marginBottom: 8,
  },
  backButtonText: {
    fontSize: 16,
    color: '#2196F3',
    fontWeight: 'bold',
  },
  sectorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  stockCount: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  stockItem: {
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 8,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  stockSymbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  stockPrice: {
    fontSize: 14,
    color: '#333',
    marginRight: 16,
  },
  stockChange: {
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default SectorsScreen;