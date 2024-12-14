const { app, BrowserWindow, ipcMain, Menu } = require("electron");
const path = require("path");
const {
  default: installExtension,
  REACT_DEVELOPER_TOOLS,
} = require("electron-devtools-installer");

require("dotenv").config();

const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 500,
  MIN_HEIGHT: 120,
};

let mainWindow;
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
    transparent: false, // Turned into true as had conflict with maximize button restore
    trafficLightPosition: { x: 10, y: 10 }, // Position of the window control buttons (close, minimize, and maximize) in macOS
    hasShadow: true,
    resizable: true,
    minWidth: WINDOW_CONFIG.MIN_WIDTH,
    minHeight: WINDOW_CONFIG.MIN_HEIGHT,
    //backgroundColor: "#00000000", // Ensure a transparent background
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

let previousBounds = null; // To store the previous window bounds

ipcMain.on("toggle-fullscreen", (_, isFullscreen) => {
  if (!mainWindow) return;
  if (isFullscreen) {
    // Restore to the previous bounds or default size
    if (previousBounds) {
      mainWindow.setBounds(previousBounds); // Restore the previous window size
    } else {
      mainWindow.setBounds({
        y: mainWindow.getBounds().y,
        height: WINDOW_CONFIG.HEIGHT, // Default height
      });
    }
    previousBounds = null; // Clear previous bounds
  } else {
    // Save the current bounds and minimize height
    previousBounds = mainWindow.getBounds();
    mainWindow.setBounds({
      y: mainWindow.getBounds().y,
      height: WINDOW_CONFIG.MIN_HEIGHT,
    });
  }
});

ipcMain.on("move-to-bottom-right", () => {
  if (!mainWindow) return;
  const { width, height } = require("electron").screen.getPrimaryDisplay().workAreaSize;
  mainWindow.setBounds({
    x: width - mainWindow.getBounds().width,
    y: height - mainWindow.getBounds().height,
  });
});

ipcMain.on("close-window", () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.on("minimize-window", () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('restore-window', (event) => {
  if (mainWindow) {
    mainWindow.restore();
  }
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
