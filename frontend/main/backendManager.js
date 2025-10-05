const { spawn } = require("child_process")
const path = require("path")
const { app } = require("electron")
const isDev = process.env.NODE_ENV === "development"
const fs = require("fs")

// Set up error logging with proper directory creation
const logDir = path.join(app.getPath("userData") || __dirname)
const logPath = path.join(logDir, "compass_backend.log")

// Ensure log directory exists
try {
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true })
  }
} catch (error) {
  console.error("Failed to create log directory:", error)
}

function logToFile(message) {
  try {
    fs.appendFileSync(logPath, `${new Date().toISOString()}: ${message}\n`)
  } catch (error) {
    console.error("Failed to write to log file:", error)
  }
}

/**
 * Manages the Python backend process for the Compass application
 * Handles both development and production environments
 * @returns {ChildProcess} The spawned backend process
 */
function startBackend() {
  let backendPath
  let backendProcess

  logToFile(`App path: ${app.getAppPath()}`)
  logToFile(`User data path: ${app.getPath("userData")}`)
  logToFile(`Executable path: ${app.getPath("exe")}`)

  try {
    // In production, use the bundled executable
    let resourcesPath
    try {
      resourcesPath = app.getPath("resources")
    } catch (error) {
      // Fallback: construct the path based on the app path
      resourcesPath = path.join(app.getAppPath(), "..", "..")
      if (app.getAppPath().includes("app.asar")) {
        resourcesPath = path.join(app.getAppPath(), "..")
      }
    }

    const possibleLocations = [
      // Standard location in resources
      path.join(resourcesPath, "backend", "compass_backend.exe"),
      // Direct path in resources folder
      path.join(resourcesPath, "compass_backend.exe"),
      // Try app.asar location
      path.join(
        resourcesPath,
        "app.asar",
        "resources",
        "backend",
        "compass_backend.exe"
      ),
      // Fallback to original location
      path.join(resourcesPath, "backend", "compass_backend.exe"),
      // Add the exact path from the screenshot
      path.join(
        app.getPath("exe"),
        "..",
        "resources",
        "backend",
        "compass_backend.exe"
      ),
      // Check in dist structure
      path.join(
        process.cwd(),
        "dist",
        "win-unpacked",
        "resources",
        "backend",
        "compass_backend.exe"
      ),
    ]

    // Find the first location that exists
    backendPath = possibleLocations.find((loc) => {
      return fs.existsSync(loc)
    })

    if (!backendPath) {
      const errorMsg = `Backend executable not found in any of the expected locations`
      logToFile(errorMsg)
      throw new Error(errorMsg)
    }

    logToFile(`Using backend at: ${backendPath}`)

    backendProcess = spawn(backendPath, [], {
      windowsHide: true, // Prevent command window from showing
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1", // Ensure Python output isn't buffered
        COMPASS_ENV: process.env.NODE_ENV || "production", // Pass environment type
      },
    })

    // Handle backend output
    backendProcess.stdout.on("data", (data) => {
      const output = data.toString()
      logToFile(`Backend output: ${output}`)
    })

    // Handle backend errors
    backendProcess.stderr.on("data", (data) => {
      const errorOutput = data.toString()
      logToFile(`Backend error: ${errorOutput}`)
    })

    backendProcess.on("exit", (code, signal) => {
      logToFile(`Backend process exited with code ${code} and signal ${signal}`)
    })

    return backendProcess
  } catch (error) {
    logToFile(`Error in startBackend: ${error.message}\n${error.stack}`)
    throw error
  }
}

module.exports = { startBackend, logToFile }
