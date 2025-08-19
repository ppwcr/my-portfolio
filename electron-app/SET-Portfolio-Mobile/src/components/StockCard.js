import React from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';

const StockCard = ({ stock }) => {
  const getChangeColor = (change) => {
    if (!change) return '#666';
    const changeNum = parseFloat(change);
    if (changeNum > 0) return '#4CAF50';
    if (changeNum < 0) return '#F44336';
    return '#666';
  };

  const getChangeIcon = (change) => {
    if (!change) return '';
    const changeNum = parseFloat(change);
    if (changeNum > 0) return '▲';
    if (changeNum < 0) return '▼';
    return '●';
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.symbol}>{stock.symbol || 'N/A'}</Text>
        <Text style={styles.sector}>{stock.sector || 'Unknown'}</Text>
      </View>
      
      <View style={styles.priceSection}>
        <Text style={styles.price}>
          ฿{stock.last_price ? parseFloat(stock.last_price).toFixed(2) : '0.00'}
        </Text>
        <View style={styles.changeSection}>
          <Text style={[styles.change, { color: getChangeColor(stock.change) }]}>
            {getChangeIcon(stock.change)} {stock.change || '0.00'}
          </Text>
          <Text style={[styles.percent, { color: getChangeColor(stock.percent_change) }]}>
            ({stock.percent_change || '0.00'}%)
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 8,
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  sector: {
    fontSize: 12,
    color: '#666',
    textTransform: 'uppercase',
  },
  priceSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  price: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  changeSection: {
    alignItems: 'flex-end',
  },
  change: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  percent: {
    fontSize: 12,
  },
});

export default StockCard;