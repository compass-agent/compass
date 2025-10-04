const { spawn } = require("child_process")
require("dotenv").config()

// Known PowerShell startup messages to filter out
const startupMessages = [
  "Windows PowerShell",
  "Copyright (C) Microsoft Corporation. All rights reserved.",
  "Try the new cross-platform PowerShell https://aka.ms/pscore6",
]

const shellPromptMessages = {
  win32: startupMessages,
  darwin: [], // Mac doesn't need to filter startup messages
  linux: [],
}

const currentPlatformMessages = shellPromptMessages[process.platform] || []

// Store terminal instances and logs
let terminals = {} // Store terminal instances by ID
const lastOutputs = {}
const shell =
  process.platform === "win32"
    ? "powershell.exe"
    : process.env.SHELL || "/bin/zsh" // Prefer user's default shell, fallback to zsh
function handleTerminalEvents(ipcMain) {
  // Handle terminal creation
  ipcMain.handle("terminal.create", (event, { id, command }) => {
    if (terminals[id]) {
      terminals[id].kill()
    }

    const terminalProcess = spawn(shell, [], {
      shell: true,
      env: process.env,
      cwd: process.cwd(),
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    })

    terminals[id] = terminalProcess // Store the terminal instance

    // Send terminal output to the renderer
    terminalProcess.stdout.on("data", (data) => {
      const output = data.toString()

      if (
        output.length === 0 ||
        output === lastOutputs[id] ||
        currentPlatformMessages.some((msg) => output.includes(msg))
      )
        return

      lastOutputs[id] = output
      event.sender.send(`terminal.output.${id}`, output)
    })

    terminalProcess.stderr.on("data", (data) => {
      const errorOutput = data.toString().trim()
      if (errorOutput.length === 0) return
      event.sender.send(`terminal.error.${id}`, errorOutput)
    })

    return { success: true }
  })

  // Handle user input from renderer
  ipcMain.handle("terminal.input", (event, { id, input }) => {
    const terminalProcess = terminals[id]
    if (!terminalProcess) {
      return { success: false, error: "Terminal not found" }
    }
    if (input.trim()) {
      terminalProcess.stdin.write(input + "\n")
      return { success: true }
    } else {
      return { success: false, error: "Empty input" }
    }
  })

  //Handle terminal closing
  ipcMain.handle("terminal.close", (event, id) => {
    const terminalProcess = terminals[id]
    if (terminalProcess) {
      terminalProcess.kill()
      delete terminals[id]
      delete lastOutputs[id]

      return { success: true }
    }
    return { success: false }
  })

  ipcMain.handle("terminal.sendSignal", (event, { id, signal }) => {
    const terminalProcess = terminals[id]
    if (terminalProcess) {
      terminalProcess.kill(signal)
      if (signal === "SIGINT") {
        event.sender.send(`terminal.output.${id}`, `PS ${process.cwd()}>`)
      }
      return { success: true }
    }
    return { success: false, error: "Terminal not found" }
  })

  ipcMain.handle("terminal.kill", (event, id) => {
    const terminalProcess = terminals[id]
    if (terminalProcess) {
      try {
        if (process.platform === "win32") {
          // Windows: Use `taskkill` to stop the process
          spawn("taskkill", ["/PID", terminalProcess.pid, "/F"])
        } else {
          // macOS & Linux: Send SIGINT (Ctrl+C equivalent)
          terminalProcess.kill("SIGINT")
        }
        delete terminals[id]
        delete lastOutputs[id]
        return { success: true }
      } catch (error) {
        return { success: false, error }
      }
    }
    return { success: false, error: "Terminal not found" }
  })
}

module.exports = { handleTerminalEvents }
