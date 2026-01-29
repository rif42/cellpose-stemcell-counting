@echo off
title Cellpose Stem Cell Counting - Installer
color 0B

echo ========================================
echo   Cellpose Stem Cell Counting Installer
echo ========================================
echo.

:: Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Python not found. Installing via winget...
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to install Python.
        pause
        exit /b 1
    )
    echo       Python installed! Please restart this script.
    pause
    exit /b 0
)
echo       Python found!

:: Check if Git is installed
echo [2/4] Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo       Git not found. Installing via winget...
    winget install -e --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo       ERROR: Failed to install Git.
        pause
        exit /b 1
    )
    echo       Git installed! Please restart this script.
    pause
    exit /b 0
)
echo       Git found!

:: Set the installation directory
set "INSTALL_DIR=%USERPROFILE%\cellpose-stemcell-counting"

:: Clone or update the repository
echo [3/4] Setting up repository...
if exist "%INSTALL_DIR%" (
    echo       Directory exists. Pulling latest changes...
    cd /d "%INSTALL_DIR%"
    git pull
) else (
    git clone https://github.com/rif42/cellpose-stemcell-counting.git "%INSTALL_DIR%"
    cd /d "%INSTALL_DIR%"
)
echo       Repository ready at: %INSTALL_DIR%

:: Create virtual environment and install dependencies
echo [4/4] Installing dependencies (this may take several minutes)...
set "VENV_PATH=%INSTALL_DIR%\venv"
if not exist "%VENV_PATH%" (
    python -m venv "%VENV_PATH%"
    echo       Virtual environment created.
) else (
    echo       Virtual environment already exists.
)

:: Activate venv and install
call "%VENV_PATH%\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To run Cellpose GUI later, use:
echo   cd %INSTALL_DIR%
echo   venv\Scripts\activate.bat
echo   python -m cellpose
echo.

:: Ask if user wants to run cellpose now
set /p RUNNOW="Do you want to launch Cellpose now? (y/n): "
if /i "%RUNNOW%"=="y" (
    echo Launching Cellpose...
    python -m cellpose
)

pause
