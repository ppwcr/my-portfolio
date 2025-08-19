const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Version info
  getVersion: () => process.versions.electron,
  
  // Platform info
  platform: process.platform,
  
  // App info
  appName: 'SET Portfolio Manager',
  appVersion: '1.0.0',
  
  // Security: Only expose what's needed
  // No direct access to Node.js APIs from renderer
});