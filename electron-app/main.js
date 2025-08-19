const { app, BrowserWindow, dialog, Menu, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

let mainWindow;
let pythonProcess;
const isDev = process.argv.includes('--dev');
const SERVER_PORT = 8001;
const SERVER_URL = `http://localhost:${SERVER_PORT}`;

// Python backend management
function findPythonExecutable() {
  const possiblePaths = [
    '/Library/Frameworks/Python.framework/Versions/3.10/bin/python3',
    '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3',
    '/Library/Frameworks/Python.framework/Versions/3.12/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
    '/opt/homebrew/bin/python3',
    '/usr/local/bin/python',
    '/usr/bin/python',
    'python3',
    'python'
  ];
  
  const { execSync } = require('child_process');
  
  for (const pythonPath of possiblePaths) {
    try {
      execSync(`${pythonPath} --version`, { stdio: 'ignore' });
      console.log(`Found Python at: ${pythonPath}`);
      return pythonPath;
    } catch (error) {
      // Continue to next path
    }
  }
  
  throw new Error('No Python installation found');
}

function showPythonInstallDialog() {
  const result = dialog.showMessageBoxSync(mainWindow, {
    type: 'error',
    title: 'Python Required',
    message: 'Python is required to run this application',
    detail: 'This application requires Python 3.8 or higher to run the portfolio server.\n\nPlease install Python and try again.',
    buttons: ['Install Python (Official)', 'Install Python (Homebrew)', 'Cancel'],
    defaultId: 0,
    cancelId: 2
  });

  switch (result) {
    case 0:
      // Open official Python download
      shell.openExternal('https://www.python.org/downloads/macos/');
      break;
    case 1:
      // Show Homebrew instructions
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Install Python via Homebrew',
        message: 'Install Python using Homebrew',
        detail: 'Open Terminal and run:\n\n1. Install Homebrew (if not installed):\n   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\n\n2. Install Python:\n   brew install python\n\n3. Restart this application'
      });
      break;
    default:
      app.quit();
  }
}

function startPythonServer() {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev 
      ? path.join(__dirname, '../main.py')
      : path.join(process.resourcesPath, 'python-backend/main.py');
    
    console.log('Starting Python server at:', pythonPath);
    
    let pythonExe;
    try {
      pythonExe = findPythonExecutable();
    } catch (error) {
      console.error('Failed to find Python:', error.message);
      
      // Show user-friendly dialog with installation options
      showPythonInstallDialog();
      reject(error);
      return;
    }
    
    pythonProcess = spawn(pythonExe, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', SERVER_PORT.toString()], {
      cwd: isDev 
        ? path.join(__dirname, '..')
        : path.join(process.resourcesPath, 'python-backend'),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Python stdout:', output);
    });

    pythonProcess.stderr.on('data', (data) => {
      const output = data.toString();
      console.log('Python stderr:', output);
      
      if (output.includes('Uvicorn running on')) {
        console.log('Python server started successfully!');
        resolve();
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      reject(error);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
    });

    // Timeout fallback - wait longer for server to be ready
    setTimeout(() => {
      console.log('Checking server health...');
      checkServerHealth()
        .then(() => {
          console.log('Server health check passed!');
          resolve();
        })
        .catch((error) => {
          console.error('Server health check failed:', error);
          reject(new Error('Server health check failed'));
        });
    }, 8000);
  });
}

async function checkServerHealth() {
  try {
    console.log(`Checking health at: ${SERVER_URL}/api/progress/status`);
    const response = await axios.get(`${SERVER_URL}/api/progress/status`, { timeout: 5000 });
    console.log('Health check response:', response.data);
    return true;
  } catch (error) {
    console.error('Health check error details:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw new Error(`Server not responding: ${error.message}`);
  }
}

function stopPythonServer() {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
  }
}

// Window management
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    title: 'SET Portfolio Manager',
    show: false
  });

  // Create application menu
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Refresh',
          accelerator: 'CmdOrCtrl+R',
          click: () => mainWindow.reload()
        },
        {
          label: 'Developer Tools',
          accelerator: 'F12',
          click: () => mainWindow.webContents.openDevTools()
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => app.quit()
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About SET Portfolio Manager',
              message: 'SET Portfolio Manager v1.0.0',
              detail: 'Desktop application for Thai stock market data management.'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(async () => {
  try {
    console.log('Starting application...');
    
    // Start Python server first
    await startPythonServer();
    console.log('Python server started successfully');
    
    // Wait a moment for server to be fully ready
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Create window and load the app
    createWindow();
    mainWindow.loadURL(SERVER_URL);
    
  } catch (error) {
    console.error('Failed to start application:', error);
    
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application server:\n${error.message}\n\nPlease ensure Python and all dependencies are installed.`
    );
    
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopPythonServer();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopPythonServer();
});

// Handle app termination
process.on('SIGINT', () => {
  stopPythonServer();
  app.quit();
});

process.on('SIGTERM', () => {
  stopPythonServer();
  app.quit();
});