#!/usr/bin/env bash
# Installation script for Google Photos Manager (Linux/macOS)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo "================================================"
echo "  Google Photos Manager - Installation Script"
echo "  Version 2.1.0"
echo "================================================"
echo

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

log_success "Python $PYTHON_VERSION detected"

# Check for virtual environment
log_info "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
log_success "Virtual environment activated"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_success "pip upgraded"

# Install core dependencies
log_info "Installing core dependencies..."
pip install -r requirements.txt
log_success "Core dependencies installed"

# Ask about mobile development
echo
read -p "Install mobile development dependencies (Kivy/Buildozer)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Installing mobile dependencies..."
    pip install kivy kivymd buildozer cython
    log_success "Mobile dependencies installed"

    # Check for Android build tools
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Checking Android build dependencies..."
        MISSING_DEPS=()

        if ! dpkg -s build-essential &> /dev/null; then MISSING_DEPS+=("build-essential"); fi
        if ! dpkg -s git &> /dev/null; then MISSING_DEPS+=("git"); fi
        if ! dpkg -s libsdl2-dev &> /dev/null; then MISSING_DEPS+=("libsdl2-dev"); fi
        if ! dpkg -s openjdk-17-jdk &> /dev/null; then MISSING_DEPS+=("openjdk-17-jdk"); fi

        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            log_warning "Missing Android build dependencies: ${MISSING_DEPS[*]}"
            echo
            read -p "Install missing dependencies with apt? (requires sudo) [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo apt-get update
                sudo apt-get install -y "${MISSING_DEPS[@]}"
                log_success "Android build dependencies installed"
            fi
        else
            log_success "All Android build dependencies present"
        fi
    fi
fi

# Ask about development tools
echo
read -p "Install development tools (testing, linting, etc.)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Installing development tools..."
    pip install -e ".[dev]"
    log_success "Development tools installed"

    # Set up pre-commit hooks
    log_info "Setting up pre-commit hooks..."
    pre-commit install
    log_success "Pre-commit hooks installed"
fi

# Create config directory
log_info "Creating configuration directory..."
CONFIG_DIR="$HOME/.photomanager"
mkdir -p "$CONFIG_DIR"
log_success "Configuration directory created at $CONFIG_DIR"

# Create PhotoLibrary directory
log_info "Setting up PhotoLibrary directory..."
PHOTO_DIR="$HOME/PhotoLibrary"
read -p "Create PhotoLibrary at $PHOTO_DIR? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    mkdir -p "$PHOTO_DIR"/{GoogleTakeout,"Photos & Videos",Review}
    log_success "PhotoLibrary structure created at $PHOTO_DIR"
fi

# Test imports
log_info "Testing imports..."
python3 << EOF
try:
    from PIL import Image
    import cv2
    import numpy as np
    print("${GREEN}✓${NC} All core imports successful")
except ImportError as e:
    print("${RED}✗${NC} Import error:", e)
    exit(1)
EOF

# Create desktop shortcut (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo
    read -p "Create desktop shortcut? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        DESKTOP_FILE="$HOME/.local/share/applications/photo-manager.desktop"
        CURRENT_DIR="$(pwd)"

        cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Version=1.0
Type=Application
Name=Photos Manager
Comment=Google Photos Takeout organizer
Exec=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/PhotoManager.py
Icon=$CURRENT_DIR/assets/icon.svg
Terminal=false
Categories=Graphics;Photography;Utility;
EOL

        chmod +x "$DESKTOP_FILE"
        log_success "Desktop shortcut created"
    fi
fi

# Final message
echo
echo "================================================"
log_success "Installation complete!"
echo "================================================"
echo
echo "To run the desktop application:"
echo "  source venv/bin/activate"
echo "  python PhotoManager.py"
echo
echo "To run the mobile application (desktop preview):"
echo "  source venv/bin/activate"
echo "  python PhotoManagerMobile.py"
echo
echo "To build Android APK:"
echo "  buildozer -v android debug"
echo
echo "For more information, see:"
echo "  - README.md"
echo "  - MOBILE_BUILD.md"
echo "  - CONTRIBUTING.md"
echo
log_info "Happy organizing! 📸"
