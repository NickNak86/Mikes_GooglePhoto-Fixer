"""
Pytest configuration and shared fixtures for Google Photos Manager tests.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """Create a sample test image with sufficient detail to avoid blur detection."""
    from PIL import ImageDraw
    image_path = temp_dir / "test_image.jpg"
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    # Add detailed pattern to ensure high variance
    for i in range(0, 800, 5):
        draw.line([(i, 0), (i, 600)], fill='black', width=1)
    for i in range(0, 600, 5):
        draw.line([(0, i), (800, i)], fill='black', width=1)
    img.save(image_path, 'JPEG', quality=95)
    return image_path


@pytest.fixture
def sample_images(temp_dir: Path) -> list[Path]:
    """Create multiple sample test images with different properties."""
    from PIL import ImageDraw
    images = []

    # High quality image with detail
    img1 = Image.new('RGB', (1920, 1080), color='white')
    draw1 = ImageDraw.Draw(img1)
    for i in range(0, 1920, 10):
        draw1.line([(i, 0), (i, 1080)], fill='blue', width=1)
    path1 = temp_dir / "high_quality.jpg"
    img1.save(path1, 'JPEG', quality=95)
    images.append(path1)

    # Low quality image
    img2 = Image.new('RGB', (640, 480), color='green')
    path2 = temp_dir / "low_quality.jpg"
    img2.save(path2, 'JPEG', quality=50)
    images.append(path2)

    # Small image
    img3 = Image.new('RGB', (200, 150), color='yellow')
    path3 = temp_dir / "small_image.jpg"
    img3.save(path3, 'JPEG', quality=95)
    images.append(path3)

    return images


@pytest.fixture
def duplicate_images(temp_dir: Path) -> tuple[Path, Path]:
    """Create two identical images for duplicate detection testing."""
    img = Image.new('RGB', (800, 600), color='purple')

    path1 = temp_dir / "duplicate1.jpg"
    img.save(path1, 'JPEG', quality=95)

    path2 = temp_dir / "duplicate2.jpg"
    img.save(path2, 'JPEG', quality=95)

    return path1, path2


@pytest.fixture
def blurry_image(temp_dir: Path) -> Path:
    """Create a blurry test image."""
    from PIL import ImageFilter

    img = Image.new('RGB', (800, 600), color='orange')
    blurred = img.filter(ImageFilter.GaussianBlur(radius=10))

    path = temp_dir / "blurry.jpg"
    blurred.save(path, 'JPEG', quality=95)
    return path


@pytest.fixture
def mock_google_takeout(temp_dir: Path) -> Path:
    """Create a mock Google Takeout directory structure."""
    takeout_path = temp_dir / "GoogleTakeout" / "Takeout" / "Google Photos"
    takeout_path.mkdir(parents=True, exist_ok=True)

    # Create some sample photos in the takeout
    for i in range(5):
        img = Image.new('RGB', (800, 600), color=(i*50, 100, 150))
        img.save(takeout_path / f"photo_{i}.jpg", 'JPEG', quality=90)

    # Create a metadata JSON file
    import json
    metadata = {
        "title": "photo_0.jpg",
        "description": "Test photo",
        "creationTime": {"timestamp": "1609459200"},
        "photoTakenTime": {"timestamp": "1609459200"}
    }
    with open(takeout_path / "photo_0.jpg.json", 'w') as f:
        json.dump(metadata, f)

    return takeout_path


@pytest.fixture
def mock_photo_library(temp_dir: Path) -> Path:
    """Create a mock photo library directory structure."""
    library_path = temp_dir / "PhotoLibrary"
    (library_path / "Photos & Videos").mkdir(parents=True, exist_ok=True)
    (library_path / "Review").mkdir(parents=True, exist_ok=True)
    (library_path / "GoogleTakeout").mkdir(parents=True, exist_ok=True)
    return library_path


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.delenv("PHOTO_LIBRARY_PATH", raising=False)


@pytest.fixture
def mock_config(temp_dir: Path) -> dict:
    """Create a mock configuration dictionary."""
    return {
        "base_path": str(temp_dir / "PhotoLibrary"),
        "worker_threads": 2,
        "blur_threshold": 100.0,
        "size_threshold": 0.5,  # MB
        "review_folder": str(temp_dir / "PhotoLibrary" / "Review"),
        "output_folder": str(temp_dir / "PhotoLibrary" / "Photos & Videos"),
    }


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "mobile: marks tests as mobile-specific"
    )
    config.addinivalue_line(
        "markers", "desktop: marks tests as desktop-specific"
    )
    config.addinivalue_line(
        "markers", "requires_opencv: marks tests that require OpenCV"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "mobile" in str(item.fspath):
            item.add_marker(pytest.mark.mobile)
        if "desktop" in str(item.fspath):
            item.add_marker(pytest.mark.desktop)
