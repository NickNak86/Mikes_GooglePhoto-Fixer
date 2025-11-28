"""
Compatibility tests for Pillow library.
"""

import pytest
from PIL import Image, ImageFilter
from pathlib import Path


class TestPillowCompatibility:
    """Tests for Pillow library compatibility."""

    def test_pillow_import(self):
        """Test that Pillow can be imported."""
        import PIL
        assert PIL is not None
        assert hasattr(PIL, '__version__')

    def test_image_creation(self, temp_dir):
        """Test creating basic images."""
        img = Image.new('RGB', (100, 100), color='red')
        assert img.size == (100, 100)
        assert img.mode == 'RGB'

    def test_image_save_load(self, temp_dir):
        """Test saving and loading images."""
        img_path = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(img_path, 'JPEG')

        loaded = Image.open(img_path)
        assert loaded.size == (100, 100)

    def test_supported_formats(self, temp_dir):
        """Test that common formats are supported."""
        formats = ['JPEG', 'PNG', 'BMP', 'GIF']
        img = Image.new('RGB', (50, 50), color='green')

        for fmt in formats:
            ext = fmt.lower() if fmt != 'JPEG' else 'jpg'
            path = temp_dir / f"test.{ext}"
            img.save(path, fmt if fmt != 'GIF' else 'GIF')
            assert path.exists()

    def test_image_filters(self, temp_dir):
        """Test that image filters work."""
        img = Image.new('RGB', (100, 100), color='white')
        blurred = img.filter(ImageFilter.GaussianBlur(radius=5))
        assert blurred is not None
        assert blurred.size == img.size
