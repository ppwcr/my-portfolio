import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Linking,
  Switch,
  ScrollView,
  TextInput,
} from 'react-native';
import PortfolioAPI from '../services/api';
import SupabaseService from '../services/supabaseClient';

const SettingsScreen = () => {
  const [notifications, setNotifications] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    testSupabaseConnection();
  }, []);

  const testSupabaseConnection = async () => {
    setTesting(true);
    try {
      const status = await SupabaseService.testConnection();
      setConnectionStatus(status);
    } catch (error) {
      setConnectionStatus({
        connected: false,
        message: `Test failed: ${error.message}`,
        demo: false
      });
    } finally {
      setTesting(false);
    }
  };

  const handleExportNVDR = async () => {
    try {
      Alert.alert(
        'Export NVDR Data',
        'This will download the latest NVDR Excel file. Continue?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Download',
            onPress: async () => {
              try {
                await PortfolioAPI.downloadNVDRExcel();
                Alert.alert('Success', 'NVDR data exported successfully!');
              } catch (error) {
                Alert.alert('Error', 'Failed to export NVDR data.');
              }
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to export NVDR data.');
    }
  };

  const handleExportShortSales = async () => {
    try {
      Alert.alert(
        'Export Short Sales Data',
        'This will download the latest Short Sales Excel file. Continue?',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Download',
            onPress: async () => {
              try {
                await PortfolioAPI.downloadShortSalesExcel();
                Alert.alert('Success', 'Short Sales data exported successfully!');
              } catch (error) {
                Alert.alert('Error', 'Failed to export Short Sales data.');
              }
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert('Error', 'Failed to export Short Sales data.');
    }
  };

  const handleAbout = () => {
    Alert.alert(
      'About SET Portfolio Manager',
      'Version 1.0.0\n\nA mobile app for managing and tracking Stock Exchange of Thailand (SET) portfolio data.\n\nDeveloped with React Native and powered by FastAPI backend.',
      [{ text: 'OK' }]
    );
  };

  const handleSupport = () => {
    Alert.alert(
      'Support',
      'Need help with the app?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Contact Support',
          onPress: () => {
            // You can replace this with your actual support email
            Linking.openURL('mailto:support@setportfolio.com?subject=SET Portfolio Mobile Support');
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Settings</Text>

      {/* App Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>App Settings</Text>
        
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>Push Notifications</Text>
          <Switch
            value={notifications}
            onValueChange={setNotifications}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={notifications ? '#2196F3' : '#f4f3f4'}
          />
        </View>

        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>Auto Refresh Data</Text>
          <Switch
            value={autoRefresh}
            onValueChange={setAutoRefresh}
            trackColor={{ false: '#767577', true: '#81b0ff' }}
            thumbColor={autoRefresh ? '#2196F3' : '#f4f3f4'}
          />
        </View>
      </View>

      {/* Data Export */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Export</Text>
        
        <TouchableOpacity style={styles.actionButton} onPress={handleExportNVDR}>
          <Text style={styles.actionButtonText}>📊 Export NVDR Data</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.actionButton} onPress={handleExportShortSales}>
          <Text style={styles.actionButtonText}>📈 Export Short Sales Data</Text>
        </TouchableOpacity>
      </View>

      {/* App Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>App Info</Text>
        
        <TouchableOpacity style={styles.infoButton} onPress={handleAbout}>
          <Text style={styles.infoButtonText}>About</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.infoButton} onPress={handleSupport}>
          <Text style={styles.infoButtonText}>Support</Text>
        </TouchableOpacity>
      </View>

      {/* Database Status */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Database Connection</Text>
        <View style={styles.statusCard}>
          {connectionStatus ? (
            <>
              <Text style={styles.statusText}>
                {connectionStatus.connected ? '🟢' : connectionStatus.demo ? '🟡' : '🔴'} 
                {connectionStatus.connected ? ' Connected to Supabase' : 
                 connectionStatus.demo ? ' Demo Mode (Configure Supabase)' : 
                 ' Connection Failed'}
              </Text>
              <Text style={styles.statusSubtext}>{connectionStatus.message}</Text>
              {connectionStatus.data_available && (
                <Text style={styles.statusSubtext}>📊 Portfolio data available</Text>
              )}
            </>
          ) : (
            <Text style={styles.statusText}>
              {testing ? '⏳ Testing connection...' : '❓ Unknown status'}
            </Text>
          )}
        </View>
        
        <TouchableOpacity 
          style={styles.actionButton} 
          onPress={testSupabaseConnection}
          disabled={testing}
        >
          <Text style={styles.actionButtonText}>
            {testing ? '⏳ Testing...' : '🔄 Test Connection'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Version Info */}
      <View style={styles.versionSection}>
        <Text style={styles.versionText}>SET Portfolio Manager v1.0.0</Text>
        <Text style={styles.versionSubtext}>React Native • Expo • Supabase</Text>
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
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'white',
    padding: 16,
    marginBottom: 8,
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
  settingLabel: {
    fontSize: 16,
    color: '#333',
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
  infoButton: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
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
  infoButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusCard: {
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
  statusText: {
    fontSize: 16,
    color: '#333',
    marginBottom: 4,
  },
  statusSubtext: {
    fontSize: 14,
    color: '#666',
  },
  versionSection: {
    alignItems: 'center',
    marginTop: 'auto',
    paddingTop: 24,
  },
  versionText: {
    fontSize: 14,
    color: '#666',
    fontWeight: 'bold',
  },
  versionSubtext: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
});

export default SettingsScreen;