# SET Portfolio Manager - Mobile App

React Native mobile application for managing Stock Exchange of Thailand (SET) portfolio data.

## Features

📱 **Native Mobile Experience**
- iOS and Android support via React Native
- Tab-based navigation
- Pull-to-refresh functionality
- Responsive design for phones and tablets

📊 **Portfolio Dashboard**
- Real-time portfolio summary
- Stock holdings overview
- Market value tracking
- Day change indicators

🏭 **Sector Analysis**
- 8 SET sectors with constituent stocks
- Interactive sector selection
- Stock performance by sector
- Real-time sector data

👥 **Investor Data**
- SET and MAI market data
- Investor type breakdowns
- Buy/sell volume analysis
- Net trading volumes

⚙️ **Settings & Export**
- NVDR and Short Sales data export
- App settings and preferences
- API status monitoring
- About and support information

## Tech Stack

- **Frontend**: React Native with Expo
- **Navigation**: React Navigation 6
- **Backend**: FastAPI (your existing server)
- **API**: RESTful API integration
- **State**: React Hooks
- **Platform**: iOS, Android, Web

## Development Setup

### Prerequisites

- Node.js 16+ 
- npm or yarn
- iOS: Xcode (for iOS simulator)
- Android: Android Studio (for Android emulator)
- Your SET Portfolio FastAPI server running

### Installation

```bash
# Clone and navigate to mobile app
cd SET-Portfolio-Mobile

# Install dependencies
npm install

# Install additional web dependencies (if needed)
npx expo install react-dom react-native-web @expo/metro-runtime
```

### Configuration

Update the API endpoint in `config.js`:

```javascript
export const API_CONFIG = {
  // Change this to your FastAPI server URL
  PRODUCTION_URL: 'https://your-api-domain.com',
  // or for local development:
  LOCAL_URL: 'http://localhost:8000',
};
```

### Running the App

```bash
# Web (for testing)
npm run web

# iOS (requires Xcode)
npm run ios

# Android (requires Android Studio)
npm run android

# Development server
npx expo start
```

## API Integration

The mobile app connects to your existing FastAPI backend using these endpoints:

- `GET /api/portfolio/dashboard` - Portfolio overview
- `GET /api/portfolio/summary` - Portfolio summary stats
- `GET /api/sector/constituents.csv?slug={sector}` - Sector data
- `GET /api/investor/chart.json?market={SET|MAI}` - Investor data
- `GET /api/nvdr/export.xlsx` - NVDR Excel export
- `GET /api/short-sales/export.xlsx` - Short sales export
- `POST /api/save-to-database` - Save data to Supabase

## Deployment Options

### Option 1: Expo Application Services (EAS)

```bash
# Install EAS CLI
npm install -g @expo/cli

# Build for iOS
npx expo build:ios

# Build for Android
npx expo build:android
```

### Option 2: React Native CLI

```bash
# Generate native code
npx expo eject

# Build iOS (requires Mac + Xcode)
cd ios && xcodebuild

# Build Android
cd android && ./gradlew assembleRelease
```

### Option 3: App Store & Google Play

1. Build production apps using EAS or React Native CLI
2. Follow Apple App Store and Google Play Store guidelines
3. Submit for review and publication

## Backend Requirements

Your FastAPI server must be accessible from mobile devices:

### For Development
- Run FastAPI server on `0.0.0.0:8000` (not just localhost)
- Ensure mobile device is on same network
- Update `LOCAL_URL` in config.js to your computer's IP

### For Production
- Deploy FastAPI server to cloud (Heroku, Vercel, AWS, etc.)
- Update `PRODUCTION_URL` in config.js
- Ensure CORS is configured for mobile domain

## Features by Screen

### 📊 Dashboard
- Portfolio summary cards
- Top stock holdings
- Save to database functionality
- Real-time market status

### 🏭 Sectors
- 8 SET sector categories
- Tap to view sector constituents
- Stock performance within sectors
- Visual sector icons

### 👥 Investor Data
- SET/MAI market toggle
- Investor type breakdown
- Buy/sell volume analysis
- Net trading calculations

### ⚙️ Settings
- App preferences
- Data export functions
- About and version info
- API connection status

## Customization

### Styling
- Colors defined in `config.js`
- Consistent design system
- iOS/Android platform adaptations

### API Endpoints
- Configurable base URL
- Timeout and retry settings
- Error handling

### Features
- Feature flags in config
- Push notifications ready
- Offline mode support (future)

## Troubleshooting

### Common Issues

**API Connection Failed**
- Check FastAPI server is running
- Verify API_CONFIG.BASE_URL is correct
- Ensure mobile device can reach server

**Build Errors**
- Run `npx expo doctor` to diagnose
- Clear metro cache: `npx expo start -c`
- Reinstall dependencies: `rm -rf node_modules && npm install`

**iOS Simulator Issues**
- Install Xcode from App Store
- Run `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`
- Accept Xcode license agreements

## Future Enhancements

- 🔔 Push notifications for price alerts
- 📱 Offline mode with local storage
- 🔐 Biometric authentication
- 📈 Advanced charting
- 🎨 Dark mode theme
- 🌐 Multi-language support

## Support

The mobile app works with your existing SET Portfolio FastAPI backend. All portfolio data, scraping, and Supabase integration continues to work through the API.

For mobile-specific issues, check the React Native and Expo documentation.