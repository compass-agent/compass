const { contextBridge, ipcRenderer } = require('electron');

// Expose specific APIs to the renderer process via the `window` object
//ipcRenderer.send: Sends messages from the renderer process to the main process.

contextBridge.exposeInMainWorld('electron', {
  closeWindow: () => ipcRenderer.send('close-window'),
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  toggleMaximizeWindow: () => ipcRenderer.send('maximize-window'), // Expose toggle function
});