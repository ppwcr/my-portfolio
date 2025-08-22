const { autoUpdater } = require('electron-updater');
const { app, dialog, BrowserWindow } = require('electron');
const path = require('path');

class AutoUpdaterService {
  constructor() {
    this.mainWindow = null;
    this.updateAvailable = false;
    this.updateDownloaded = false;
    
    // Configure auto-updater
    autoUpdater.autoDownload = false; // Don't auto-download, ask user first
    autoUpdater.autoInstallOnAppQuit = true; // Install on app quit
    
    // Set up event listeners
    this.setupEventListeners();
  }

  setMainWindow(window) {
    this.mainWindow = window;
  }

  setupEventListeners() {
    // Check for update errors
    autoUpdater.on('error', (err) => {
      console.error('Auto-updater error:', err);
      this.showErrorDialog('Update Error', `Failed to check for updates: ${err.message}`);
    });

    // Check for updates
    autoUpdater.on('checking-for-update', () => {
      console.log('Checking for updates...');
      this.sendStatusToWindow('Checking for updates...');
    });

    // No updates available
    autoUpdater.on('update-not-available', () => {
      console.log('No updates available');
      this.sendStatusToWindow('No updates available');
      this.showInfoDialog('No Updates', 'You are running the latest version of SET Portfolio Manager.');
    });

    // Update available
    autoUpdater.on('update-available', (info) => {
      console.log('Update available:', info);
      this.updateAvailable = true;
      this.sendStatusToWindow(`Update available: ${info.version}`);
      
      // Ask user if they want to download the update
      this.showUpdateAvailableDialog(info);
    });

    // Update download progress
    autoUpdater.on('download-progress', (progressObj) => {
      const logMessage = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}% (${progressObj.transferred}/${progressObj.total})`;
      console.log(logMessage);
      this.sendStatusToWindow(`Downloading update: ${Math.round(progressObj.percent)}%`);
    });

    // Update downloaded
    autoUpdater.on('update-downloaded', (info) => {
      console.log('Update downloaded:', info);
      this.updateDownloaded = true;
      this.sendStatusToWindow('Update downloaded. Restart to install.');
      
      // Ask user to restart the app
      this.showUpdateDownloadedDialog(info);
    });
  }

  // Check for updates
  checkForUpdates() {
    console.log('Checking for updates...');
    this.sendStatusToWindow('Checking for updates...');
    
    try {
      autoUpdater.checkForUpdates();
    } catch (error) {
      console.error('Error checking for updates:', error);
      this.showErrorDialog('Update Error', `Failed to check for updates: ${error.message}`);
    }
  }

  // Download update
  downloadUpdate() {
    if (this.updateAvailable) {
      console.log('Downloading update...');
      this.sendStatusToWindow('Downloading update...');
      autoUpdater.downloadUpdate();
    }
  }

  // Install update
  installUpdate() {
    if (this.updateDownloaded) {
      console.log('Installing update...');
      autoUpdater.quitAndInstall();
    }
  }

  // Show update available dialog
  showUpdateAvailableDialog(info) {
    const options = {
      type: 'info',
      title: 'Update Available',
      message: `A new version of SET Portfolio Manager is available!`,
      detail: `Version ${info.version}\n\n${info.releaseNotes || 'Bug fixes and improvements'}\n\nWould you like to download and install this update?`,
      buttons: ['Download Update', 'Remind Me Later', 'Skip This Version'],
      defaultId: 0,
      cancelId: 1
    };

    dialog.showMessageBox(this.mainWindow, options).then((result) => {
      switch (result.response) {
        case 0: // Download Update
          this.downloadUpdate();
          break;
        case 1: // Remind Me Later
          // Schedule reminder for later
          setTimeout(() => this.checkForUpdates(), 24 * 60 * 60 * 1000); // 24 hours
          break;
        case 2: // Skip This Version
          // Mark this version as skipped
          this.skipVersion(info.version);
          break;
      }
    });
  }

  // Show update downloaded dialog
  showUpdateDownloadedDialog(info) {
    const options = {
      type: 'info',
      title: 'Update Ready',
      message: 'Update downloaded successfully!',
      detail: `Version ${info.version} has been downloaded and is ready to install.\n\nRestart the application to install the update.`,
      buttons: ['Restart Now', 'Restart Later'],
      defaultId: 0,
      cancelId: 1
    };

    dialog.showMessageBox(this.mainWindow, options).then((result) => {
      if (result.response === 0) {
        this.installUpdate();
      }
    });
  }

  // Show error dialog
  showErrorDialog(title, message) {
    dialog.showErrorBox(title, message);
  }

  // Show info dialog
  showInfoDialog(title, message) {
    dialog.showMessageBox(this.mainWindow, {
      type: 'info',
      title: title,
      message: message,
      buttons: ['OK']
    });
  }

  // Send status to renderer process
  sendStatusToWindow(message) {
    if (this.mainWindow && !this.mainWindow.isDestroyed()) {
      this.mainWindow.webContents.send('update-status', message);
    }
  }

  // Skip version (store in local storage)
  skipVersion(version) {
    // Store skipped version in app settings
    const skippedVersions = app.getPath('userData');
    console.log(`Skipped version ${version}`);
  }

  // Get current version
  getCurrentVersion() {
    return app.getVersion();
  }

  // Check if update is available
  isUpdateAvailable() {
    return this.updateAvailable;
  }

  // Check if update is downloaded
  isUpdateDownloaded() {
    return this.updateDownloaded;
  }
}

module.exports = AutoUpdaterService;
