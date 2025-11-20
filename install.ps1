# Installation script for Google Photos Manager (Windows PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [switch]$Mobile,
    [switch]$Dev,
    [switch]$NoPrompt
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Blue }
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "✗ $args" -ForegroundColor Red }

# Banner
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Google Photos Manager - Installation Script" -ForegroundColor Cyan
Write-Host "  Version 2.1.0" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Info "Checking Python version..."
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }

    $versionMatch = $pythonVersion -match "Python (\d+\.\d+)"
    if ($versionMatch) {
        $version = [version]$matches[1]
        $requiredVersion = [version]"3.9"

        if ($version -lt $requiredVersion) {
            Write-Error "Python 3.9 or higher is required. Found: $version"
            exit 1
        }

        Write-Success "Python $version detected"
    }
}
catch {
    Write-Error "Python 3 is not installed. Please install Python 3.9 or higher from python.org"
    exit 1
}

# Check if virtual environment exists
Write-Info "Setting up virtual environment..."
if (Test-Path "venv") {
    Write-Warning "Virtual environment already exists"
}
else {
    python -m venv venv
    Write-Success "Virtual environment created"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"

# Upgrade pip
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel --quiet
Write-Success "pip upgraded"

# Install core dependencies
Write-Info "Installing core dependencies..."
pip install -r requirements.txt
Write-Success "Core dependencies installed"

# Ask about mobile development
if (-not $NoPrompt) {
    Write-Host ""
    $installMobile = Read-Host "Install mobile development dependencies (Kivy/Buildozer)? [y/N]"
    $Mobile = $installMobile -match "^[Yy]$"
}

if ($Mobile) {
    Write-Info "Installing mobile dependencies..."
    pip install kivy kivymd buildozer cython
    Write-Success "Mobile dependencies installed"

    Write-Warning "Note: Buildozer works best on Linux/WSL."
    Write-Warning "For Android builds on Windows, use WSL (Windows Subsystem for Linux)."
}

# Ask about development tools
if (-not $NoPrompt) {
    Write-Host ""
    $installDev = Read-Host "Install development tools (testing, linting, etc.)? [y/N]"
    $Dev = $installDev -match "^[Yy]$"
}

if ($Dev) {
    Write-Info "Installing development tools..."
    pip install -e ".[dev]"
    Write-Success "Development tools installed"

    # Set up pre-commit hooks
    Write-Info "Setting up pre-commit hooks..."
    pre-commit install
    Write-Success "Pre-commit hooks installed"
}

# Create config directory
Write-Info "Creating configuration directory..."
$configDir = Join-Path $env:USERPROFILE ".photomanager"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Write-Success "Configuration directory created at $configDir"
}
else {
    Write-Success "Configuration directory exists at $configDir"
}

# Create PhotoLibrary directory
Write-Info "Setting up PhotoLibrary directory..."
$photoDir = Join-Path $env:USERPROFILE "PhotoLibrary"

if (-not $NoPrompt) {
    $createPhotoDir = Read-Host "Create PhotoLibrary at $photoDir? [Y/n]"
    $shouldCreate = $createPhotoDir -notmatch "^[Nn]$"
}
else {
    $shouldCreate = $true
}

if ($shouldCreate) {
    New-Item -ItemType Directory -Path "$photoDir\GoogleTakeout" -Force | Out-Null
    New-Item -ItemType Directory -Path "$photoDir\Photos & Videos" -Force | Out-Null
    New-Item -ItemType Directory -Path "$photoDir\Review" -Force | Out-Null
    Write-Success "PhotoLibrary structure created at $photoDir"
}

# Test imports
Write-Info "Testing imports..."
try {
    python -c "from PIL import Image; import cv2; import numpy as np"
    Write-Success "All core imports successful"
}
catch {
    Write-Error "Import test failed. Please check your installation."
    exit 1
}

# Create desktop shortcut
if (-not $NoPrompt) {
    Write-Host ""
    $createShortcut = Read-Host "Create desktop shortcut? [y/N]"

    if ($createShortcut -match "^[Yy]$") {
        Write-Info "Creating desktop shortcut..."

        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "Photos Manager.lnk"
        $targetPath = Join-Path (Get-Location) "venv\Scripts\pythonw.exe"
        $arguments = """$(Join-Path (Get-Location) "PhotoManager.py")"""
        $iconPath = Join-Path (Get-Location) "assets\icon.svg"

        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $targetPath
        $Shortcut.Arguments = $arguments
        $Shortcut.WorkingDirectory = Get-Location
        $Shortcut.Description = "Google Photos Manager"
        if (Test-Path $iconPath) {
            $Shortcut.IconLocation = $iconPath
        }
        $Shortcut.Save()

        Write-Success "Desktop shortcut created"
    }
}

# Final message
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Success "Installation complete!"
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the desktop application:"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python PhotoManager.py"
Write-Host ""
Write-Host "To run the mobile application (desktop preview):"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python PhotoManagerMobile.py"
Write-Host ""

if ($Mobile) {
    Write-Host "To build Android APK (use WSL):"
    Write-Host "  wsl"
    Write-Host "  cd /mnt/c/[path-to-project]"
    Write-Host "  buildozer -v android debug"
    Write-Host ""
}

Write-Host "For more information, see:"
Write-Host "  - README.md"
Write-Host "  - MOBILE_BUILD.md"
Write-Host "  - CONTRIBUTING.md"
Write-Host ""
Write-Info "Happy organizing! 📸"
Write-Host ""

# Pause if run directly (not from script)
if (-not $NoPrompt) {
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
