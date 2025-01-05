const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('coordinatePreview', {
  showPreview: (x, y) => ipcRenderer.send('show-coordinate-preview', { x, y }),
  hidePreview: () => ipcRenderer.send('hide-coordinate-preview')
});
