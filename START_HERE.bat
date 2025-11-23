@echo off
title Google Photos Manager
color 0A

echo.
echo  ===============================================
echo   GOOGLE PHOTOS MANAGER
echo   Easy Photo Organization for the Family!
echo  ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed!
    echo  Please install Python from python.org
    echo.
    pause
    exit /b 1
)

:: Check if Flask is installed, install if not
echo  Checking requirements...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo  Installing required packages...
    pip install flask pillow
)

echo.
echo  Starting the app...
echo  A browser window will open automatically.
echo.
echo  TO ACCESS FROM YOUR PHONE:
echo  1. Make sure your phone is on the same WiFi
echo  2. Look for the URL shown in the window
echo  3. Type that URL in your phone's browser
echo.
echo  Press Ctrl+C to stop when you're done.
echo  ===============================================
echo.

:: Run the web app
python "%~dp0PhotoManagerWeb.py"

pause
