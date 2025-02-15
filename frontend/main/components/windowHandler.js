const { ipcMain, screen } = require("electron");
const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 500,
  MIN_HEIGHT: 43,
  MINIMAL_HEIGHT: 43,
};
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

  const moveToCenter = () => {
    if (!mainWindow) return;
    
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
    const windowBounds = mainWindow.getBounds();
    
    // Calculate position to center the window both horizontally and vertically
    const x = Math.round((screenWidth - windowBounds.width) / 2);
    const y = Math.round((screenHeight - windowBounds.height) / 2);

    mainWindow.setBounds({
      x,
      y,
      width: windowBounds.width,
      height: windowBounds.height
    });
  };

  ipcMain.on("toggle-minimal-view", (_, isMinimal) => {
    if (!mainWindow) return;
    
    if (isMinimal) {
      // Store current bounds before minimizing
      previousBounds = mainWindow.getBounds();
      
      // Set minimal height and center the window
      mainWindow.setSize(previousBounds.width, WINDOW_CONFIG.MINIMAL_HEIGHT);
      moveToCenter();
    } else {
      // Restore original size and position
      if (previousBounds) {
        mainWindow.setBounds(previousBounds);
        previousBounds = null;
      } else {
        // Fallback if no previous bounds stored
        mainWindow.setSize(WINDOW_CONFIG.WIDTH, WINDOW_CONFIG.HEIGHT);
      }
    }
  });
};
