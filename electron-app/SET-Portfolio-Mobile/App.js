import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';

// Import screens
import WebDashboardScreen from './src/screens/WebDashboardScreen';
import SectorsScreen from './src/screens/SectorsScreen';
import InvestorScreen from './src/screens/InvestorScreen';
import ScrapingScreen from './src/screens/ScrapingScreen';
import SettingsScreen from './src/screens/SettingsScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Tab.Navigator
        screenOptions={{
          tabBarActiveTintColor: '#2196F3',
          tabBarInactiveTintColor: 'gray',
          tabBarStyle: {
            backgroundColor: '#fff',
            borderTopWidth: 1,
            borderTopColor: '#e0e0e0',
          },
          headerStyle: {
            backgroundColor: '#2196F3',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Tab.Screen 
          name="Dashboard" 
          component={WebDashboardScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>📊</Text>
            ),
            title: 'SET Portfolio'
          }}
        />
        <Tab.Screen 
          name="Sectors" 
          component={SectorsScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>🏭</Text>
            ),
            title: 'Sectors'
          }}
        />
        <Tab.Screen 
          name="Investor" 
          component={InvestorScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>👥</Text>
            ),
            title: 'Investor Data'
          }}
        />
        <Tab.Screen 
          name="Scraping" 
          component={ScrapingScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>🕷️</Text>
            ),
            title: 'Mobile Scraping'
          }}
        />
        <Tab.Screen 
          name="Settings" 
          component={SettingsScreen}
          options={{
            tabBarIcon: ({ color, size }) => (
              <Text style={{ color, fontSize: size }}>⚙️</Text>
            ),
            title: 'Settings'
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}