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

const InvestorScreen = () => {
  const [investorData, setInvestorData] = useState(null);
  const [selectedMarket, setSelectedMarket] = useState('SET');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadInvestorData = async (market = 'SET') => {
    try {
      setLoading(true);
      const data = await PortfolioAPI.getInvestorData(market);
      setInvestorData(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load investor data');
      console.error('Investor data error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadInvestorData(selectedMarket);
  }, [selectedMarket]);

  const onRefresh = () => {
    setRefreshing(true);
    loadInvestorData(selectedMarket);
  };

  const formatVolume = (volume) => {
    if (!volume) return '0';
    const num = Number(volume);
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(1)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatValue = (value) => {
    if (!value) return '0';
    const num = Number(value);
    return `฿${num.toLocaleString()}`;
  };

  const getInvestorColor = (type) => {
    const colors = {
      'Local Institutions': '#2196F3',
      'Foreign Investors': '#4CAF50',
      'Local Individuals': '#FF9800',
      'Proprietary Trading': '#9C27B0',
    };
    return colors[type] || '#666';
  };

  if (loading && !investorData) {
    return (
      <View style={styles.centered}>
        <Text style={styles.loadingText}>Loading investor data...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <Text style={styles.title}>Investor Trading Data</Text>
      
      {/* Market Selector */}
      <View style={styles.marketSelector}>
        <TouchableOpacity
          style={[
            styles.marketButton,
            selectedMarket === 'SET' && styles.marketButtonActive
          ]}
          onPress={() => setSelectedMarket('SET')}
        >
          <Text style={[
            styles.marketButtonText,
            selectedMarket === 'SET' && styles.marketButtonTextActive
          ]}>
            SET
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.marketButton,
            selectedMarket === 'MAI' && styles.marketButtonActive
          ]}
          onPress={() => setSelectedMarket('MAI')}
        >
          <Text style={[
            styles.marketButtonText,
            selectedMarket === 'MAI' && styles.marketButtonTextActive
          ]}>
            MAI
          </Text>
        </TouchableOpacity>
      </View>

      {investorData && (
        <>
          <Text style={styles.subtitle}>
            Market: {selectedMarket} • Last Updated: {new Date().toLocaleDateString()}
          </Text>

          {/* Buy/Sell Summary */}
          {investorData.summary && (
            <View style={styles.summarySection}>
              <Text style={styles.sectionTitle}>Trading Summary</Text>
              <View style={styles.summaryCard}>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Total Buy Volume</Text>
                  <Text style={styles.summaryValue}>
                    {formatVolume(investorData.summary.total_buy_volume)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Total Sell Volume</Text>
                  <Text style={styles.summaryValue}>
                    {formatVolume(investorData.summary.total_sell_volume)}
                  </Text>
                </View>
                <View style={styles.summaryRow}>
                  <Text style={styles.summaryLabel}>Net Volume</Text>
                  <Text style={[
                    styles.summaryValue,
                    {
                      color: (investorData.summary.net_volume || 0) >= 0 ? '#4CAF50' : '#F44336'
                    }
                  ]}>
                    {(investorData.summary.net_volume || 0) >= 0 ? '+' : ''}
                    {formatVolume(investorData.summary.net_volume)}
                  </Text>
                </View>
              </View>
            </View>
          )}

          {/* Investor Types */}
          {investorData.investors && (
            <View style={styles.investorsSection}>
              <Text style={styles.sectionTitle}>By Investor Type</Text>
              {investorData.investors.map((investor, index) => (
                <View key={index} style={styles.investorCard}>
                  <View style={styles.investorHeader}>
                    <View style={[
                      styles.investorDot,
                      { backgroundColor: getInvestorColor(investor.type) }
                    ]} />
                    <Text style={styles.investorType}>{investor.type}</Text>
                  </View>
                  
                  <View style={styles.investorData}>
                    <View style={styles.investorRow}>
                      <Text style={styles.investorLabel}>Buy Volume</Text>
                      <Text style={styles.investorValue}>
                        {formatVolume(investor.buy_volume)}
                      </Text>
                    </View>
                    <View style={styles.investorRow}>
                      <Text style={styles.investorLabel}>Sell Volume</Text>
                      <Text style={styles.investorValue}>
                        {formatVolume(investor.sell_volume)}
                      </Text>
                    </View>
                    <View style={styles.investorRow}>
                      <Text style={styles.investorLabel}>Net Volume</Text>
                      <Text style={[
                        styles.investorValue,
                        {
                          color: (investor.net_volume || 0) >= 0 ? '#4CAF50' : '#F44336'
                        }
                      ]}>
                        {(investor.net_volume || 0) >= 0 ? '+' : ''}
                        {formatVolume(investor.net_volume)}
                      </Text>
                    </View>
                  </View>
                </View>
              ))}
            </View>
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
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 18,
    color: '#666',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 24,
  },
  marketSelector: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  marketButton: {
    flex: 1,
    padding: 12,
    backgroundColor: 'white',
    marginRight: 8,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  marketButtonActive: {
    backgroundColor: '#2196F3',
    borderColor: '#2196F3',
  },
  marketButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#666',
  },
  marketButtonTextActive: {
    color: 'white',
  },
  summarySection: {
    marginBottom: 24,
  },
  investorsSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  summaryCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  investorCard: {
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  investorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  investorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  investorType: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  investorData: {
    paddingLeft: 20,
  },
  investorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  investorLabel: {
    fontSize: 14,
    color: '#666',
  },
  investorValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
});

export default InvestorScreen;