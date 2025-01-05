const { BrowserWindow } = require('electron');
const path = require('path');

let previewWindow = null;

function createPreviewWindow() {
  previewWindow = new BrowserWindow({
    width: 40,
    height: 40,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    focusable: false,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: true
    }
  });

  const previewPath = path.join(__dirname, '../renderer/components/preview/preview.html');
  previewWindow.loadFile(previewPath);
}

function handleCoordinatePreview(ipcMain) {
  ipcMain.on('show-coordinate-preview', (event, { x, y }) => {
    if (!previewWindow) {
      createPreviewWindow();
    }
    previewWindow.setPosition(x - 20, y - 20);
    previewWindow.show();
  });

  ipcMain.on('hide-coordinate-preview', () => {
    if (previewWindow) {
      previewWindow.hide();
    }
  });
}

module.exports = { handleCoordinatePreview }; 