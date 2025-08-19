import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Alert,
  Platform,
} from 'react-native';
import SupabaseService from '../services/supabaseClient';

const WebDashboardScreen = () => {
  const [data, setData] = useState({
    portfolioStocks: [],
    summaryData: null,
    setIndexData: null,
    myPortfolio: [],
    loading: true,
    refreshing: false,
    searchQuery: '',
    sortKey: 'symbol',
    sortDir: 'asc'
  });

  const [portfolioSymbols, setPortfolioSymbols] = useState(new Set());

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setData(prev => ({ ...prev, loading: true }));
      
      const [dashboardData, summaryData, setIndexData] = await Promise.all([
        SupabaseService.getDashboardData(),
        SupabaseService.getPortfolioSummary(),
        SupabaseService.getSetIndexData()
      ]);

      setData(prev => ({
        ...prev,
        portfolioStocks: dashboardData.holdings || [],
        summaryData: summaryData,
        setIndexData: setIndexData,
        loading: false,
        refreshing: false
      }));

    } catch (error) {
      console.error('Dashboard load error:', error);
      setData(prev => ({ ...prev, loading: false, refreshing: false }));
    }
  };

  const onRefresh = () => {
    setData(prev => ({ ...prev, refreshing: true }));
    loadDashboardData();
  };

  const formatNumber = (value, decimals = 2) => {
    if (value === null || value === undefined || isNaN(value)) return '';
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: decimals });
  };

  const getValueClass = (value) => {
    if (value > 0) return styles.positive;
    if (value < 0) return styles.negative;
    return styles.neutral;
  };

  const filteredAndSortedData = () => {
    let filtered = data.portfolioStocks.filter(stock =>
      !data.searchQuery || 
      stock.symbol.toLowerCase().includes(data.searchQuery.toLowerCase())
    );

    filtered.sort((a, b) => {
      const va = a[data.sortKey];
      const vb = b[data.sortKey];
      
      if (va == null && vb == null) return 0;
      if (va == null) return data.sortDir === 'asc' ? -1 : 1;
      if (vb == null) return data.sortDir === 'asc' ? 1 : -1;
      
      if (va < vb) return data.sortDir === 'asc' ? -1 : 1;
      if (va > vb) return data.sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  };

  const toggleSort = (key) => {
    setData(prev => ({
      ...prev,
      sortKey: key,
      sortDir: prev.sortKey === key && prev.sortDir === 'asc' ? 'desc' : 'asc'
    }));
  };

  const renderHeader = () => (
    <View style={styles.header}>
      <View>
        <Text style={styles.title}>Portfolio Dashboard — NVDR & Short Sales</Text>
        <Text style={styles.subtitle}>Symbol • ราคาปิด • NVDR • Short Sales</Text>
        <Text style={styles.tradeDate}>
          Trade Date: {data.summaryData?.last_updated ? 
            new Date(data.summaryData.last_updated).toLocaleDateString() : 
            'Loading...'}
        </Text>
      </View>
      <View style={styles.headerButtons}>
        <TouchableOpacity style={styles.refreshButton} onPress={onRefresh}>
          <Text style={styles.refreshButtonText}>Refresh Data</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderStatusBar = () => (
    <View style={styles.statusBar}>
      <View style={styles.statusLeft}>
        <Text style={styles.statusIcon}>📊</Text>
        <View>
          <Text style={styles.statusMessage}>
            {data.summaryData?.source || 'Database ready'}
          </Text>
          <Text style={styles.statusDetails}>
            {data.summaryData?.connected ? 'Connected to Supabase' : 'Demo mode'}
          </Text>
        </View>
      </View>
      <Text style={styles.statusTimestamp}>
        {new Date().toLocaleTimeString()}
      </Text>
    </View>
  );

  const renderSummaryCards = () => {
    if (!data.summaryData) return null;

    return (
      <View style={styles.summaryCards}>
        <View style={styles.summaryCard}>
          <Text style={styles.cardLabel}>Total Symbols</Text>
          <Text style={styles.cardValue}>{data.summaryData.total_holdings || 0}</Text>
          <Text style={styles.cardUnit}>stocks</Text>
          <View style={styles.miniChart}>
            <Text style={styles.miniChartText}>📊</Text>
          </View>
        </View>
        
        <View style={styles.summaryCard}>
          <Text style={styles.cardLabel}>Avg Price</Text>
          <Text style={styles.cardValue}>
            {formatNumber(data.summaryData.market_value ? data.summaryData.market_value / data.summaryData.total_holdings : 0)}
          </Text>
          <Text style={styles.cardUnit}>Baht</Text>
          <View style={styles.miniChart}>
            <Text style={styles.miniChartText}>💰</Text>
          </View>
        </View>
        
        <View style={styles.summaryCard}>
          <Text style={styles.cardLabel}>NVDR (Σ)</Text>
          <Text style={[styles.cardValue, getValueClass(data.summaryData.day_change)]}>
            {formatNumber(data.summaryData.day_change || 0)}M
          </Text>
          <Text style={styles.cardUnit}>Million Baht</Text>
          <View style={styles.miniChart}>
            <Text style={styles.miniChartText}>📈</Text>
          </View>
        </View>
        
        <View style={styles.summaryCard}>
          <Text style={styles.cardLabel}>Short Sales (Σ)</Text>
          <Text style={[styles.cardValue, getValueClass(data.summaryData.day_change_percent)]}>
            {formatNumber(Math.abs(data.summaryData.day_change_percent || 0))}M
          </Text>
          <Text style={styles.cardUnit}>Million Baht</Text>
          <View style={styles.miniChart}>
            <Text style={styles.miniChartText}>📉</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSetIndexSection = () => {
    if (!data.setIndexData) return null;

    return (
      <View style={styles.setIndexSection}>
        <View style={styles.setIndexHeader}>
          <Text style={styles.setIndexTitle}>SET Index</Text>
          <Text style={styles.setIndexTimestamp}>
            {data.setIndexData.last_updated ? 
              new Date(data.setIndexData.last_updated).toLocaleTimeString() : 
              'Loading...'}
          </Text>
        </View>
        
        <View style={styles.setIndexTable}>
          <View style={styles.setIndexHeaderRow}>
            <Text style={styles.setIndexHeaderCell}>Index</Text>
            <Text style={styles.setIndexHeaderCellRight}>Last</Text>
            <Text style={styles.setIndexHeaderCellRight}>Change</Text>
            <Text style={styles.setIndexHeaderCellRight}>Volume</Text>
            <Text style={styles.setIndexHeaderCellRight}>Value</Text>
          </View>
          
          {data.setIndexData.set_index?.slice(0, 5).map((index, i) => (
            <View key={i} style={styles.setIndexRow}>
              <Text style={styles.setIndexCell}>{index.index_name}</Text>
              <Text style={styles.setIndexCellRight}>{formatNumber(index.last_value)}</Text>
              <Text style={[styles.setIndexCellRight, getValueClass(index.change_value)]}>
                {index.change_text}
              </Text>
              <Text style={styles.setIndexCellRight}>{formatNumber(index.volume_thousands, 0)}</Text>
              <Text style={styles.setIndexCellRight}>{formatNumber(index.value_million_baht, 0)}</Text>
            </View>
          ))}
        </View>
      </View>
    );
  };

  const renderSearchBar = () => (
    <View style={styles.searchSection}>
      <View style={styles.searchHeader}>
        <Text style={styles.searchTitle}>All Symbols</Text>
        <Text style={styles.searchCount}>
          {filteredAndSortedData().length} / {data.portfolioStocks.length} symbols
        </Text>
      </View>
      
      <View style={styles.searchContainer}>
        <Text style={styles.searchIcon}>🔎</Text>
        <TextInput
          style={styles.searchInput}
          placeholder="Search all symbols (e.g., AOT)"
          value={data.searchQuery}
          onChangeText={(text) => setData(prev => ({ ...prev, searchQuery: text }))}
          autoCapitalize="characters"
        />
        {data.searchQuery.length > 0 && (
          <TouchableOpacity 
            style={styles.clearButton}
            onPress={() => setData(prev => ({ ...prev, searchQuery: '' }))}
          >
            <Text style={styles.clearButtonText}>✕</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  const renderTableHeader = () => (
    <View style={styles.tableHeader}>
      <TouchableOpacity 
        style={styles.headerCell}
        onPress={() => toggleSort('symbol')}
      >
        <Text style={styles.headerText}>Symbol</Text>
        <Text style={styles.sortIndicator}>
          {data.sortKey === 'symbol' ? (data.sortDir === 'asc' ? '▲' : '▼') : '↕'}
        </Text>
      </TouchableOpacity>
      
      <View style={styles.headerCell}>
        <Text style={styles.headerText}>Sector</Text>
      </View>
      
      <TouchableOpacity 
        style={styles.headerCell}
        onPress={() => toggleSort('change')}
      >
        <Text style={styles.headerTextRight}>Change</Text>
        <Text style={styles.sortIndicator}>
          {data.sortKey === 'change' ? (data.sortDir === 'asc' ? '▲' : '▼') : '↕'}
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={styles.headerCell}
        onPress={() => toggleSort('last_price')}
      >
        <Text style={styles.headerTextRight}>ราคาปิด</Text>
        <Text style={styles.sortIndicator}>
          {data.sortKey === 'last_price' ? (data.sortDir === 'asc' ? '▲' : '▼') : '↕'}
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={styles.headerCell}
        onPress={() => toggleSort('percent_change')}
      >
        <Text style={styles.headerTextRight}>% Change</Text>
        <Text style={styles.sortIndicator}>
          {data.sortKey === 'percent_change' ? (data.sortDir === 'asc' ? '▲' : '▼') : '↕'}
        </Text>
      </TouchableOpacity>
      
      <View style={styles.headerCell}>
        <Text style={styles.headerTextRight}>Volume</Text>
      </View>
      
      <View style={styles.headerCell}>
        <Text style={styles.headerTextCenter}>Portfolio</Text>
      </View>
    </View>
  );

  const renderTableRow = (stock, index) => {
    const changeValue = parseFloat(stock.change?.toString().replace(/[^-+\d.]/g, '') || 0);
    const percentChangeValue = parseFloat(stock.percent_change?.toString().replace(/[^-+\d.]/g, '') || 0);
    
    return (
      <View key={stock.symbol || index} style={styles.tableRow}>
        <View style={styles.cell}>
          <Text style={styles.symbolText}>{stock.symbol || ''}</Text>
        </View>
        
        <View style={styles.cell}>
          <Text style={styles.sectorText}>{stock.sector || ''}</Text>
        </View>
        
        <View style={styles.cell}>
          <Text style={[styles.cellTextRight, getValueClass(changeValue)]}>
            {changeValue > 0 ? '+' : ''}{formatNumber(changeValue)}
          </Text>
        </View>
        
        <View style={styles.cell}>
          <Text style={styles.cellTextRight}>{formatNumber(stock.last_price)}</Text>
        </View>
        
        <View style={styles.cell}>
          <Text style={[styles.cellTextRight, getValueClass(percentChangeValue)]}>
            {percentChangeValue > 0 ? '+' : ''}{formatNumber(percentChangeValue)}%
          </Text>
        </View>
        
        <View style={styles.cell}>
          <Text style={styles.cellTextRight}>{formatNumber(stock.volume, 0)}</Text>
        </View>
        
        <View style={styles.cell}>
          <TouchableOpacity 
            style={styles.portfolioButton}
            onPress={() => {
              const isInPortfolio = portfolioSymbols.has(stock.symbol);
              if (isInPortfolio) {
                portfolioSymbols.delete(stock.symbol);
              } else {
                portfolioSymbols.add(stock.symbol);
              }
              setPortfolioSymbols(new Set(portfolioSymbols));
            }}
          >
            <Text style={styles.portfolioButtonText}>
              {portfolioSymbols.has(stock.symbol) ? '✓' : '+'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  const renderTable = () => {
    const filteredData = filteredAndSortedData();
    
    return (
      <View style={styles.tableContainer}>
        {renderTableHeader()}
        <ScrollView style={styles.tableBody}>
          {data.loading ? (
            <View style={styles.loadingState}>
              <Text style={styles.loadingText}>Loading portfolio data...</Text>
            </View>
          ) : filteredData.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No portfolio data available</Text>
            </View>
          ) : (
            filteredData.map((stock, index) => renderTableRow(stock, index))
          )}
        </ScrollView>
      </View>
    );
  };

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={data.refreshing} onRefresh={onRefresh} />
      }
    >
      {renderHeader()}
      {renderStatusBar()}
      {renderSetIndexSection()}
      {renderSummaryCards()}
      {renderSearchBar()}
      {renderTable()}
      
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Real-time data from SET database. Last updated: {new Date().toLocaleString()}
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f1f5f9', // Tailwind bg-slate-100
  },
  
  // Header Styles
  header: {
    padding: 16,
    flexDirection: 'column',
    gap: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#334155', // Tailwind text-slate-700
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b', // Tailwind text-slate-500
    opacity: 0.7,
  },
  tradeDate: {
    fontSize: 12,
    color: '#64748b',
    opacity: 0.5,
    marginTop: 4,
  },
  headerButtons: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  refreshButton: {
    backgroundColor: 'white',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
      },
      android: { elevation: 2 },
      web: { boxShadow: '0px 1px 2px rgba(0, 0, 0, 0.1)' },
    }),
  },
  refreshButtonText: {
    fontSize: 14,
    color: '#334155',
  },

  // Status Bar Styles
  statusBar: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#dbeafe', // Tailwind bg-blue-50
    borderColor: '#93c5fd', // Tailwind border-blue-200
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusIcon: {
    fontSize: 18,
  },
  statusMessage: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1e40af', // Tailwind text-blue-800
  },
  statusDetails: {
    fontSize: 12,
    color: '#1e40af',
    opacity: 0.7,
  },
  statusTimestamp: {
    fontSize: 12,
    color: '#1e40af',
    opacity: 0.6,
  },

  // Summary Cards Styles
  summaryCards: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: 16,
    marginBottom: 16,
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    minWidth: 150,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: { elevation: 4 },
      web: { boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)' },
    }),
  },
  cardLabel: {
    fontSize: 12,
    color: '#64748b',
    opacity: 0.6,
    marginBottom: 4,
  },
  cardValue: {
    fontSize: 20,
    fontWeight: '600',
    color: '#334155',
    textAlign: 'center',
  },
  cardUnit: {
    fontSize: 12,
    color: '#64748b',
    opacity: 0.5,
    marginTop: 2,
  },
  miniChart: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 24,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  miniChartText: {
    fontSize: 12,
    opacity: 0.6,
  },

  // SET Index Styles
  setIndexSection: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: { elevation: 4 },
      web: { boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)' },
    }),
  },
  setIndexHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  setIndexTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#334155',
  },
  setIndexTimestamp: {
    fontSize: 12,
    color: '#64748b',
    opacity: 0.6,
  },
  setIndexTable: {
    padding: 8,
  },
  setIndexHeaderRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    paddingVertical: 8,
  },
  setIndexHeaderCell: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    paddingHorizontal: 8,
  },
  setIndexHeaderCellRight: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    paddingHorizontal: 8,
    textAlign: 'right',
  },
  setIndexRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    paddingVertical: 8,
  },
  setIndexCell: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    paddingHorizontal: 8,
  },
  setIndexCellRight: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    paddingHorizontal: 8,
    textAlign: 'right',
    fontVariant: ['tabular-nums'],
  },

  // Search Styles
  searchSection: {
    marginHorizontal: 16,
    marginBottom: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 16,
    borderColor: '#93c5fd',
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: { elevation: 4 },
      web: { boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)' },
    }),
  },
  searchHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  searchTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
  },
  searchCount: {
    fontSize: 12,
    color: '#64748b',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 12,
    backgroundColor: 'white',
    borderRadius: 12,
    borderColor: '#93c5fd',
    borderWidth: 1,
    paddingHorizontal: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
      },
      android: { elevation: 1 },
      web: { boxShadow: 'inset 0px 1px 2px rgba(0, 0, 0, 0.05)' },
    }),
  },
  searchIcon: {
    fontSize: 16,
    color: '#2563eb',
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
    color: '#334155',
  },
  clearButton: {
    padding: 4,
    borderRadius: 4,
  },
  clearButtonText: {
    fontSize: 16,
    color: '#64748b',
  },

  // Table Styles
  tableContainer: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderRadius: 16,
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: { elevation: 4 },
      web: { boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)' },
    }),
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    paddingVertical: 8,
  },
  headerCell: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  headerText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  headerTextRight: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    textAlign: 'right',
    flex: 1,
  },
  headerTextCenter: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    textAlign: 'center',
    flex: 1,
  },
  sortIndicator: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 4,
  },
  tableBody: {
    maxHeight: 600,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    paddingVertical: 8,
  },
  cell: {
    flex: 1,
    paddingHorizontal: 8,
    justifyContent: 'center',
  },
  symbolText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  sectorText: {
    fontSize: 14,
    color: '#6b7280',
    opacity: 0.7,
  },
  cellTextRight: {
    fontSize: 14,
    color: '#374151',
    textAlign: 'right',
    fontVariant: ['tabular-nums'],
  },
  portfolioButton: {
    backgroundColor: '#dcfce7', // Tailwind bg-green-100
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'center',
  },
  portfolioButtonText: {
    fontSize: 14,
    color: '#15803d', // Tailwind text-green-700
    fontWeight: '500',
  },

  // State Styles
  loadingState: {
    padding: 48,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#64748b',
  },
  emptyState: {
    padding: 48,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#64748b',
  },

  // Color Classes
  positive: {
    color: '#16a34a', // Tailwind text-green-600
  },
  negative: {
    color: '#dc2626', // Tailwind text-red-600
  },
  neutral: {
    color: '#374151', // Tailwind text-gray-700
  },

  // Footer
  footer: {
    marginHorizontal: 16,
    marginBottom: 32,
  },
  footerText: {
    fontSize: 11,
    color: '#64748b',
    opacity: 0.6,
    textAlign: 'center',
  },
});

export default WebDashboardScreen;