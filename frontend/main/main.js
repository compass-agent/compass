const { app, BrowserWindow, ipcMain, Menu, dialog } = require("electron");
const path = require("path");
const {
  default: installExtension,
  REACT_DEVELOPER_TOOLS,
} = require("electron-devtools-installer");
const { handleCoordinatePreview } = require("./components/coordinatePreview");
const { handleTerminalEvents } = require("./components/terminalEvents");
const setupFileHandlers = require('./components/fileHandlers'); 
const setupWindowHandlers = require('./components/windowHandler');
require("dotenv").config();

if (process.platform === 'darwin') {
  app.setName('Compass');
  app.name = 'Compass';
}

const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 500,
  MIN_HEIGHT: 43,
  MINIMAL_HEIGHT: 43 
};

let mainWindow;
let previewWindow = null;
let templateTrainingWindow = null;

function createMenu() {
  const template = [
    {
      label: 'Compass',
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'delete' },
        { role: 'selectAll' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: WINDOW_CONFIG.WIDTH,
    height: WINDOW_CONFIG.HEIGHT,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Specify the preload script
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      enableHardwareAcceleration: true,
    },
    alwaysOnTop: true,
    frame: false, // Turned into true as had conflict with maximize button restore
    // transparent: true, // Turned into true as had conflict with maximize button restore
    trafficLightPosition: { x: 10, y: 10 }, // Position of the window control buttons (close, minimize, and maximize) in macOS
    hasShadow: true,
    resizable: true,
    minWidth: WINDOW_CONFIG.MIN_WIDTH,
    minHeight: WINDOW_CONFIG.MIN_HEIGHT,
    backgroundColor: "#00000000", // Ensure a transparent background
    title: 'Compass'
  });

  mainWindow.setResizable(true);

  const indexPath = path.join(__dirname, '../renderer/main-chat/index.html');
  mainWindow.loadFile(indexPath);
  Menu.setApplicationMenu(null);
  // Instead of Menu.setApplicationMenu(null), call createMenu
  if (process.platform === 'darwin') {
    createMenu();
  }

  if (process.env.NODE_ENV === "development") {
    mainWindow.webContents.openDevTools(); //{ mode: 'detach' }
    // Install React DevTools
    // ISSUE: The React tab does not apprear!
    installExtension(REACT_DEVELOPER_TOOLS)
      .then((name) => console.log(`Added Extension: ${name}`))
      .catch((err) => console.error("Failed to install React DevTools:", err));
  }

  setupFileHandlers(mainWindow);
  setupWindowHandlers(mainWindow);
}

function createTemplateTrainingWindow() {
  templateTrainingWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false,  // Changed to false for security
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false  // Add this for development
    },
    show: false,
  });

  const templateTrainingPath = path.join(__dirname, '../renderer/template-training/index.html');
  console.log('Loading template training from:', templateTrainingPath);
  templateTrainingWindow.loadFile(templateTrainingPath);

  // Add these lines for debugging
  templateTrainingWindow.webContents.on('did-finish-load', () => {
    console.log('Template training window finished loading');
    templateTrainingWindow.webContents.openDevTools();  // Force open dev tools
  });

  templateTrainingWindow.once('ready-to-show', () => {
    console.log('Template training window ready to show');
    templateTrainingWindow.center();
    templateTrainingWindow.show();
  });

  // Dev tools for debugging
  if (process.env.NODE_ENV === 'development') {
    templateTrainingWindow.webContents.openDevTools();
  }

  templateTrainingWindow.on('closed', () => {
    templateTrainingWindow = null;
  });
}

app.whenReady().then(() => {
  if (process.platform === 'darwin') {
    app.name = 'Compass';
  }
  createWindow();
  handleCoordinatePreview(ipcMain);
  handleTerminalEvents(ipcMain);
});

app.on("window-all-closed", () => {
  if (previewWindow) {
    previewWindow = null;
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

ipcMain.on('open-template-training', () => {
  if (!templateTrainingWindow) {
    createTemplateTrainingWindow();
  }
});

