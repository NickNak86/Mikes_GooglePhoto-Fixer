"""
Unit tests for mobile_utils.py
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the modules to test
try:
    from mobile_utils import MobilePlatform, ConfigManager, StorageHelper
except ImportError:
    pytest.skip("mobile_utils not available", allow_module_level=True)


class TestMobilePlatform:
    """Tests for MobilePlatform class."""

    def test_is_android_detection(self):
        """Test Android platform detection."""
        with patch('mobile_utils.ANDROID', True):
            platform = MobilePlatform()
            assert platform.is_android() == True

    def test_is_not_android(self):
        """Test non-Android platform detection."""
        with patch('mobile_utils.ANDROID', False):
            platform = MobilePlatform()
            assert platform.is_android() == False

    def test_get_storage_path_desktop(self, temp_dir):
        """Test storage path on desktop platforms."""
        with patch('mobile_utils.ANDROID', False):
            with patch('pathlib.Path.home', return_value=temp_dir):
                platform = MobilePlatform()
                path = platform.get_storage_path()
                assert path == temp_dir / "PhotoLibrary"

    def test_get_storage_path_android(self):
        """Test storage path on Android fallback."""
        # When running in a non-Android environment with ANDROID patched to True,
        # the autoclass import will fail and it will use the fallback path
        with patch('mobile_utils.ANDROID', True):
            platform = MobilePlatform()
            path = platform.get_storage_path()
            # Should fallback to /sdcard/PhotoLibrary when autoclass fails
            assert str(path) == "/sdcard/PhotoLibrary"

    def test_get_config_dir_desktop(self, temp_dir):
        """Test config directory on desktop."""
        with patch('mobile_utils.ANDROID', False):
            with patch('pathlib.Path.home', return_value=temp_dir):
                platform = MobilePlatform()
                config_dir = platform.get_config_dir()
                assert config_dir == temp_dir / ".photomanager"

    def test_request_permissions_non_android(self):
        """Test permission request on non-Android (should not raise error)."""
        with patch('mobile_utils.ANDROID', False):
            platform = MobilePlatform()
            # Should not raise exception
            platform.request_permissions()

    def test_check_permissions_non_android(self):
        """Test permission check on non-Android (should return True)."""
        with patch('mobile_utils.ANDROID', False):
            platform = MobilePlatform()
            assert platform.check_permissions() == True


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_load_default_config(self, temp_dir):
        """Test loading default configuration."""
        config_file = temp_dir / "config.json"
        manager = ConfigManager(config_file)

        config = manager.load_config()
        assert "worker_threads" in config
        assert "blur_threshold" in config
        assert "size_threshold" in config

    def test_save_and_load_config(self, temp_dir):
        """Test saving and loading configuration."""
        config_file = temp_dir / "config.json"
        manager = ConfigManager(config_file)

        # Save custom config
        custom_config = {
            "worker_threads": 4,
            "blur_threshold": 150.0,
            "custom_setting": "test_value"
        }
        manager.save_config(custom_config)

        # Load and verify
        loaded_config = manager.load_config()
        assert loaded_config["worker_threads"] == 4
        assert loaded_config["blur_threshold"] == 150.0
        assert loaded_config["custom_setting"] == "test_value"

    def test_get_setting(self, temp_dir):
        """Test getting individual settings."""
        config_file = temp_dir / "config.json"
        manager = ConfigManager(config_file)

        config = {"test_key": "test_value"}
        manager.save_config(config)

        assert manager.get("test_key") == "test_value"
        assert manager.get("non_existent", "default") == "default"

    def test_set_setting(self, temp_dir):
        """Test setting individual settings."""
        config_file = temp_dir / "config.json"
        manager = ConfigManager(config_file)

        manager.set("new_key", "new_value")
        assert manager.get("new_key") == "new_value"

    def test_mobile_default_threads(self, temp_dir):
        """Test that mobile gets fewer default threads."""
        config_file = temp_dir / "config.json"

        with patch('mobile_utils.ANDROID', True):
            manager = ConfigManager(config_file)
            config = manager.load_config()
            assert config["worker_threads"] == 2

    def test_desktop_default_threads(self, temp_dir):
        """Test that desktop gets more default threads."""
        config_file = temp_dir / "config.json"

        with patch('mobile_utils.ANDROID', False):
            manager = ConfigManager(config_file)
            config = manager.load_config()
            assert config["worker_threads"] == 4


class TestStorageHelper:
    """Tests for StorageHelper class."""

    def test_get_review_folder_path(self, temp_dir):
        """Test getting review folder path."""
        helper = StorageHelper(base_path=temp_dir)
        review_path = helper.get_review_folder_path()
        assert review_path == temp_dir / "Review"

    def test_count_photos_in_directory(self, temp_dir, sample_images):
        """Test counting photos in directory."""
        # sample_images are already in temp_dir, no need to copy
        helper = StorageHelper(base_path=temp_dir)
        count = helper.count_photos_in_directory(temp_dir)
        assert count == len(sample_images)

    def test_count_photos_empty_directory(self, temp_dir):
        """Test counting photos in empty directory."""
        helper = StorageHelper(base_path=temp_dir)
        count = helper.count_photos_in_directory(temp_dir)
        assert count == 0

    def test_get_folder_size(self, temp_dir, sample_images):
        """Test getting folder size."""
        # sample_images are already in temp_dir, no need to copy
        helper = StorageHelper(base_path=temp_dir)
        size = helper.get_folder_size(temp_dir)
        assert size > 0

    def test_format_size_bytes(self):
        """Test human-readable size formatting."""
        helper = StorageHelper()

        assert helper.format_size(500) == "500.0 B"
        assert helper.format_size(1024) == "1.0 KB"
        assert helper.format_size(1024 * 1024) == "1.0 MB"
        assert helper.format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert helper.format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    def test_format_size_zero(self):
        """Test formatting zero size."""
        helper = StorageHelper()
        assert helper.format_size(0) == "0.0 B"

    def test_get_review_categories(self, temp_dir):
        """Test getting review category folders."""
        helper = StorageHelper(base_path=temp_dir)

        # Create review category folders
        review_path = temp_dir / "Review"
        (review_path / "Duplicates").mkdir(parents=True, exist_ok=True)
        (review_path / "Blurry").mkdir(parents=True, exist_ok=True)
        (review_path / "Too Small").mkdir(parents=True, exist_ok=True)

        categories = helper.get_review_categories()
        assert "Duplicates" in categories
        assert "Blurry" in categories
        assert "Too Small" in categories


@pytest.mark.integration
def test_full_mobile_utils_workflow(temp_dir):
    """Integration test for complete mobile utils workflow."""
    with patch('mobile_utils.ANDROID', False):
        with patch('pathlib.Path.home', return_value=temp_dir):
            # Create platform instance
            platform = MobilePlatform()

            # Get storage path
            storage_path = platform.get_storage_path()
            storage_path.mkdir(parents=True, exist_ok=True)

            # Create config manager
            config_dir = platform.get_config_dir()
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / "config.json"
            config_manager = ConfigManager(config_file)

            # Save and load config
            config_manager.set("test_setting", "test_value")
            assert config_manager.get("test_setting") == "test_value"

            # Use storage helper
            storage_helper = StorageHelper(base_path=storage_path)
            review_path = storage_helper.get_review_folder_path()
            review_path.mkdir(parents=True, exist_ok=True)

            # Verify everything works together
            assert storage_path.exists()
            assert config_file.exists()
            assert review_path.exists()
