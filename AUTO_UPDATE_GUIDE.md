# Auto-Update Guide - SET Portfolio Manager

This guide explains how the auto-update system works and how to use it.

## 🔄 **How Auto-Update Works**

### **Current Implementation:**

1. **Automatic Check** - App checks for updates 10 seconds after startup
2. **Manual Check** - Users can check via "Updates" menu
3. **User Choice** - Users decide whether to download/install updates
4. **GitHub Integration** - Updates are published to GitHub releases

### **Update Flow:**

```
App Starts → Check for Updates → Update Available? → Ask User → Download → Install
     ↓              ↓                    ↓              ↓         ↓         ↓
  10 seconds    GitHub API          Show Dialog    User Choice  Progress   Restart
```

## 🛠️ **Setup Requirements**

### **1. GitHub Token (Required)**

Create a GitHub personal access token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` permissions
3. Set environment variable:
   ```bash
   export GH_TOKEN=your_github_token_here
   ```

### **2. Code Signing (Recommended)**

For Windows, code signing is recommended:

1. **Purchase a code signing certificate**
2. **Configure in package.json:**
   ```json
   {
     "build": {
       "win": {
         "certificateFile": "path/to/certificate.p12",
         "certificatePassword": "password"
       }
     }
   }
   ```

## 📦 **Publishing Updates**

### **Method 1: Using Publish Script**

```bash
cd electron-app
npm run publish
```

### **Method 2: Direct Build and Publish**

```bash
cd electron-app
npm run publish-win
```

### **Method 3: Manual GitHub Release**

1. **Build the application:**
   ```bash
   npm run build-win
   ```

2. **Create GitHub release:**
   - Go to GitHub repository
   - Click "Releases" → "Create a new release"
   - Tag version (e.g., `v1.0.1`)
   - Upload the .exe files
   - Add release notes

## 🔧 **Configuration Options**

### **Auto-Update Settings**

Edit `auto-updater.js` to customize behavior:

```javascript
// Check frequency (default: 10 seconds after startup)
setTimeout(() => {
  autoUpdater.checkForUpdates();
}, 10000);

// Auto-download (default: false - asks user first)
autoUpdater.autoDownload = false;

// Auto-install on quit (default: true)
autoUpdater.autoInstallOnAppQuit = true;
```

### **Update Channels**

Support multiple update channels:

```javascript
// Stable channel
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'ppwcr',
  repo: 'my-portfolio',
  private: false
});

// Beta channel
autoUpdater.setFeedURL({
  provider: 'github',
  owner: 'ppwcr',
  repo: 'my-portfolio',
  private: false,
  channel: 'beta'
});
```

## 📋 **User Experience**

### **Update Notifications:**

1. **Update Available Dialog:**
   ```
   ┌─────────────────────────────────────┐
   │ Update Available                    │
   │                                     │
   │ A new version is available!         │
   │ Version 1.0.1                      │
   │                                     │
   │ [Download Update] [Remind Later]    │
   └─────────────────────────────────────┘
   ```

2. **Download Progress:**
   ```
   ┌─────────────────────────────────────┐
   │ Downloading Update                  │
   │                                     │
   │ ████████████████████░░░░ 80%        │
   │                                     │
   └─────────────────────────────────────┘
   ```

3. **Install Ready:**
   ```
   ┌─────────────────────────────────────┐
   │ Update Ready                        │
   │                                     │
   │ Update downloaded successfully!     │
   │                                     │
   │ [Restart Now] [Restart Later]       │
   └─────────────────────────────────────┘
   ```

## 🎯 **Menu Integration**

The app includes an "Updates" menu:

- **Check for Updates** - Manual update check
- **Download Update** - Download available update
- **Install Update** - Install downloaded update

## 🔒 **Security Features**

### **1. Update Verification**

- **SHA256 checksums** for downloaded files
- **Code signing verification** (if configured)
- **HTTPS-only downloads** from GitHub

### **2. User Control**

- **No forced updates** - User always has choice
- **Skip version option** - Can skip specific versions
- **Remind later** - Schedule future checks

### **3. Error Handling**

- **Network errors** - Graceful fallback
- **Download failures** - Retry mechanism
- **Installation errors** - Rollback capability

## 🐛 **Troubleshooting**

### **Common Issues:**

1. **"Update check failed"**
   - Check internet connection
   - Verify GitHub token permissions
   - Check firewall settings

2. **"Download failed"**
   - Check disk space
   - Verify network stability
   - Check antivirus software

3. **"Installation failed"**
   - Run as administrator
   - Close other applications
   - Check Windows permissions

### **Debug Mode:**

Enable debug logging:

```javascript
// In auto-updater.js
autoUpdater.logger = require('electron-log');
autoUpdater.logger.transports.file.level = 'debug';
```

## 📊 **Update Statistics**

Track update adoption:

```javascript
// In auto-updater.js
autoUpdater.on('update-downloaded', (info) => {
  // Send analytics
  analytics.track('update_downloaded', {
    version: info.version,
    platform: process.platform
  });
});
```

## 🔄 **Version Management**

### **Semantic Versioning:**

- **Major.Minor.Patch** (e.g., 1.0.1)
- **Breaking changes** = Major version bump
- **New features** = Minor version bump
- **Bug fixes** = Patch version bump

### **Update Strategy:**

1. **Patch updates** - Auto-download recommended
2. **Minor updates** - Ask user first
3. **Major updates** - Always ask user

## 🚀 **Best Practices**

### **1. Release Management**

- **Test thoroughly** before publishing
- **Write clear release notes**
- **Use semantic versioning**
- **Maintain changelog**

### **2. User Communication**

- **Clear update descriptions**
- **Highlight important changes**
- **Provide rollback instructions**
- **Support multiple channels**

### **3. Monitoring**

- **Track update adoption rates**
- **Monitor error rates**
- **Collect user feedback**
- **Analyze update patterns**

## 📞 **Support**

### **For Users:**

- Check "Updates" menu in the application
- Review release notes on GitHub
- Contact support for issues

### **For Developers:**

- Monitor GitHub releases
- Check auto-updater logs
- Test update process regularly
- Maintain update infrastructure

The auto-update system provides a seamless way to keep users on the latest version while maintaining user control and security! 🚀
