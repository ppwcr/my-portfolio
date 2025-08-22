const { app } = require('electron');
const AutoUpdaterService = require('./auto-updater');

// Mock Electron app for testing
const mockApp = {
  getVersion: () => '1.0.0',
  getPath: (name) => {
    if (name === 'userData') return './test-user-data';
    return './test-path';
  }
};

// Mock dialog for testing
const mockDialog = {
  showMessageBox: (window, options) => {
    console.log('📋 Dialog would show:', options);
    return Promise.resolve({ response: 0 }); // Simulate user clicking first button
  },
  showErrorBox: (title, message) => {
    console.log('❌ Error dialog:', title, message);
  }
};

// Mock autoUpdater for testing
const mockAutoUpdater = {
  autoDownload: false,
  autoInstallOnAppQuit: true,
  on: (event, callback) => {
    console.log(`📡 Registered listener for: ${event}`);
    // Simulate events for testing
    if (event === 'checking-for-update') {
      setTimeout(() => callback(), 100);
    }
    if (event === 'update-not-available') {
      setTimeout(() => callback(), 200);
    }
    if (event === 'update-available') {
      setTimeout(() => callback({ version: '1.0.1', releaseNotes: 'Test update' }), 300);
    }
  },
  checkForUpdates: () => {
    console.log('🔍 Checking for updates...');
  },
  downloadUpdate: () => {
    console.log('⬇️ Downloading update...');
  },
  quitAndInstall: () => {
    console.log('🔄 Quitting and installing...');
  }
};

// Test the auto-updater service
function testAutoUpdater() {
  console.log('🧪 Testing Auto-Updater Service...\n');
  
  // Create auto-updater instance
  const autoUpdater = new AutoUpdaterService();
  
  console.log('✅ Auto-updater service created');
  console.log(`📱 Current version: ${autoUpdater.getCurrentVersion()}`);
  
  // Test update check
  console.log('\n🔍 Testing update check...');
  autoUpdater.checkForUpdates();
  
  // Test status methods
  console.log('\n📊 Status check:');
  console.log(`   Update available: ${autoUpdater.isUpdateAvailable()}`);
  console.log(`   Update downloaded: ${autoUpdater.isUpdateDownloaded()}`);
  
  console.log('\n✅ Auto-updater test completed!');
}

// Run the test
if (require.main === module) {
  testAutoUpdater();
}

module.exports = { testAutoUpdater };
