const { contextBridge, ipcRenderer } = require('electron');

// Expose specific APIs to the renderer process via the `window` object
//ipcRenderer.send: Sends messages from the renderer process to the main process.

contextBridge.exposeInMainWorld('electron', {
  platform: process.platform,
  ipcRenderer: {
    send: (channel, ...args) => {
      const validChannels = ["toggle-fullscreen", "close-window", "minimize-window", "maximize-window", "move-to-bottom-right"];
      if (validChannels.includes(channel)) {
        ipcRenderer.send(channel, ...args);
      }
    },
    on: (channel, func) => {
      const validChannels = ["some-event"];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args));
      }
    },
  },
  restoreWindow: () => ipcRenderer.send('restore-window'),
  closeWindow: () => ipcRenderer.send('close-window'),
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  toggleMaximizeWindow: () => ipcRenderer.send('maximize-window'), // Expose toggle function
});