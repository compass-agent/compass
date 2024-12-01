const { app, BrowserWindow, ipcMain, Menu } = require("electron");
const path = require("path");
const { WINDOW_CONFIG } = require("./constants");
require("dotenv").config();


let mainWindow;
function createWindow() {
  mainWindow = new BrowserWindow({
    width: WINDOW_CONFIG.WIDTH,
    height: WINDOW_CONFIG.HEIGHT,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Specify the preload script
      // contextIsolation: true, // Ensures that contextBridge works securely
      // enableRemoteModule: false, // Disable deprecated remote module
      // nodeIntegration: false, // Disable direct Node.js access in the renderer
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
    },
    alwaysOnTop: true,
    frame: true, // Turned into true as had conflict with maximize button
    transparent: false, // Turned into true as had conflict with maximize button
    trafficLightPosition: { x: 10, y: 10 }, // Position of the window control buttons (close, minimize, and maximize) in macOS
    hasShadow: true,
    resizable: true,
    minWidth: WINDOW_CONFIG.MIN_WIDTH,
    minHeight: WINDOW_CONFIG.MIN_HEIGHT,
  });

  mainWindow.setResizable(true);

  const indexPath = path.join(__dirname, "../renderer/index.html");
  mainWindow.loadFile(indexPath);

  // Remove the default menu
  Menu.setApplicationMenu(null);

  if (process.env.NODE_ENV === "development") {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Handle window actions from the renderer process
ipcMain.on("close-window", () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.on("minimize-window", () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on("maximize-window", () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.restore(); // Restore to the previous size
    } else {
      console.log("Main Process: Maximizing the window...");
      mainWindow.maximize();
    }
  }
});
