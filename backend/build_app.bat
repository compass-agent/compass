@echo off
REM Build script for the Compass Python backend (PyInstaller onedir bundle).
REM Prefer running from the repo root via:  npm run build:backend
REM This script is the standalone equivalent.

echo ===== Building Compass Backend =====

REM Stop any running instances of the backend.
taskkill /F /IM "Compass Backend.exe" 2>nul
taskkill /F /IM compass_backend.exe 2>nul
timeout /t 2 /nobreak >nul

REM Run PyInstaller from the repo root using the shared .venv
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv not found. Run "npm run setup:backend" first.
    exit /b 1
)

.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm backend\compass_backend.spec --distpath backend\dist --workpath backend\build

echo ===== Build complete =====
echo Bundle created at: backend\dist\Compass Backend\Compass Backend.exe
