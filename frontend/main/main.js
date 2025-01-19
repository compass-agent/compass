const { app, BrowserWindow, ipcMain, Menu, dialog } = require("electron");
const path = require("path");
const fs = require("fs");
const {
  default: installExtension,
  REACT_DEVELOPER_TOOLS,
} = require("electron-devtools-installer");
const { handleCoordinatePreview } = require("./coordinatePreview");
require("dotenv").config();

const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 500,
  MIN_HEIGHT: 120,
};

let mainWindow;
let previewWindow = null;

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
}

app.whenReady().then(() => {
  createWindow();
  handleCoordinatePreview(ipcMain);
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
  const { width, height } =
    require("electron").screen.getPrimaryDisplay().workAreaSize;
  mainWindow.setBounds({
    x: width - mainWindow.getBounds().width,
    y: height - mainWindow.getBounds().height,
  });
  mainWindow.webContents.send("move-to-bottom-right-done");
});

ipcMain.on("close-window", () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.on("minimize-window", () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on("restore-window", (event) => {
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

ipcMain.handle("save-file", async (event, { filePath, content }) => {
  try {

    fs.writeFileSync(filePath, content, "utf-8");
    console.log("Main Process: File saved successfully");

    return { success: true };
  } catch (error) {
    console.error("Main Process: Failed to save file:", error);
    return { success: false, error: error.message };
  }
});


ipcMain.handle("open-file-dialog", async () => {
  try {
    // Temporarily disable alwaysOnTop
    mainWindow.setAlwaysOnTop(false);
    const result = await dialog.showOpenDialog({
      properties: ["openFile"],
      filters: [
        { name: "Text Files", extensions: ["txt"] },
        { name: "All Files", extensions: ["*"] },
      ],
    });
    if (result.canceled) {
      return { success: false, error: "File selection was canceled" };
    } else {
      const filePath = result.filePaths[0];
      const fileName = path.basename(filePath);
      const content = fs.readFileSync(filePath, "utf-8");
      return { success: true, filePath, fileName, content };
    }
    mainWindow.setAlwaysOnTop(true);
  } catch (error) {
    console.error("Main Process: Failed to open file dialog:", error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle("save-file-dialog", async (event, content) => {
  try {
    // Temporarily disable alwaysOnTop
    mainWindow.setAlwaysOnTop(false);
    const result = await dialog.showSaveDialog({
      title: "Save File",
      defaultPath: path.join(app.getPath("documents"), "untitled.txt"),
      filters: [
        { name: "Text Files", extensions: ["txt"] },
        { name: "All Files", extensions: ["*"] },
      ],
    });
    if (result.canceled) {
      return { success: false, error: "Save was canceled" };
    } else {
      const filePath = result.filePath;
      fs.writeFileSync(filePath, content, "utf-8");
      return { success: true, filePath };
    }
    mainWindow.setAlwaysOnTop(true);
  } catch (error) {
    console.error("Main Process: Failed to save file:", error);
    return { success: false, error: error.message };
  }
});

