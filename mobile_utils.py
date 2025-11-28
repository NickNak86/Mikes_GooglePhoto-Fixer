"""
Mobile Platform Utilities
=========================
Android-specific utilities for permissions, storage, and platform features

Author: Claude Code
Date: 2025-11-20
Version: 2.1
"""

from pathlib import Path
import os
import json

# Platform detection
try:
    from jnius import autoclass
    from android.permissions import request_permissions, check_permission, Permission
    ANDROID = True
except ImportError:
    ANDROID = False


class MobilePlatform:
    """Platform-specific utilities"""

    @staticmethod
    def is_android() -> bool:
        """Check if running on Android"""
        return ANDROID

    @staticmethod
    def request_storage_permissions():
        """Request storage permissions on Android (legacy method for backwards compatibility)"""
        return MobilePlatform.request_permissions()

    @staticmethod
    def check_storage_permissions() -> bool:
        """Check if storage permissions are granted (legacy method for backwards compatibility)"""
        return MobilePlatform.check_permissions()

    @staticmethod
    def get_storage_path() -> Path:
        """Get platform-specific storage path"""
        if ANDROID:
            # Android external storage
            try:
                Environment = autoclass('android.os.Environment')
                storage = Environment.getExternalStorageDirectory().getPath()
                return Path(storage) / "PhotoLibrary"
            except:
                return Path("/sdcard/PhotoLibrary")
        else:
            # Desktop or other platforms
            return Path.home() / "PhotoLibrary"

    @staticmethod
    def get_config_dir() -> Path:
        """Get platform-specific config directory"""
        if ANDROID:
            # Android app data directory
            try:
                from android import mActivity
                context = mActivity.getApplicationContext()
                files_dir = context.getFilesDir().getPath()
                return Path(files_dir)
            except:
                return Path("/sdcard/PhotoLibrary")
        else:
            return Path.home() / ".photomanager"

    @staticmethod
    def get_config_path() -> Path:
        """Get platform-specific config path (legacy method for backwards compatibility)"""
        return MobilePlatform.get_config_dir()

    @staticmethod
    def request_permissions():
        """Request necessary permissions"""
        if not ANDROID:
            return True

        try:
            # Request necessary permissions
            permissions = [
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.CAMERA
            ]
            request_permissions(permissions)
            return True
        except Exception as e:
            print(f"Error requesting permissions: {e}")
            return False

    @staticmethod
    def check_permissions() -> bool:
        """Check if storage permissions are granted"""
        if not ANDROID:
            return True

        try:
            has_read = check_permission(Permission.READ_EXTERNAL_STORAGE)
            has_write = check_permission(Permission.WRITE_EXTERNAL_STORAGE)
            return has_read and has_write
        except:
            return False


class ConfigManager:
    """Manage app configuration"""

    def __init__(self, config_file: Path = None):
        if config_file is None:
            self.config_file = MobilePlatform.get_config_dir() / "config.json"
        else:
            self.config_file = Path(config_file)
        self.config = self.load_config()

    def load(self) -> dict:
        """Load configuration (legacy method)"""
        return self.load_config()

    def load_config(self) -> dict:
        """Load configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Default configuration
        return {
            'base_path': str(MobilePlatform.get_storage_path()),
            'worker_threads': 2 if MobilePlatform.is_android() else 4,
            'blur_threshold': 100.0,
            'size_threshold': 0.5,
            'max_workers': 2 if MobilePlatform.is_android() else 4,
            'auto_backup': True,
            'backup_path': '',
            'theme': 'dark',
            'notifications': True
        }

    def save(self):
        """Save configuration (legacy method)"""
        return self.save_config(self.config)

    def save_config(self, config: dict = None):
        """Save configuration"""
        if config is not None:
            self.config = config
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set configuration value"""
        self.config[key] = value
        self.save()


class StorageHelper:
    """Helper for file and folder management"""

    def __init__(self, base_path: Path = None):
        """Initialize StorageHelper with optional base path"""
        if base_path is None:
            self.base_path = MobilePlatform.get_storage_path()
        else:
            self.base_path = Path(base_path)

    def get_review_folder_path(self) -> Path:
        """Get the main review folder path"""
        return self.base_path / "Review"

    def get_review_folders(self, base_path: Path = None) -> dict:
        """Get review folder paths"""
        if base_path is None:
            base_path = self.base_path
        review_dir = base_path / "Pics Waiting for Approval"
        return {
            'too_small': review_dir / "NEEDS ATTENTION - Too Small",
            'blur_corrupt': review_dir / "NEEDS ATTENTION - Blurry or Corrupt",
            'burst': review_dir / "NEEDS ATTENTION - Burst Photos",
            'duplicates': review_dir / "NEEDS ATTENTION - Duplicates"
        }

    def get_review_categories(self) -> list[str]:
        """Get list of review category folder names"""
        review_path = self.get_review_folder_path()
        categories = []
        if review_path.exists():
            for item in review_path.iterdir():
                if item.is_dir():
                    categories.append(item.name)
        return categories

    def count_photos_in_directory(self, path: Path) -> int:
        """Count photos in directory"""
        if not path.exists():
            return 0

        photo_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.webp'}
        count = 0

        try:
            for item in path.rglob('*'):
                if item.is_file() and item.suffix.lower() in photo_extensions:
                    count += 1
        except:
            pass

        return count

    @staticmethod
    def get_photo_count(path: Path) -> int:
        """Count photos in directory (static method for backwards compatibility)"""
        helper = StorageHelper()
        return helper.count_photos_in_directory(path)

    def get_folder_size(self, path: Path) -> int:
        """Get total size of folder in bytes"""
        if not path.exists():
            return 0

        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except:
            pass

        return total

    def format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
