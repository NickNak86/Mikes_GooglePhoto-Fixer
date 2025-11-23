@echo off
title Google Photos Manager - Web/Phone Edition
color 0B

echo.
echo  ===============================================
echo   GOOGLE PHOTOS MANAGER - WEB EDITION
echo   Access from your phone!
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
    echo  Installing Flask...
    pip install flask pillow
)

echo.
echo  Starting the web server...
echo.
echo  ===============================================
echo  TO ACCESS FROM YOUR PHONE:
echo  1. Make sure your phone is on the same WiFi
echo  2. Look for the URL shown below
echo  3. Type that URL in your phone's browser
echo  ===============================================
echo.

python "%~dp0PhotoManagerWeb.py"

pause
