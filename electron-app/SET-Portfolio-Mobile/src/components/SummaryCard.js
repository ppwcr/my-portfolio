import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';

const SummaryCard = ({ data }) => {
  const formatNumber = (num) => {
    if (!num) return '0';
    return Number(num).toLocaleString('en-US');
  };

  const formatPercent = (num) => {
    if (!num) return '0.00%';
    return `${Number(num).toFixed(2)}%`;
  };

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Portfolio Overview</Text>
      
      <View style={styles.row}>
        <View style={styles.item}>
          <Text style={styles.label}>Total Holdings</Text>
          <Text style={styles.value}>{formatNumber(data.total_holdings || data.total_stocks)}</Text>
        </View>
        <View style={styles.item}>
          <Text style={styles.label}>Market Value</Text>
          <Text style={styles.value}>฿{formatNumber(data.market_value || data.total_value)}</Text>
        </View>
      </View>

      <View style={styles.row}>
        <View style={styles.item}>
          <Text style={styles.label}>Day Change</Text>
          <Text style={[
            styles.value,
            { color: (data.day_change || 0) >= 0 ? '#4CAF50' : '#F44336' }
          ]}>
            {(data.day_change || 0) >= 0 ? '+' : ''}{formatNumber(data.day_change || 0)}
          </Text>
        </View>
        <View style={styles.item}>
          <Text style={styles.label}>Day Change %</Text>
          <Text style={[
            styles.value,
            { color: (data.day_change_percent || 0) >= 0 ? '#4CAF50' : '#F44336' }
          ]}>
            {(data.day_change_percent || 0) >= 0 ? '+' : ''}{formatPercent(data.day_change_percent || 0)}
          </Text>
        </View>
      </View>

      <View style={styles.divider} />

      <View style={styles.row}>
        <View style={styles.item}>
          <Text style={styles.label}>Last Updated</Text>
          <Text style={styles.smallValue}>
            {data.last_updated ? new Date(data.last_updated).toLocaleString() : 'N/A'}
          </Text>
        </View>
        <View style={styles.item}>
          <Text style={styles.label}>Data Source</Text>
          <Text style={styles.smallValue}>SET (Stock Exchange of Thailand)</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: {
          width: 0,
          height: 4,
        },
        shadowOpacity: 0.15,
        shadowRadius: 6,
      },
      android: {
        elevation: 8,
      },
      web: {
        boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.15)',
      },
    }),
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
    textAlign: 'center',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  item: {
    flex: 1,
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  value: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
  },
  smallValue: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: '#e0e0e0',
    marginVertical: 8,
  },
});

export default SummaryCard;