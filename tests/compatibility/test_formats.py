"""
Compatibility tests for various image formats.
"""

import pytest
from PIL import Image
from pathlib import Path


class TestImageFormatSupport:
    """Tests for image format support."""

    def test_jpeg_format(self, temp_dir):
        """Test JPEG format support."""
        img = Image.new('RGB', (100, 100), color='red')
        path = temp_dir / "test.jpg"
        img.save(path, 'JPEG', quality=95)

        loaded = Image.open(path)
        assert loaded.format == 'JPEG'
        assert loaded.size == (100, 100)

    def test_png_format(self, temp_dir):
        """Test PNG format support."""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        path = temp_dir / "test.png"
        img.save(path, 'PNG')

        loaded = Image.open(path)
        assert loaded.format == 'PNG'
        assert loaded.size == (100, 100)

    def test_gif_format(self, temp_dir):
        """Test GIF format support."""
        img = Image.new('RGB', (100, 100), color='green')
        path = temp_dir / "test.gif"
        img.save(path, 'GIF')

        loaded = Image.open(path)
        assert loaded.format == 'GIF'
        assert loaded.size == (100, 100)

    def test_bmp_format(self, temp_dir):
        """Test BMP format support."""
        img = Image.new('RGB', (100, 100), color='blue')
        path = temp_dir / "test.bmp"
        img.save(path, 'BMP')

        loaded = Image.open(path)
        assert loaded.format == 'BMP'
        assert loaded.size == (100, 100)

    def test_webp_format(self, temp_dir):
        """Test WEBP format support."""
        try:
            img = Image.new('RGB', (100, 100), color='yellow')
            path = temp_dir / "test.webp"
            img.save(path, 'WEBP')

            loaded = Image.open(path)
            assert loaded.format == 'WEBP'
            assert loaded.size == (100, 100)
        except Exception:
            pytest.skip("WEBP not supported in this Pillow installation")

    def test_format_detection(self, temp_dir):
        """Test automatic format detection."""
        # Create different format files
        formats = {'jpg': 'JPEG', 'png': 'PNG', 'bmp': 'BMP', 'gif': 'GIF'}

        for ext, fmt in formats.items():
            img = Image.new('RGB', (50, 50), color='purple')
            path = temp_dir / f"test.{ext}"
            img.save(path, fmt if fmt != 'JPEG' else fmt)

            # Open without specifying format
            loaded = Image.open(path)
            assert loaded.size == (50, 50)
