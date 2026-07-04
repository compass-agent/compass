const { spawn, execFile } = require("child_process")
const path = require("path")
const { app } = require("electron")
const fs = require("fs")

// Set up error logging with proper directory creation
const logDir = path.join(app.getPath("userData") || __dirname, "logs")
const logPath = path.join(logDir, "electron_main.log")

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
  console.log(message)
}

let backendProcess = null
let restartCount = 0
let stoppingIntentionally = false
const MAX_AUTO_RESTARTS = 3

/**
 * Directory where user-facing artifacts (SAP models, generated configs)
 * are stored. Shared with the backend via the WORKSPACE_FOLDER env var.
 */
function getWorkspaceDir() {
  const dir = path.join(app.getPath("documents"), "Compass")
  try {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
  } catch (error) {
    logToFile(`Failed to create workspace dir ${dir}: ${error.message}`)
  }
  return dir
}

function findBackendExecutable() {
  const resourcesPath = process.resourcesPath
  const possibleLocations = [
    // onedir bundle (current layout)
    path.join(resourcesPath, "backend", "compass_backend", "compass_backend.exe"),
    // legacy onefile layouts, kept as fallbacks
    path.join(resourcesPath, "backend", "compass_backend.exe"),
    path.join(resourcesPath, "compass_backend.exe"),
  ]
  return possibleLocations.find((loc) => fs.existsSync(loc)) || null
}

/**
 * Kill any orphaned backend from a previous run so port 5001 is free.
 * Only used in production, where the backend exe name is unambiguous.
 */
function killOrphanedBackends() {
  return new Promise((resolve) => {
    execFile(
      "taskkill",
      ["/F", "/IM", "compass_backend.exe", "/T"],
      (error) => {
        // Exit code 128 means "not found", which is the normal case
        if (!error) {
          logToFile("Killed orphaned compass_backend.exe process(es)")
        }
        resolve()
      }
    )
  })
}

/**
 * Spawns the packaged Python backend. No-op in development, where the
 * backend is started separately via `npm run dev`.
 * @returns {ChildProcess|null}
 */
function startBackend() {
  if (!app.isPackaged) {
    logToFile("Development mode: backend is expected to run via `npm run dev`")
    return null
  }

  if (backendProcess) {
    logToFile("Backend already running; skipping start")
    return backendProcess
  }

  logToFile(`App path: ${app.getAppPath()}`)
  logToFile(`Resources path: ${process.resourcesPath}`)
  logToFile(`User data path: ${app.getPath("userData")}`)

  const backendPath = findBackendExecutable()
  if (!backendPath) {
    logToFile("ERROR: Backend executable not found in any expected location")
    throw new Error(
      "Backend executable not found. Please reinstall the application."
    )
  }

  logToFile(`Starting backend: ${backendPath}`)
  stoppingIntentionally = false

  backendProcess = spawn(backendPath, [], {
    cwd: path.dirname(backendPath),
    windowsHide: true, // Prevent command window from showing
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
      COMPASS_ENV: "production",
      WORKSPACE_FOLDER: getWorkspaceDir(),
    },
  })

  backendProcess.stdout.on("data", (data) => {
    logToFile(`Backend stdout: ${data.toString().trim()}`)
  })

  backendProcess.stderr.on("data", (data) => {
    logToFile(`Backend stderr: ${data.toString().trim()}`)
  })

  backendProcess.on("error", (error) => {
    logToFile(`Backend spawn error: ${error.message}`)
  })

  backendProcess.on("exit", (code, signal) => {
    logToFile(`Backend exited with code ${code}, signal ${signal}`)
    backendProcess = null
    if (!stoppingIntentionally && restartCount < MAX_AUTO_RESTARTS) {
      restartCount += 1
      logToFile(
        `Auto-restarting backend (attempt ${restartCount}/${MAX_AUTO_RESTARTS})`
      )
      setTimeout(() => {
        try {
          startBackend()
        } catch (error) {
          logToFile(`Auto-restart failed: ${error.message}`)
        }
      }, 2000)
    }
  })

  return backendProcess
}

function stopBackend() {
  stoppingIntentionally = true
  if (backendProcess) {
    logToFile(`Stopping backend (pid ${backendProcess.pid})`)
    try {
      // taskkill with /T also terminates any child processes
      execFile("taskkill", ["/F", "/PID", String(backendProcess.pid), "/T"])
    } catch (error) {
      logToFile(`taskkill failed, falling back to kill(): ${error.message}`)
      try {
        backendProcess.kill()
      } catch (_) {
        /* already dead */
      }
    }
    backendProcess = null
  }
}

async function restartBackend() {
  logToFile("Restart backend requested")
  stopBackend()
  await killOrphanedBackends()
  restartCount = 0
  await new Promise((resolve) => setTimeout(resolve, 1000))
  return startBackend()
}

module.exports = {
  startBackend,
  stopBackend,
  restartBackend,
  killOrphanedBackends,
  getWorkspaceDir,
  logToFile,
}
