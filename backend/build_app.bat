@echo off
REM Build script for compass_backend

echo ===== Building compass_backend =====

REM Stop any running instances of compass_backend.exe
echo Stopping any running instances of compass_backend.exe...
taskkill /F /IM compass_backend.exe 2>nul
REM Wait a moment to ensure process is fully terminated
timeout /t 2 /nobreak >nul

REM Clean up previous builds
echo Cleaning up previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__
REM Don't delete the spec file as we've modified it
if exist "*.pyc" del /s /q *.pyc

REM Clean up Python cache directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo Previous builds cleaned up

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Clear pip cache to ensure clean dependencies
pip cache purge

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Install required packages
echo Installing required packages...
pip install --no-cache-dir -r requirements.txt

REM Set PYTHONPATH to include the src directory
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Build the executable
echo Building executable...
pyinstaller --clean --noconfirm --log-level DEBUG compass_backend.spec

echo ===== Build complete =====
echo Executable created at: dist\compass_backend\compass_backend.exe

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat 