import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
  TouchableOpacity,
  Platform,
} from 'react-native';
import PortfolioAPI from '../services/api';
import StockCard from '../components/StockCard';
import SummaryCard from '../components/SummaryCard';

const DashboardScreen = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboard, summary] = await Promise.all([
        PortfolioAPI.getDashboardData(),
        PortfolioAPI.getPortfolioSummary(),
      ]);
      
      setDashboardData(dashboard);
      setSummaryData(summary);
    } catch (error) {
      Alert.alert(
        'Error',
        'Failed to load dashboard data. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
      console.error('Dashboard fetch error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const handleSaveToDatabase = async () => {
    try {
      Alert.alert(
        'Save to Database',
        'This will save all current data to Supabase. Continue?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Save',
            onPress: async () => {
              try {
                await PortfolioAPI.saveToDatabase();
                Alert.alert('Success', 'Data saved to database successfully!');
              } catch (error) {
                Alert.alert('Error', 'Failed to save data to database.');
              }
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to save to database.');
    }
  };

  if (loading && !dashboardData) {
    return (
      <View style={styles.centered}>
        <Text style={styles.loadingText}>Loading portfolio data...</Text>
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
      {/* Summary Section */}
      {summaryData && (
        <View style={styles.summarySection}>
          <Text style={styles.sectionTitle}>Portfolio Summary</Text>
          <SummaryCard data={summaryData} />
        </View>
      )}

      {/* Stock Holdings */}
      {dashboardData && dashboardData.stocks && (
        <View style={styles.stocksSection}>
          <Text style={styles.sectionTitle}>
            Stock Holdings ({dashboardData.stocks.length})
          </Text>
          {dashboardData.stocks.slice(0, 10).map((stock, index) => (
            <StockCard key={stock.symbol || index} stock={stock} />
          ))}
          {dashboardData.stocks.length > 10 && (
            <Text style={styles.moreText}>
              + {dashboardData.stocks.length - 10} more stocks
            </Text>
          )}
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.actionsSection}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleSaveToDatabase}
        >
          <Text style={styles.actionButtonText}>💾 Save to Database</Text>
        </TouchableOpacity>
      </View>

      {/* Market Status */}
      <View style={styles.statusSection}>
        <Text style={styles.sectionTitle}>Market Status</Text>
        <View style={styles.statusCard}>
          <Text style={styles.statusText}>🟢 SET Index: Active</Text>
          <Text style={styles.statusText}>📊 Data Updated: {new Date().toLocaleTimeString()}</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
  summarySection: {
    margin: 16,
  },
  stocksSection: {
    margin: 16,
  },
  actionsSection: {
    margin: 16,
  },
  statusSection: {
    margin: 16,
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  moreText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
    padding: 12,
  },
  actionButton: {
    backgroundColor: '#2196F3',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusCard: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: {
          width: 0,
          height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 3.84,
      },
      android: {
        elevation: 5,
      },
      web: {
        boxShadow: '0px 2px 3.84px rgba(0, 0, 0, 0.1)',
      },
    }),
  },
  statusText: {
    fontSize: 16,
    marginBottom: 8,
    color: '#333',
  },
});

export default DashboardScreen;