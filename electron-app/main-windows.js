const { app, BrowserWindow, dialog, Menu, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

let mainWindow;
let pythonProcess;
const isDev = process.argv.includes('--dev');
const SERVER_PORT = 8000; // Use the same port as your main.py
const SERVER_URL = `http://localhost:${SERVER_PORT}`;

// Python backend management for Windows
function findPythonExecutable() {
  const possiblePaths = [
    'python.exe',
    'python3.exe',
    'py.exe',
    path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python311', 'python.exe'),
    path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python310', 'python.exe'),
    path.join(process.env.LOCALAPPDATA, 'Programs', 'Python', 'Python39', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python311', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python310', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python39', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python311', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python310', 'python.exe'),
    path.join(process.env.PROGRAMFILES, 'Python39', 'python.exe'),
    'C:\\Python311\\python.exe',
    'C:\\Python310\\python.exe',
    'C:\\Python39\\python.exe',
    'C:\\Python311\\python.exe',
    'C:\\Python310\\python.exe',
    'C:\\Python39\\python.exe'
  ];
  
  const { execSync } = require('child_process');
  
  for (const pythonPath of possiblePaths) {
    try {
      execSync(`"${pythonPath}" --version`, { stdio: 'ignore' });
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
    buttons: ['Install Python (Official)', 'Install Python (Microsoft Store)', 'Cancel'],
    defaultId: 0,
    cancelId: 2
  });

  switch (result) {
    case 0:
      // Open official Python download
      shell.openExternal('https://www.python.org/downloads/windows/');
      break;
    case 1:
      // Show Microsoft Store instructions
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Install Python via Microsoft Store',
        message: 'Install Python using Microsoft Store',
        detail: '1. Open Microsoft Store\n2. Search for "Python"\n3. Install the latest version\n4. Restart this application'
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
    
    // Use the main.py directly with the correct arguments
    const pythonArgs = [
      pythonPath,
      '--host', '127.0.0.1',
      '--port', SERVER_PORT.toString()
    ];
    
    console.log('Starting Python with args:', pythonArgs);
    
    pythonProcess = spawn(pythonExe, pythonArgs, {
      cwd: isDev 
        ? path.join(__dirname, '..')
        : path.join(process.resourcesPath, 'python-backend'),
      stdio: ['pipe', 'pipe', 'pipe'],
      windowsHide: false // Show console for debugging
    });

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Python stdout:', output);
    });

    pythonProcess.stderr.on('data', (data) => {
      const output = data.toString();
      console.log('Python stderr:', output);
      
      // Check for successful server start
      if (output.includes('Uvicorn running on') || output.includes('Application startup complete')) {
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
    }, 10000); // Increased timeout for Windows
  });
}

async function checkServerHealth() {
  try {
    console.log(`Checking health at: ${SERVER_URL}/`);
    const response = await axios.get(`${SERVER_URL}/`, { timeout: 10000 });
    console.log('Health check response status:', response.status);
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
    console.log('Stopping Python server...');
    pythonProcess.kill('SIGTERM');
    
    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (pythonProcess) {
        console.log('Force killing Python process...');
        pythonProcess.kill('SIGKILL');
        pythonProcess = null;
      }
    }, 5000);
  }
}

// Window management
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false
    },
    icon: path.join(__dirname, 'assets/icon.ico'),
    title: 'SET Portfolio Manager',
    show: false,
    frame: true,
    resizable: true,
    maximizable: true,
    minimizable: true,
    center: true,
    // Windows-specific options
    autoHideMenuBar: false,
    titleBarStyle: 'default'
  });

  // Create application menu
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Refresh',
          accelerator: 'Ctrl+R',
          click: () => mainWindow.reload()
        },
        {
          label: 'Developer Tools',
          accelerator: 'F12',
          click: () => mainWindow.webContents.openDevTools()
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'Ctrl+Q',
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
              detail: 'Desktop application for Thai stock market data management.\n\nBuilt with Electron and FastAPI.'
            });
          }
        },
        {
          label: 'Open in Browser',
          click: () => {
            shell.openExternal(SERVER_URL);
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

  // Handle window errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorDescription);
    dialog.showErrorBox(
      'Load Error',
      `Failed to load the application:\n${errorDescription}\n\nPlease check if the Python server is running.`
    );
  });
}

// App lifecycle
app.whenReady().then(async () => {
  try {
    console.log('Starting SET Portfolio Manager...');
    
    // Start Python server first
    await startPythonServer();
    console.log('Python server started successfully');
    
    // Wait a moment for server to be fully ready
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Create window and load the app
    createWindow();
    mainWindow.loadURL(SERVER_URL);
    
  } catch (error) {
    console.error('Failed to start application:', error);
    
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start the application server:\n${error.message}\n\nPlease ensure Python and all dependencies are installed.\n\nYou can also try running the application manually:\n1. Open Command Prompt\n2. Navigate to the application folder\n3. Run: python main.py`
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

// Handle Windows-specific events
if (process.platform === 'win32') {
  app.on('second-instance', () => {
    // Someone tried to run a second instance, focus our window instead
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}
