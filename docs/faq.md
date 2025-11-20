# Frequently Asked Questions

Common questions about Google Photos Manager, answered.

## General

??? question "What is Google Photos Manager?"
    Google Photos Manager is an intelligent tool for organizing, deduplicating, and managing Google Photos Takeout archives. It automatically detects duplicates, blurry photos, burst sequences, and small files, helping you clean up and organize your photo library efficiently.

??? question "Is it free?"
    Yes! Google Photos Manager is completely free and open-source under the MIT License. You can use it, modify it, and distribute it freely.

??? question "Does it work offline?"
    Yes! All processing happens locally on your device. No internet connection is required once you've downloaded the tool and your Google Takeout.

??? question "Will it delete my original photos?"
    No! The original Google Takeout files are never modified. All processing creates organized copies, and flagged items are moved to a Review folder for your manual inspection before any deletions.

## Installation & Setup

??? question "What are the system requirements?"
    **Desktop:**

    - Python 3.9 or higher
    - 2GB RAM minimum (4GB+ recommended)
    - ~2GB free disk space plus your photo library size
    - Windows 10+, macOS 10.14+, or modern Linux

    **Mobile (Android):**

    - Android 5.0 (API 21) or higher
    - 2GB RAM minimum
    - Storage space for your photo library

??? question "Do I need ExifTool?"
    ExifTool is optional but recommended for advanced metadata handling. The app will work without it, but you'll get better results (especially with dates and locations) if it's installed.

    - **Linux**: `sudo apt-get install exiftool`
    - **macOS**: `brew install exiftool`
    - **Windows**: Download from [exiftool.org](https://exiftool.org/)

??? question "Can I run this in the cloud?"
    Yes! You can run it on cloud VMs (AWS, Google Cloud, Azure) or use Docker. See the [Docker Guide](development/setup.md#docker-setup) for details.

## Usage

??? question "How long does processing take?"
    Processing time depends on your library size and hardware:

    - **Small** (1,000 photos): 2-5 minutes
    - **Medium** (10,000 photos): 15-30 minutes
    - **Large** (50,000 photos): 1-3 hours
    - **Very Large** (100,000+ photos): 3-6 hours

    Mobile devices are typically 20-30% slower than desktop.

??? question "Can I pause and resume processing?"
    Currently, processing cannot be paused. However, if interrupted, you can safely restart and the tool will skip already-processed files.

??? question "How accurate is duplicate detection?"
    Duplicate detection uses SHA256 hashing, which is cryptographically secure and has a near-zero false positive rate. If two files have the same hash, they are **guaranteed** to be identical bit-for-bit.

??? question "Why are some non-blurry photos flagged as blurry?"
    The blur detection algorithm (Laplacian variance) works well for most photos but can flag:

    - Photos with uniform colors (sky, walls)
    - Intentionally soft-focus artistic shots
    - Low-contrast images

    You can adjust the blur threshold (default: 100.0) to reduce false positives.

??? question "What's the difference between duplicates and bursts?"
    - **Duplicates**: Identical files (same hash) - exact copies
    - **Bursts**: Different photos taken within seconds - similar but not identical

    Duplicates are always safe to delete (keeping one). Bursts might have subtle differences worth reviewing.

## Mobile App

??? question "Does the mobile app work on iOS?"
    Not yet. iOS support is planned using Kivy's iOS toolchain, but it requires additional development and testing. Follow [issue #X] for updates.

??? question "Why is the mobile app slower than desktop?"
    Mobile devices have:

    - Less RAM
    - Slower CPUs
    - Thermal throttling
    - Lower storage I/O speeds

    The app is optimized with fewer worker threads (2 vs 4) to balance speed and battery life.

??? question "Can I build the APK on Windows?"
    Buildozer (Android build tool) works best on Linux. Windows users should:

    1. Use WSL (Windows Subsystem for Linux) - **Recommended**
    2. Use a Linux VM
    3. Use Docker with the Kivy/Buildozer image

    See [Mobile Build Guide](mobile/building.md#windows-users) for details.

??? question "How do I transfer files to my Android device?"
    Several options:

    1. **USB Cable + ADB**:
       ```bash
       adb push takeout.zip /sdcard/PhotoLibrary/GoogleTakeout/
       ```

    2. **File Manager Apps**: Use any file manager to copy from PC to phone

    3. **Cloud Storage**: Upload to Google Drive, download on phone

    4. **Network Share**: Use SMB/FTP if on same network

## Troubleshooting

??? question "Application crashes or freezes"
    **Possible causes and solutions:**

    1. **Insufficient RAM**:
        - Close other applications
        - Reduce worker threads in settings
        - Process in smaller batches

    2. **Corrupted photos**:
        - Check logs for specific error messages
        - Skip problematic files manually

    3. **Full disk**:
        - Ensure adequate free space (2x library size recommended)
        - Clean up temporary files

??? question "OpenCV or Pillow import errors"
    ```bash
    # Reinstall dependencies
    pip uninstall opencv-python Pillow
    pip install opencv-python Pillow --no-cache-dir

    # On some systems, you might need:
    pip install opencv-python-headless
    ```

??? question "Mobile app won't install on Android"
    **Check:**

    1. **Unknown Sources**: Enable "Install from Unknown Sources" in Settings
    2. **API Level**: Ensure Android 5.0+ (API 21+)
    3. **Architecture**: APK built for arm64-v8a and armeabi-v7a
    4. **Storage**: Sufficient space for installation

    **Debug:**
    ```bash
    adb install -r bin/PhotosManager-*.apk
    # -r flag reinstalls if already present
    ```

??? question "Storage permission denied on Android"
    **Android 10+** requires special permissions:

    1. Go to Settings → Apps → Photos Manager
    2. Grant Storage permissions
    3. If still failing, enable "All Files Access" (Android 11+)
    4. Restart app

??? question "Photos not being found in Takeout"
    **Verify structure:**

    ```
    GoogleTakeout/
    └── Takeout/
        └── Google Photos/
            ├── Photo1.jpg
            ├── Photo2.jpg
            └── ...
    ```

    **Common issues:**

    - Incomplete extraction
    - Wrong path selected
    - Non-standard Takeout structure
    - Symbolic links not supported

## Performance & Optimization

??? question "How can I speed up processing?"
    **Desktop:**

    - Increase worker threads (4-8 on modern CPUs)
    - Use SSD instead of HDD
    - Close other applications
    - Disable antivirus scanning of working directory temporarily

    **Mobile:**

    - Keep device plugged in (prevents throttling)
    - Close background apps
    - Use high-performance mode
    - Ensure device doesn't overheat

??? question "Is my data being uploaded anywhere?"
    **No!** All processing is 100% local:

    - No network requests
    - No telemetry or analytics
    - No cloud storage
    - No external services

    You can verify by monitoring network traffic or running completely offline.

??? question "How much storage do I need?"
    **Minimum**: Original Takeout size + 10%

    **Recommended**: Original Takeout size × 2

    **Example**: For a 50GB Takeout, have 100GB free space

## Advanced

??? question "Can I customize the blur detection algorithm?"
    Yes! Modify `blur_threshold` in settings:

    - **Lower** (50-80): More aggressive, flags more photos
    - **Default** (100): Balanced
    - **Higher** (150-200): Less aggressive, fewer false positives

    Or implement custom algorithms by extending `PhotoProcessorEnhanced`.

??? question "Can I process photos from sources other than Google Takeout?"
    Partially. The tool is optimized for Google Takeout structure but can process any photo directory by:

    1. Placing photos in expected directory structure
    2. Using the core `PhotoProcessorEnhanced` class directly
    3. Customizing file scanning logic

    See [API Documentation](api/photo-processor.md) for details.

??? question "How do I contribute code?"
    We welcome contributions! See:

    - [Contributing Guide](development/contributing.md)
    - [Development Setup](development/setup.md)
    - [Code Style Guide](development/code-style.md)

    Or start with [Good First Issues](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/labels/good%20first%20issue).

??? question "Can I use this commercially?"
    Yes! The MIT License allows commercial use. You can:

    - Use it in your business
    - Modify and distribute it
    - Include it in commercial products

    Just maintain the original license and copyright notice.

## Data & Privacy

??? question "What metadata is preserved?"
    The tool preserves:

    - EXIF data (camera settings, location, date)
    - Creation/modification times
    - File permissions
    - Original filenames

    Organized copies maintain all original metadata.

??? question "Does it modify original files?"
    **Never!** The original Google Takeout folder is read-only from the app's perspective. All modifications happen on copies in the organized output folder.

??? question "Where is my data stored?"
    **Desktop:**

    - Default: `~/PhotoLibrary/`
    - Configurable in settings

    **Mobile:**

    - Default: `/sdcard/PhotoLibrary/`
    - Respects Android storage best practices

    **Review data:**

    - Stored locally in `Review/` folder
    - JSON files for decisions
    - Never uploaded or shared

## Support & Community

??? question "I found a bug! Where do I report it?"
    Please [open an issue](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues/new?template=bug_report.md) on GitHub with:

    - Detailed description
    - Steps to reproduce
    - System information
    - Relevant logs

    See our [Bug Report Template](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/blob/main/.github/ISSUE_TEMPLATE/bug_report.md).

??? question "I have a feature request"
    Great! [Submit a feature request](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues/new?template=feature_request.md) with:

    - Problem you're trying to solve
    - Proposed solution
    - Use cases and examples

    Or join [Discussions](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions) to brainstorm ideas!

??? question "Where can I get help?"
    Multiple channels available:

    - 📖 [Documentation](https://nicknak86.github.io/Mikes_GooglePhoto-Fixer/)
    - 💬 [GitHub Discussions](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions)
    - 🐛 [Issue Tracker](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
    - 📧 Check repository for contact information

??? question "How can I support the project?"
    You can help by:

    - ⭐ **Starring** the repository
    - 🐛 **Reporting** bugs and issues
    - 💡 **Suggesting** features
    - 📝 **Contributing** code or documentation
    - 💬 **Helping** others in Discussions
    - 📢 **Sharing** with friends and colleagues

---

## Still have questions?

If your question isn't answered here:

1. Search [existing issues](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
2. Check [documentation](index.md)
3. Ask in [Discussions](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions)
4. [Open a new issue](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues/new)

We're here to help! 🎉
