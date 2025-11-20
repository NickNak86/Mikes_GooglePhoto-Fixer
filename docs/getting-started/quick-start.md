# Quick Start Guide

Get up and running with Google Photos Manager in just a few minutes!

## Prerequisites

Before you begin, ensure you have:

- [x] Python 3.9 or higher installed
- [x] Google Takeout ZIP file or extracted folder
- [x] ~2GB free disk space (more for large photo libraries)

## Installation

=== "Linux/macOS"

    ```bash
    # Clone the repository
    git clone https://github.com/NickNak86/Mikes_GooglePhoto-Fixer.git
    cd Mikes_GooglePhoto-Fixer

    # Run installation script
    chmod +x install.sh
    ./install.sh
    ```

=== "Windows"

    ```powershell
    # Clone the repository
    git clone https://github.com/NickNak86/Mikes_GooglePhoto-Fixer.git
    cd Mikes_GooglePhoto-Fixer

    # Run installation script
    powershell -ExecutionPolicy Bypass -File install.ps1
    ```

=== "Manual"

    ```bash
    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

    # For mobile development
    pip install kivy kivymd buildozer
    ```

## First Run - Desktop

1. **Launch the application:**

    ```bash
    python PhotoManager.py
    ```

2. **Configure paths:**
    - Base Path: Where your photo library will be stored (default: `~/PhotoLibrary`)
    - ExifTool Path: Location of exiftool binary (or just `exiftool` if in PATH)

3. **Set processing options:**
    - Worker Threads: Number of parallel workers (default: 4)
    - Blur Threshold: Sensitivity for blur detection (default: 100.0)
    - Size Threshold: Minimum file size in MB (default: 0.5)

4. **Select Google Takeout:**
    - Click "Select Takeout" and choose your Google Takeout ZIP or folder
    - The tool will automatically extract ZIPs if needed

5. **Start Processing:**
    - Click "Process Takeout" and monitor progress
    - Processing time varies: ~2-5 minutes per 1,000 photos

## First Run - Mobile (Android)

!!! info "Building APK"
    First, build the Android APK following the [Mobile Building Guide](../mobile/building.md)

1. **Install APK on Android device:**
    ```bash
    adb install bin/PhotosManager-2.1.0-arm64-v8a-debug.apk
    ```

2. **Grant permissions:**
    - Storage: Allow access to photos and files
    - (Optional) Camera: For future camera integration

3. **Transfer Google Takeout:**
    - Copy Takeout to: `/sdcard/PhotoLibrary/GoogleTakeout/`
    - You can use file manager apps or ADB:
      ```bash
      adb push takeout.zip /sdcard/PhotoLibrary/GoogleTakeout/
      ```

4. **Process photos:**
    - Open app and tap "Process New Takeout"
    - Review progress and wait for completion

5. **Review flagged items:**
    - Tap "Review Flagged Photos"
    - Swipe through photo groups
    - Choose: Keep Best, Skip, or Delete All

## Understanding the Output

After processing, your library will be organized as:

```
PhotoLibrary/
├── GoogleTakeout/          # Your original Takeout files (preserved)
├── Photos & Videos/        # Organized output
│   ├── 2024/
│   │   ├── 01-January/
│   │   ├── 02-February/
│   │   └── ...
│   └── 2023/
│       └── ...
└── Review/                 # Items needing review
    ├── Duplicates/
    ├── Blurry/
    ├── TooSmall/
    └── Bursts/
```

## Review Process

### Desktop Review Interface

1. **Launch review interface:**
    ```bash
    python ReviewInterface.py
    ```

2. **Review each group:**
    - Duplicates: Choose which copies to keep
    - Blurry: Decide if photo is salvageable
    - Bursts: Select best shots from sequence
    - Too Small: Keep or discard small files

3. **Apply decisions:**
    - Click "Apply Decisions" to execute changes
    - Original files in GoogleTakeout remain untouched

### Mobile Review

1. Tap "Review Flagged Photos"
2. View photo group with thumbnails
3. Choose action:
    - **Keep Best**: Keeps highest quality photo from group
    - **Skip**: Leave group for later review
    - **Delete All**: Remove all photos in group
4. Decisions apply immediately

## Common First-Time Tasks

### Task 1: Process First Takeout

=== "Desktop"
    1. Open PhotoManager
    2. Select Takeout folder
    3. Click "Process Takeout"
    4. Wait for completion (~5-10 min for 2,000 photos)
    5. Review statistics in completion dialog

=== "Mobile"
    1. Transfer Takeout to device
    2. Open Photos Manager app
    3. Tap "Process New Takeout"
    4. Monitor progress bar
    5. View completion summary

### Task 2: Handle Duplicates

1. Navigate to Review → Duplicates
2. Compare photos in each group
3. Select best quality version:
    - Highest resolution
    - Sharpest image
    - Best composition
4. Mark others for deletion
5. Apply decisions

### Task 3: Manage Burst Photos

1. Review burst photo groups
2. Identify best shots from sequence
3. Consider keeping:
    - Best facial expressions
    - Sharpest focus
    - Best composition
4. Delete redundant photos
5. Apply changes

## Performance Tips

!!! tip "Optimize Processing Speed"
    - **Desktop**: Use 4-8 worker threads on modern CPUs
    - **Mobile**: Stick to 2 threads to preserve battery
    - **Large Libraries**: Process in batches (e.g., one year at a time)
    - **Storage**: Use SSD for faster I/O

!!! warning "Memory Considerations"
    - **Large files**: Close other applications during processing
    - **Mobile**: Ensure 2GB+ free RAM
    - **Swap**: Consider increasing swap space for very large libraries

## Troubleshooting

### Installation Issues

??? question "ImportError: No module named 'PIL'"
    Install Pillow:
    ```bash
    pip install Pillow
    ```

??? question "OpenCV import fails"
    Install opencv-python:
    ```bash
    pip install opencv-python
    ```

### Processing Issues

??? question "Application hangs during processing"
    - Reduce worker threads
    - Check available RAM
    - Ensure storage has sufficient space

??? question "Photos not found in Takeout"
    - Verify Takeout structure: `Takeout/Google Photos/`
    - Check ZIP extraction completed successfully
    - Ensure proper permissions

### Mobile Issues

??? question "App crashes on Android"
    Check logs:
    ```bash
    adb logcat | grep python
    ```

??? question "Storage permission denied"
    1. Go to Settings → Apps → Photos Manager
    2. Grant Storage permissions
    3. Restart app

## Next Steps

Now that you're set up, explore:

- [Processing Guide](../user-guide/processing.md) - Detailed processing options
- [Review Interface](../user-guide/review.md) - Master the review workflow
- [Best Practices](../user-guide/best-practices.md) - Tips for optimal results
- [Mobile Development](../mobile/architecture.md) - Build and customize the Android app

## Getting Help

Need assistance?

- 📖 [FAQ](../faq.md) - Common questions answered
- 🐛 [Report Issues](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
- 💬 [Discussions](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions)
- 📧 Check documentation for detailed guides

---

!!! success "You're all set!"
    Start processing your first Google Takeout and enjoy organized photos! 📸
