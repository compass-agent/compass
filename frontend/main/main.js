const { app, BrowserWindow, ipcMain, Menu, dialog } = require("electron");
const path = require("path");
const {
  default: installExtension,
  REACT_DEVELOPER_TOOLS,
} = require("electron-devtools-installer");
const { handleCoordinatePreview } = require("./coordinatePreview");
const { handleTerminalEvents } = require("./terminalEvents");
const setupFileHandlers = require('./fileHandlers'); 
const setupWindowHandlers = require('./windowHandler');
require("dotenv").config();

const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 500,
  MIN_HEIGHT: 120,
};

let mainWindow;
let previewWindow = null;
let templateTrainingWindow = null;

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
  });

  mainWindow.setResizable(true);

  const indexPath = path.join(__dirname, "../renderer/index.html");
  mainWindow.loadFile(indexPath);

  // Remove the default menu
  Menu.setApplicationMenu(null);

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
      nodeIntegration: true,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false, // Don't show until ready
  });

  templateTrainingWindow.loadFile(
    path.join(__dirname, '../renderer/template-training/index.html')
  );

  // Center the window and show when ready
  templateTrainingWindow.once('ready-to-show', () => {
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