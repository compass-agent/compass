const { app, BrowserWindow, ipcMain, Menu, dialog } = require("electron")
const path = require("path")
const fs = require("fs")
const { handleCoordinatePreview } = require("./components/coordinatePreview")
const { handleTerminalEvents } = require("./components/terminalEvents")
const setupFileHandlers = require("./components/fileHandlers")
const setupWindowHandlers = require("./components/windowHandler")
require("dotenv").config()
const { startBackend, logToFile } = require("./backendManager")

if (process.platform === "darwin") {
  app.setName("Compass")
  app.name = "Compass"
}

// Only import devtools in development
let isDev = process.env.NODE_ENV === "development"

const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 300,
  MIN_HEIGHT: 45,
  MINIMAL_HEIGHT: 45,
}

// Window bounds persistence
const BOUNDS_FILE = path.join(app.getPath('userData'), 'window-bounds.json')

function saveWindowBounds() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    const bounds = mainWindow.getBounds()
    fs.writeFileSync(BOUNDS_FILE, JSON.stringify(bounds))
  }
}

function loadWindowBounds() {
  try {
    if (fs.existsSync(BOUNDS_FILE)) {
      return JSON.parse(fs.readFileSync(BOUNDS_FILE, 'utf8'))
    }
  } catch (error) {
    console.log('Could not load window bounds:', error.message)
  }
  return null
}

let mainWindow
let previewWindow = null
let templateTrainingWindow = null

function createMenu() {
  const template = [
    {
      label: "Compass",
      submenu: [
        { role: "about" },
        { type: "separator" },
        { role: "services" },
        { type: "separator" },
        { role: "hide" },
        { role: "hideOthers" },
        { role: "unhide" },
        { type: "separator" },
        { role: "quit" },
      ],
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "delete" },
        { role: "selectAll" },
      ],
    },
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

function createWindow() {
  const savedBounds = loadWindowBounds()
  
  mainWindow = new BrowserWindow({
    width: savedBounds?.width || WINDOW_CONFIG.WIDTH,
    height: savedBounds?.height || WINDOW_CONFIG.HEIGHT,
    x: savedBounds?.x,
    y: savedBounds?.y,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Specify the preload script
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false,
      enableHardwareAcceleration: true,
    },
    alwaysOnTop: true,
    frame: false,
    transparent: true, // Enable window transparency
    trafficLightPosition: { x: 10, y: 10 }, // Position of the window control buttons (close, minimize, and maximize) in macOS
    hasShadow: true,
    resizable: true,
    minWidth: WINDOW_CONFIG.MIN_WIDTH,
    minHeight: WINDOW_CONFIG.MIN_HEIGHT,
    backgroundColor: "#00000000", // Ensure a transparent background
    title: "Compass",
  })

  mainWindow.setResizable(true)

  const indexPath = path.join(__dirname, "../renderer/main-chat/index.html")
  mainWindow.loadFile(indexPath)
  Menu.setApplicationMenu(null)
  // Instead of Menu.setApplicationMenu(null), call createMenu
  if (process.platform === "darwin") {
    createMenu()
  }

  if (isDev || true) {
    // Open DevTools in detached mode to preserve window transparency
    mainWindow.webContents.openDevTools({ mode: "detach" })
  }

  // Save window bounds when closing
  mainWindow.on('close', () => {
    saveWindowBounds()
  })

  setupFileHandlers(mainWindow)
  setupWindowHandlers(mainWindow)
}

function createTemplateTrainingWindow() {
  templateTrainingWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: false, // Changed to false for security
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
      webSecurity: false, // Add this for development
    },
    show: false,
  })

  const templateTrainingPath = path.join(
    __dirname,
    "../renderer/template-training/index.html"
  )
  console.log("Loading template training from:", templateTrainingPath)
  templateTrainingWindow.loadFile(templateTrainingPath)

  // Remove or comment out these lines
  templateTrainingWindow.webContents.on("did-finish-load", () => {
    console.log("Template training window finished loading")
    // templateTrainingWindow.webContents.openDevTools();  // Remove this line
  })

  templateTrainingWindow.once("ready-to-show", () => {
    console.log("Template training window ready to show")
    templateTrainingWindow.center()
    templateTrainingWindow.show()
  })

  // Remove or comment out this block
  // if (process.env.NODE_ENV === 'development') {
  //   templateTrainingWindow.webContents.openDevTools();
  // }

  templateTrainingWindow.on("closed", () => {
    templateTrainingWindow = null
  })
}

app.whenReady().then(() => {
  if (!isDev) {
    // Start the Python backend in production
    try {
      logToFile("Starting backend process...")
      backendProcess = startBackend()

      // Make sure to terminate the backend process when the app quits
      app.on("quit", () => {
        saveWindowBounds()
        logToFile("Application quitting, terminating backend process")
        if (backendProcess) {
          backendProcess.kill()
        }
      })
    } catch (error) {
      logToFile(`Error starting backend: ${error.message}`)
      console.error("Failed to start backend:", error)

      // Show error dialog to user
      dialog.showErrorBox(
        "Backend Error",
        `Failed to start the backend process: ${error.message}\n\nPlease check the logs for more details.`
      )
    }
  }

  if (process.platform === "darwin") {
    app.name = "Compass"
  }
  createWindow()
  handleCoordinatePreview(ipcMain)
  handleTerminalEvents(ipcMain)
})

app.on("window-all-closed", () => {
  if (previewWindow) {
    previewWindow = null
  }
  if (process.platform !== "darwin") {
    app.quit()
  }
})

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

ipcMain.on("open-template-training", () => {
  if (!templateTrainingWindow) {
    createTemplateTrainingWindow()
  }
})
