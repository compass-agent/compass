const { ipcMain, app, dialog } = require("electron")
const fs = require("fs")
const path = require("path")

module.exports = (mainWindow) => {
  ipcMain.handle("save-file", async (event, { filePath, content }) => {
    try {
      if (!filePath) {
        throw new Error("File path is undefined")
      }

      // Normalize path for Windows
      const normalizedPath = path.normalize(filePath)

      // Ensure directory exists
      const directory = path.dirname(normalizedPath)
      if (!fs.existsSync(directory)) {
        fs.mkdirSync(directory, { recursive: true })
      }

      fs.writeFileSync(filePath, content || "", "utf-8")

      return { success: true, path: normalizedPath }
    } catch (error) {
      return { success: false, error: error.message }
    }
  })

  ipcMain.handle("read-file", async (event, filePath) => {
    try {
      if (!filePath) {
        return { success: false, error: "File path is undefined" }
      }

      // Normalize path for Windows
      const normalizedPath = path.normalize(filePath)

      // Check if path is absolute
      if (!path.isAbsolute(normalizedPath)) {
        return { success: false, error: "File path is relative" }
      }
      // Read file content
      const content = fs.readFileSync(normalizedPath, "utf-8")

      return { success: true, content }
    } catch (error) {
      console.error("Main Process: Failed to read file:", error)
      return { success: false, error: error.message }
    }
  })

  ipcMain.handle("open-file-dialog", async () => {
    try {
      // Temporarily disable alwaysOnTop
      mainWindow.setAlwaysOnTop(false)
      const result = await dialog.showOpenDialog({
        properties: ["openFile"],
        filters: [
          { name: "Text Files", extensions: ["txt"] },
          { name: "All Files", extensions: ["*"] },
        ],
      })
      if (result.canceled) {
        mainWindow.setAlwaysOnTop(true)
        return { success: false, error: "File selection was canceled" }
      } else {
        const filePath = result.filePaths[0]
        const fileName = path.basename(filePath)
        const content = fs.readFileSync(filePath, "utf-8")
        mainWindow.setAlwaysOnTop(true)
        return { success: true, filePath, fileName, content }
      }
    } catch (error) {
      console.error("Main Process: Failed to open file dialog:", error)
      return { success: false, error: error.message }
    }
  })

  ipcMain.handle("open-config-file-dialog", async () => {
    try {
      // Temporarily disable alwaysOnTop
      mainWindow.setAlwaysOnTop(false)
      const result = await dialog.showOpenDialog({
        properties: ["openFile"],
        filters: [
          { name: "YAML Files", extensions: ["yaml", "yml"] },
          { name: "All Files", extensions: ["*"] },
        ],
        title: "Select SAP Configuration File",
      })
      if (result.canceled) {
        mainWindow.setAlwaysOnTop(true)
        return { success: false, error: "File selection was canceled" }
      } else {
        const filePath = result.filePaths[0]
        const fileName = path.basename(filePath)
        mainWindow.setAlwaysOnTop(true)
        return { success: true, filePath, fileName }
      }
    } catch (error) {
      console.error("Main Process: Failed to open config file dialog:", error)
      return { success: false, error: error.message }
    }
  })

  ipcMain.handle("save-file-dialog", async (event, tab) => {
    try {
      // Temporarily disable alwaysOnTop
      mainWindow.setAlwaysOnTop(false)
      const result = await dialog.showSaveDialog({
        title: "Save File",
        defaultPath: path.join(
          app.getPath("documents"),
          tab.name || "untitled.txt"
        ),
        filters: [
          { name: "Text Files", extensions: ["txt"] },
          { name: "All Files", extensions: ["*"] },
        ],
      })
      if (result.canceled) {
        mainWindow.setAlwaysOnTop(true)
        return { success: false, error: "Save was canceled" }
      } else {
        const filePath = result.filePath
        fs.writeFileSync(filePath, tab.content, "utf-8")
        mainWindow.setAlwaysOnTop(true)
        return { success: true, filePath }
      }
    } catch (error) {
      console.error("Main Process: Failed to save file:", error)
      return { success: false, error: error.message }
    }
  })
}
