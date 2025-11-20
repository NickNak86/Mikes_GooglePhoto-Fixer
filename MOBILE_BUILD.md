# Mobile App Build Instructions

## Google Photos Manager - Android Edition

Complete guide to building and deploying the Android APK for the Photos Manager mobile app.

---

## Prerequisites

### Required Software

1. **Python 3.9+**
   ```bash
   python --version  # Should be 3.9 or higher
   ```

2. **Buildozer** (Android build tool)
   ```bash
   pip install buildozer
   ```

3. **Cython** (Required for Kivy)
   ```bash
   pip install cython
   ```

4. **Android SDK & NDK**
   - Buildozer will auto-download these if not present
   - Or manually install Android Studio

5. **Linux/WSL** (Recommended)
   - Buildozer works best on Linux
   - Windows users: Use WSL (Windows Subsystem for Linux)
   - Mac users: Native support

---

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /home/user/Systems_Automation/projects/8-GooglePhotos

# Install Python dependencies
pip install -r requirements.txt

# Install mobile-specific dependencies
pip install kivy==2.2.1 kivymd==1.1.1 buildozer cython
```

### 2. Test Locally (Desktop)

Before building for Android, test on desktop:

```bash
python PhotoManagerMobile.py
```

This will run the Kivy app in desktop mode for testing.

### 3. Initialize Buildozer

```bash
# This will use the existing buildozer.spec file
buildozer init
```

### 4. Build Debug APK

```bash
# First build (takes 20-40 minutes)
buildozer -v android debug

# Subsequent builds (5-10 minutes)
buildozer android debug
```

The APK will be created in: `bin/PhotosManager-2.1.0-arm64-v8a-debug.apk`

### 5. Install on Device

#### Via USB (ADB)
```bash
# Enable USB debugging on Android device
# Connect device via USB

buildozer android deploy run
```

#### Manual Install
```bash
# Copy APK to device
adb install bin/PhotosManager-2.1.0-arm64-v8a-debug.apk

# Or transfer via file manager and install
```

---

## Buildozer Spec Configuration

Key settings in `buildozer.spec`:

```ini
[app]
title = Photos Manager
package.name = photosmanager
package.domain = com.mikesystems
version = 2.1.0

# Android permissions
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,ACCESS_NETWORK_STATE

# Target API levels
android.api = 33
android.minapi = 21
android.ndk = 25b

# Architectures
android.archs = arm64-v8a, armeabi-v7a
```

---

## Build Commands Reference

### Clean Build
```bash
# Remove all build artifacts and start fresh
buildozer android clean
buildozer -v android debug
```

### Release Build (Signed)
```bash
# Create keystore (one-time)
keytool -genkey -v -keystore my-release-key.keystore -alias photos_manager -keyalg RSA -keysize 2048 -validity 10000

# Build release APK
buildozer android release

# Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore my-release-key.keystore bin/PhotosManager-2.1.0-arm64-v8a-release-unsigned.apk photos_manager

# Align APK
zipalign -v 4 bin/PhotosManager-2.1.0-arm64-v8a-release-unsigned.apk bin/PhotosManager-2.1.0-release.apk
```

### View Logs
```bash
# Run app and view logs
buildozer android deploy run logcat

# Or use ADB directly
adb logcat | grep python
```

---

## Troubleshooting

### Build Fails: "No module named 'Cython'"
```bash
pip install --upgrade cython
```

### Build Fails: SDK License Not Accepted
```bash
# Edit buildozer.spec
android.accept_sdk_license = True
```

### Build Fails: NDK Not Found
```bash
# Let Buildozer download it
buildozer android clean
rm -rf ~/.buildozer/android/platform/android-ndk*
buildozer -v android debug
```

### App Crashes on Startup
```bash
# Check logs
adb logcat | grep -i python

# Common issues:
# - Missing permissions in AndroidManifest.xml
# - Import errors (missing dependencies)
# - Path issues (use /sdcard/ on Android)
```

### Storage Access Issues
```bash
# Android 10+ requires special permissions
# Edit buildozer.spec to add:
android.gradle_dependencies = androidx.appcompat:appcompat:1.2.0
android.enable_androidx = True

# Request permissions at runtime (already implemented in mobile_utils.py)
```

---

## File Structure

```
8-GooglePhotos/
├── PhotoManagerMobile.py      # Main Kivy app
├── mobile_utils.py            # Android utilities & permissions
├── PhotoProcessorEnhanced.py  # Shared backend
├── buildozer.spec             # Build configuration
├── requirements.txt           # Python dependencies
├── bin/                       # Built APKs (created by Buildozer)
├── .buildozer/                # Build cache (created by Buildozer)
└── MOBILE_BUILD.md           # This file
```

---

## Testing Checklist

Before building final release:

- [ ] Test on desktop with `python PhotoManagerMobile.py`
- [ ] Verify all screens navigate correctly
- [ ] Test permissions request on Android 10+
- [ ] Test processing pipeline with sample photos
- [ ] Test review interface with different photo groups
- [ ] Verify storage paths work on device
- [ ] Test on multiple Android versions (API 21-33)
- [ ] Test on different screen sizes
- [ ] Check app doesn't crash on background/foreground
- [ ] Verify logs show no critical errors

---

## Performance Tips

1. **Reduce Worker Threads on Mobile**
   - Default: 2 workers (set in mobile_utils.py)
   - Desktop: 4 workers

2. **Optimize Image Loading**
   - Use AsyncImage for lazy loading
   - Limit displayed photos (currently 6 per group)

3. **Background Processing**
   - Processing runs in separate thread
   - UI stays responsive

4. **Storage Optimization**
   - Use /sdcard/FamilyArchive for compatibility
   - Avoid internal storage for large files

---

## Next Steps

1. **Build First APK**
   ```bash
   buildozer -v android debug
   ```

2. **Test on Device**
   - Transfer sample Google Takeout
   - Run processing
   - Review photos

3. **Iterate**
   - Fix bugs
   - Add features
   - Optimize performance

4. **Release**
   - Build signed release APK
   - Test thoroughly
   - Deploy to family devices

---

## Additional Resources

- [Buildozer Documentation](https://buildozer.readthedocs.io/)
- [Kivy Documentation](https://kivy.org/doc/stable/)
- [KivyMD Documentation](https://kivymd.readthedocs.io/)
- [Python for Android](https://python-for-android.readthedocs.io/)
- [Android Permissions Guide](https://developer.android.com/guide/topics/permissions/overview)

---

**Built with ❤️ for easy family photo management**
