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
   $env:PYTHONPATH = "src"; python src/compass/app.py  # For Windows PowerShell (including VS Code terminal)
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
  npm run package
  ```

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
