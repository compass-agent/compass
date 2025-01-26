const { contextBridge, ipcRenderer } = require("electron");

// Expose specific APIs to the renderer process via the `window` object
//ipcRenderer.send: Sends messages from the renderer process to the main process.

contextBridge.exposeInMainWorld("electron", {
  platform: process.platform,
  ipcRenderer: {
    send: (channel, data) => {
      const validChannels = [
        "toggle-fullscreen",
        "move-to-bottom-right",
        "close-window",
        "minimize-window",
        "maximize-window",
        "show-coordinate-preview",
        "hide-coordinate-preview",
        "open-template-training",
        "open-file-editor",
        "save-file-content",
        "close-editor-window",
        "run-command", // Allow sending commands to run in the terminal
      ];
      if (validChannels.includes(channel)) {
        if (channel !== "toggle-fullscreen" && channel !== "move-to-bottom-right") {
          ipcRenderer.send(channel, data);
        }
      }
    },
    on: (channel, func) => {
      const validChannels = ["move-to-bottom-right-done", "load-file-content", "save-file-success", "command-output"];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args));
      }
    },
    invoke: (channel, data) => {
      const validChannels = ['open-file-dialog', 'save-file', 'read-file', 'save-file-dialog'];
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, data);
      }
    },
    removeListener: (channel, func) => {
      const validChannels = ["move-to-bottom-right-done", "load-file-content", "save-file-success"];
      if (validChannels.includes(channel)) {
        ipcRenderer.removeListener(channel, func);
      }
    },
  },
  restoreWindow: () => ipcRenderer.send("restore-window"),
  closeWindow: () => ipcRenderer.send("close-window"),
  minimizeWindow: () => ipcRenderer.send("minimize-window"),
  toggleMaximizeWindow: () => ipcRenderer.send("maximize-window"), // Expose toggle function
  templateTraining: {
    saveTemplate: (data) => ipcRenderer.send('save-template', data),
    onTemplateSaved: (callback) => ipcRenderer.on('template-saved', callback),
  },
  terminal: {
    runCommand: (command) => ipcRenderer.send("run-command", command), // Send a command to run
    onCommandOutput: (callback) => ipcRenderer.on("command-output", (event, data) => callback(data)), // Listen for command outputs
    removeCommandOutputListener: (callback) =>
      ipcRenderer.removeListener("command-output", callback), // remove a previously added listener for command-output events.
  }
});

// Add coordinate preview API
contextBridge.exposeInMainWorld('coordinatePreview', {
  showPreview: (x, y) => ipcRenderer.send('show-coordinate-preview', { x, y }),
  hidePreview: () => ipcRenderer.send('hide-coordinate-preview')
});
