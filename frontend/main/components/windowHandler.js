const { ipcMain, screen } = require("electron");
const WINDOW_CONFIG = {
  WIDTH: 500,
  HEIGHT: 553,
  MIN_WIDTH: 300,
  MIN_HEIGHT: 45,
  MINIMAL_HEIGHT: 45,
};
module.exports = (mainWindow) => {
  let previousBounds = null; // To store the previous window bounds
  // Comment out the handlers but keep them for reference
  ipcMain.on("toggle-fullscreen", (_, isFullscreen) => {
    if (!mainWindow) return;
    if (isFullscreen) {
      if (previousBounds) {
        mainWindow.setBounds(previousBounds);
      } else {
        mainWindow.setBounds({
          y: mainWindow.getBounds().y,
          height: WINDOW_CONFIG.HEIGHT,
        });
      }
      previousBounds = null;
    } else {
      previousBounds = mainWindow.getBounds();
      mainWindow.setBounds({
        y: mainWindow.getBounds().y,
        height: WINDOW_CONFIG.MIN_HEIGHT,
      });
    }
  });

  ipcMain.on("move-to-bottom-right", () => {
    if (!mainWindow) return;
    const { width, height } =
      require("electron").screen.getPrimaryDisplay().workAreaSize;
    mainWindow.setBounds({
      x: width - mainWindow.getBounds().width,
      y: height - mainWindow.getBounds().height,
    });
    mainWindow.webContents.send("move-to-bottom-right-done");
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

  const moveToVerticalInputPosition = () => {
    if (!mainWindow) return;

    const { width: screenWidth, height: screenHeight } =
      screen.getPrimaryDisplay().workAreaSize;
    const windowBounds = mainWindow.getBounds();

    // Keep original x position
    const x = windowBounds.x;

    // Calculate reduced width (30% of original width)
    const reducedWidth = Math.floor(windowBounds.width * 0.3);

    // Calculate the y position where the input box was
    const previousBottom = windowBounds.y + windowBounds.height;
    const newY = previousBottom - WINDOW_CONFIG.MINIMAL_HEIGHT;

    // Add 500px offset toward bottom
    const offsetY = newY + 500;

    // Ensure window stays within screen bounds
    const adjustedY = Math.min(
      Math.max(0, offsetY),
      screenHeight - WINDOW_CONFIG.MINIMAL_HEIGHT
    );

    // Set both size and position in one call to avoid flickering
    mainWindow.setBounds({
      x: x, // Keep original x position
      y: adjustedY,
      width: reducedWidth, // Use 30% of original width
      height: WINDOW_CONFIG.MINIMAL_HEIGHT,
    });
  };

  ipcMain.on("toggle-minimal-view", (_, isMinimal) => {
    if (!mainWindow) return;

    if (isMinimal) {
      // Store current bounds before minimizing
      previousBounds = mainWindow.getBounds();

      // Set minimal height while maintaining x position and calculating y position
      mainWindow.setSize(previousBounds.width, WINDOW_CONFIG.MINIMAL_HEIGHT);
      moveToVerticalInputPosition();
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
