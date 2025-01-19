const { contextBridge, ipcRenderer } = require("electron");

// Expose specific APIs to the renderer process via the `window` object
//ipcRenderer.send: Sends messages from the renderer process to the main process.

contextBridge.exposeInMainWorld("electron", {
  platform: process.platform,
  ipcRenderer: {
    send: (channel, ...args) => {
      const validChannels = [
        "toggle-fullscreen",
        "close-window",
        "minimize-window",
        "maximize-window",
        "move-to-bottom-right",
        "show-coordinate-preview",
        "hide-coordinate-preview",
        "open-file-editor",
        "save-file-content",
        "close-editor-window",
      ];
      if (validChannels.includes(channel)) {
        ipcRenderer.send(channel, ...args);
      }
    },
    on: (channel, func) => {
      const validChannels = ["move-to-bottom-right-done", "load-file-content", "save-file-success"];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args));
      }
    },
    invoke: (channel, data) => {
      const validChannels = ['open-file-dialog', 'save-file', 'save-file-dialog'];
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
  toggleMaximizeWindow: () => ipcRenderer.send("maximize-window"),
});

// Add coordinate preview API
contextBridge.exposeInMainWorld('coordinatePreview', {
  showPreview: (x, y) => ipcRenderer.send('show-coordinate-preview', { x, y }),
  hidePreview: () => ipcRenderer.send('hide-coordinate-preview')
});
