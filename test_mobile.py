#!/usr/bin/env python3
"""
Quick Test Script for Mobile App
=================================
Tests mobile utilities and basic functionality before building APK

Run this to verify everything works before running Buildozer
"""

import sys
from pathlib import Path

print("=" * 60)
print("Google Photos Manager - Mobile App Test")
print("=" * 60)
print()

# Test 1: Import mobile utilities
print("[1/6] Testing mobile utilities import...")
try:
    from mobile_utils import MobilePlatform, ConfigManager, StorageHelper
    print("✓ Mobile utilities imported successfully")
except Exception as e:
    print(f"✗ Failed to import mobile utilities: {e}")
    sys.exit(1)

# Test 2: Platform detection
print("\n[2/6] Testing platform detection...")
try:
    is_android = MobilePlatform.is_android()
    print(f"✓ Platform: {'Android' if is_android else 'Desktop/Other'}")
except Exception as e:
    print(f"✗ Platform detection failed: {e}")
    sys.exit(1)

# Test 3: Storage paths
print("\n[3/6] Testing storage paths...")
try:
    storage_path = MobilePlatform.get_storage_path()
    config_path = MobilePlatform.get_config_path()
    print(f"✓ Storage path: {storage_path}")
    print(f"✓ Config path: {config_path}")
except Exception as e:
    print(f"✗ Storage path detection failed: {e}")
    sys.exit(1)

# Test 4: Config manager
print("\n[4/6] Testing config manager...")
try:
    config = ConfigManager()
    base_path = config.get('base_path')
    max_workers = config.get('max_workers')
    print(f"✓ Config loaded successfully")
    print(f"  - Base path: {base_path}")
    print(f"  - Max workers: {max_workers}")
except Exception as e:
    print(f"✗ Config manager failed: {e}")
    sys.exit(1)

# Test 5: Import Kivy components
print("\n[5/6] Testing Kivy imports...")
try:
    from kivy.app import App
    from kivymd.app import MDApp
    print("✓ Kivy and KivyMD imported successfully")
except Exception as e:
    print(f"✗ Kivy imports failed: {e}")
    print("  Run: pip install kivy==2.2.1 kivymd==1.1.1")
    sys.exit(1)

# Test 6: Import main app
print("\n[6/6] Testing main app import...")
try:
    from PhotoManagerMobile import PhotosManagerMobileApp
    print("✓ Main app imported successfully")
except Exception as e:
    print(f"✗ Main app import failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print()
print("Next steps:")
print("  1. Test run: python PhotoManagerMobile.py")
print("  2. Build APK: buildozer -v android debug")
print()
