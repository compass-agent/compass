// Configuration script to handle Python backend bundling during Electron build process
const path = require('path');
const fs = require('fs');

module.exports = {
  afterPack: async (context) => {
    // Log what we're doing
    console.log('Copying backend executable...');
    console.log('Source:', path.join('backend', 'dist', 'compass-backend.exe'));
    console.log('Destination:', path.join(context.appOutDir, 'resources', 'backend'));
    
    const backendExe = path.join('backend', 'dist', 'compass-backend.exe');
    const destPath = path.join(context.appOutDir, 'resources', 'backend');
    
    if (!fs.existsSync(backendExe)) {
      throw new Error(`Backend executable not found at ${backendExe}`);
    }
    
    if (!fs.existsSync(destPath)) {
      fs.mkdirSync(destPath, { recursive: true });
    }
    
    fs.copyFileSync(backendExe, path.join(destPath, 'compass-backend.exe'));
    console.log('Backend executable copied successfully');
  }
}; 