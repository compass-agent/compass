const { spawn } = require('child_process');
const path = require('path');
const { app } = require('electron');
const isDev = process.env.NODE_ENV === 'development';
const fs = require('fs');

// Set up error logging with proper directory creation
const logDir = path.join(app.getPath('userData') || __dirname);
const logPath = path.join(logDir, 'compass_backend.log');

// Ensure log directory exists
try {
    if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
    }
} catch (error) {
    console.error('Failed to create log directory:', error);
}

function logToFile(message) {
    try {
        // Log to console as well for debugging
        console.log(message);
        fs.appendFileSync(logPath, `${new Date().toISOString()}: ${message}\n`);
    } catch (error) {
        console.error('Failed to write to log file:', error);
    }
}

/**
 * Manages the Python backend process for the Compass application
 * Handles both development and production environments
 * @returns {ChildProcess} The spawned backend process
 */
function startBackend() {
    let backendPath;
    let backendProcess;

    // Log environment variables for debugging
    logToFile('Environment variables:');
    logToFile(`NODE_ENV: ${process.env.NODE_ENV}`);
    // logToFile(`BACKEND_HOST: ${process.env.BACKEND_HOST}`);
    // logToFile(`BACKEND_PORT: ${process.env.BACKEND_PORT}`);
    
    // Additional app path logging for debugging
    logToFile(`App path: ${app.getAppPath()}`);
    logToFile(`User data path: ${app.getPath('userData')}`);
    logToFile(`Executable path: ${app.getPath('exe')}`);

    try {
            // In production, use the bundled executable
            // Try multiple possible locations for the backend executable
            logToFile('Checking possible backend executable locations:');
            // Try to get the resources path more reliably
            let resourcesPath;
            try {
                resourcesPath = app.getPath('resources');
                logToFile(`Resources path retrieved: ${resourcesPath}`);
            } catch (error) {
                // Fallback: construct the path based on the app path
                resourcesPath = path.join(app.getAppPath(), '..', '..');
                if (app.getAppPath().includes('app.asar')) {
                    resourcesPath = path.join(app.getAppPath(), '..');
                }
                logToFile(`Using fallback resources path: ${resourcesPath}`);
            }
            
            const possibleLocations = [
                // Standard location in resources
                path.join(resourcesPath, 'backend', 'compass_backend.exe'),
                // Direct path in resources folder
                path.join(resourcesPath, 'compass_backend.exe'),
                // Try app.asar location
                path.join(resourcesPath, 'app.asar', 'resources', 'backend', 'compass_backend.exe'),
                // Fallback to original location
                path.join(resourcesPath, 'backend', 'compass_backend.exe'),
                // Add the exact path from the screenshot
                path.join(app.getPath('exe'), '..', 'resources', 'backend', 'compass_backend.exe'),
                // Check in dist structure
                path.join(process.cwd(), 'dist', 'win-unpacked', 'resources', 'backend', 'compass_backend.exe')
            ];
            
            // Log all locations we're checking
            possibleLocations.forEach(loc => {
                logToFile(`- ${loc}`);
            });
            
            // Log additional potential paths
            logToFile(`Checking additional potential executable paths:`);
            logToFile(`- Relative to exe: ${path.join(app.getPath('exe'), '..', 'resources', 'backend', 'compass_backend.exe')}`);
            logToFile(`- Current working directory: ${process.cwd()}`);
            logToFile(`- From cwd to dist: ${path.join(process.cwd(), 'dist', 'win-unpacked', 'resources', 'backend', 'compass_backend.exe')}`);
            
            // Find the first location that exists
            backendPath = possibleLocations.find(loc => {
                const exists = fs.existsSync(loc);
                logToFile(`Checking ${loc}: ${exists ? 'EXISTS' : 'NOT FOUND'}`);
                return exists;
            });
            
            if (!backendPath) {
                const errorMsg = `Backend executable not found in any of the expected locations`;
                console.error(errorMsg);
                logToFile(errorMsg);
                throw new Error(errorMsg);
            }
            
            console.log('Production backend path:', backendPath);
            logToFile(`Using backend at: ${backendPath}`);
            
            backendProcess = spawn(backendPath, [], {
                windowsHide: true,  // Prevent command window from showing
                env: {
                    ...process.env,
                    PYTHONUNBUFFERED: '1',  // Ensure Python output isn't buffered
                    COMPASS_ENV: process.env.NODE_ENV || 'production' // Pass environment type
                }
            });

        // Handle backend output
        backendProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`Backend: ${output}`);
            logToFile(`Backend output: ${output}`);
        });

        // Handle backend errors
        backendProcess.stderr.on('data', (data) => {
            const errorOutput = data.toString();
            console.error(`Backend Error: ${errorOutput}`);
            logToFile(`Backend error: ${errorOutput}`);
        });

        backendProcess.on('exit', (code, signal) => {
            logToFile(`Backend process exited with code ${code} and signal ${signal}`);
        });

        return backendProcess;

    } catch (error) {
        console.error('Error in startBackend:', error);
        logToFile(`Error in startBackend: ${error.message}\n${error.stack}`);
        throw error;
    }
}

module.exports = { startBackend, logToFile };