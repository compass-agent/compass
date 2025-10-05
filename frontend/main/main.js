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
const BOUNDS_FILE = path.join(app.getPath("userData"), "window-bounds.json")

function saveWindowBounds() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    const bounds = mainWindow.getBounds()
    fs.writeFileSync(BOUNDS_FILE, JSON.stringify(bounds))
  }
}

function loadWindowBounds() {
  try {
    if (fs.existsSync(BOUNDS_FILE)) {
      return JSON.parse(fs.readFileSync(BOUNDS_FILE, "utf8"))
    }
  } catch (error) {
    console.log("Could not load window bounds:", error.message)
  }
  return null
}

// Agent persistence
const AGENT_FILE = path.join(app.getPath("userData"), "last-agent.json")

function saveLastAgent(agentData) {
  try {
    fs.writeFileSync(AGENT_FILE, JSON.stringify(agentData))
  } catch (error) {
    console.error("Failed to save last agent:", error.message)
  }
}

function loadLastAgent() {
  try {
    if (fs.existsSync(AGENT_FILE)) {
      const agentData = JSON.parse(fs.readFileSync(AGENT_FILE, "utf8"))
      return agentData
    }
  } catch (error) {
    console.error("Could not load last agent:", error.message)
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

  // Save window bounds when closing
  mainWindow.on("close", () => {
    saveWindowBounds()

    // Close template training window if it's open
    if (templateTrainingWindow && !templateTrainingWindow.isDestroyed()) {
      templateTrainingWindow.close()
    }
  })

  setupFileHandlers(mainWindow)
  setupWindowHandlers(mainWindow)
}

function createTemplateTrainingWindow() {
  const mainBounds = mainWindow
    ? mainWindow.getBounds()
    : { x: 100, y: 100, width: 900, height: 700 }
  templateTrainingWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    x: Math.max(0, (mainBounds.x || 0) + 40),
    y: Math.max(0, (mainBounds.y || 0) + 40),
    modal: false,
    title: "Agent Hub",
    frame: false,
    titleBarStyle: "hidden",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
      webSecurity: false,
    },
    show: false,
  })

  const templateTrainingPath = path.join(
    __dirname,
    "../renderer/template-training/index.html"
  )
  templateTrainingWindow.loadFile(templateTrainingPath)

  templateTrainingWindow.once("ready-to-show", () => {
    try {
      templateTrainingWindow.show()
      templateTrainingWindow.focus()
    } catch {
      /* noop */
    }
  })

  templateTrainingWindow.on("closed", () => {
    templateTrainingWindow = null
  })
}

// IPC Handlers
ipcMain.on("open-template-training", () => {
  if (!templateTrainingWindow) {
    createTemplateTrainingWindow()
  } else {
    templateTrainingWindow.focus()
  }
})

ipcMain.on("close-template-training", () => {
  if (templateTrainingWindow && !templateTrainingWindow.isDestroyed()) {
    templateTrainingWindow.close()
  }
})

// Handle agent selection from template training window
ipcMain.handle("agent-selected", async (event, agentData) => {
  // Validate agent data
  if (!agentData || typeof agentData !== "object") {
    console.error("Invalid agent data received in main process:", agentData)
    return { success: false, error: "Invalid agent data" }
  }

  // Save the selected agent for persistence
  saveLastAgent(agentData)

  // Send the selected agent to the main window
  if (mainWindow && !mainWindow.isDestroyed()) {
    try {
      // Create a clean copy of the data to avoid any serialization issues
      const cleanData = {
        agentId: agentData.agentId,
        name: agentData.name,
        description: agentData.description,
        generalTools: agentData.generalTools,
        softwareIntegrations: agentData.softwareIntegrations,
        configuration: agentData.configuration,
      }

      mainWindow.webContents.send("update-selected-agent", cleanData)
    } catch (error) {
      console.error("Error sending to main window:", error)
      return { success: false, error: error.message }
    }
  } else {
    console.error("Main window is not available")
    return { success: false, error: "Main window not available" }
  }

  // Return success response
  return { success: true }
})

// Handle loading last agent on startup
ipcMain.handle("load-last-agent", async () => {
  return loadLastAgent()
})

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
