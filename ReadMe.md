# COMPASS DEVELOPMENT GUIDE

This guide will help you set up and run the Compass development environment.

## PREREQUISITES
- Node.js and npm (Node Package Manager)
- Python 3.11 or higher
- Git

## INITIAL SETUP
1. Clone the repository:
   ```bash
   git clone https://github.com/mohammadkazem-sadoughi/compass.git
   cd compass
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Set up Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # This works on MacOS/Linux
   venv\Scripts\activate     # This works on Windows
   pip install -r requirements.txt
   cd ..
   ```

## DEVELOPMENT ENVIRONMENT
The project consists of two main parts that need to run simultaneously:
1. Frontend (Electron/React)
2. Backend (Python/Flask)

To start the development environment:

1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate  # This works on MacOS/Linux
   venv\Scripts\activate     # This works on Windows
   python src/compass/app.py
   If Python can not locate the modules, run the following commands:
   $env:PYTHONPATH = "src"; python src/compass/app.py  # For Windows PowerShell (including IDE(Cursor) terminal)
   PYTHONPATH=src python src/compass/app.py  # For macOS/Linux
   set PYTHONPATH=src && python src/compass/app.py  # For Windows Command Prompt
   ```

2. In a new terminal, start the frontend:

   In one terminal you need to first:
   ```bash
   npm run watch
   ```

   Then in another terminal:
   ```bash
   npm run dev
   ```
The reason for running `npm run watch` first is because it will watch for changes in the React code and automatically rebuild the application.

The above commands will concurrently run:
- React build watcher (for hot reloading)
- Electron application

## USEFUL COMMANDS
- Start development environment:
  ```bash
  npm run dev
  ```

- Watch for React changes only:
  ```bash
  npm run watch
  ```

- Run Electron app only:
  ```bash
  npm start
  ```

- Package the application:
  ```bash
  npm run package-win
  ```

- Build the backend executable:
  ```bash
  cd backend
  build_app.bat
  ```

- IDE(Cursor) Tasks (access via `Terminal > Run Task` in the top menu, or press Ctrl+Shift+P and type "Tasks: Run Task"):
  - `Start Development Environment` - Runs both backend and frontend
  - `Build Backend Executable` - Builds the Python backend
  - `Package Electron App` - Packages the Electron app
  - `Full Build and Package` - Complete build process

- Kill running instances (macOS/Linux):
  ```bash
  ps aux | grep -i Compass | awk '{print $2}' | xargs kill -9
  ```

## PROJECT STRUCTURE
```
/src
  /main          - Electron main process
  /renderer      - React frontend code
  /services      - Shared services
/backend         - Python Flask backend
  /services      - Backend services
  /venv          - Python virtual environment
```

## CONTRIBUTING
1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. Push to your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

## Running the Backend Server

### Windows (Optimized Performance)
For better performance on Windows systems, run the backend server using:
```powershell
cd backend
$env:EVENTLET_NO_GREENDNS="yes"; $env:EVENTLET_THREADPOOL_SIZE="20"; $env:EVENTLET_WEBSOCKET="false"; $env:PYTHONPATH="src"; ./venv/Scripts/python.exe src/compass/app.py
```

This command includes optimizations for Windows systems to improve startup time and overall performance.

## BUILDING THE EXECUTABLE AND PACKAGING

There are two ways to build and package the application:

### Option 1: Using IDE(Cursor) Tasks

1. Open the project in IDE(Cursor)
2. Access tasks in one of these ways:
   - **Method A**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) to open the Command Palette, then type "Tasks: Run Task" and select it
   - **Method B**: Click on `Terminal` in the top menu bar, then select `Run Task` from the dropdown menu
   - **Method C**: Press `Alt` key to show the top menu if it's hidden, then navigate to `Terminal > Run Task`

3. Choose one of the following tasks:
   - `Build Backend Executable` - Builds only the Python backend
   - `Package Electron App` - Packages only the Electron frontend

### Option 2: Using the Command Line

1. Build the backend executable:
   ```bash
   cd backend
   build_app.bat
   ```
   This will create the `compass_backend.exe` file in the appropriate directory.

2. Package the entire application for Windows:
   ```bash
   cd ..
   npm run package-win
   ```

Note: node >= 16
   
The build process will:
1. Build the backend executable using PyInstaller
2. Package the Electron application with the backend executable included
3. Create an installer in the `dist` folder

The final packaged application will include all necessary dependencies and can be distributed to users.




