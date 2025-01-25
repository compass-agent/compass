
const { ipcMain, screen } = require('electron');

module.exports = (mainWindow) => {
let previousBounds = null; // To store the previous window bounds
// Comment out the handlers but keep them for reference
ipcMain.on("toggle-fullscreen", (_, isFullscreen) => {
  // if (!mainWindow) return;
  // if (isFullscreen) {
  //   if (previousBounds) {
  //     mainWindow.setBounds(previousBounds);
  //   } else {
  //     mainWindow.setBounds({
  //       y: mainWindow.getBounds().y,
  //       height: WINDOW_CONFIG.HEIGHT,
  //     });
  //   }
  //   previousBounds = null;
  // } else {
  //   previousBounds = mainWindow.getBounds();
  //   mainWindow.setBounds({
  //     y: mainWindow.getBounds().y,
  //     height: WINDOW_CONFIG.MIN_HEIGHT,
  //   });
  // }
});

ipcMain.on("move-to-bottom-right", () => {
  // if (!mainWindow) return;
  // const { width, height } = require("electron").screen.getPrimaryDisplay().workAreaSize;
  // mainWindow.setBounds({
  //   x: width - mainWindow.getBounds().width,
  //   y: height - mainWindow.getBounds().height,
  // });
  // mainWindow.webContents.send("move-to-bottom-right-done");
});

ipcMain.on("close-window", () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.on("minimize-window", () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on("restore-window", (event) => {
  if (mainWindow) {
    mainWindow.restore();
  }
});

ipcMain.on("maximize-window", () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.restore(); // Restore to the previous size
    } else {
      console.log("Main Process: Maximizing the window...");
      mainWindow.maximize();
    }
  }
});
}