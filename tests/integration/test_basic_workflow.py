"""
Basic integration tests for the photo management workflow.
"""

import pytest
from pathlib import Path
from PIL import Image


@pytest.mark.integration
class TestBasicWorkflow:
    """Integration tests for basic photo management workflow."""

    def test_create_photo_library_structure(self, temp_dir):
        """Test creating the photo library directory structure."""
        library_path = temp_dir / "PhotoLibrary"
        library_path.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        (library_path / "Photos & Videos").mkdir(exist_ok=True)
        (library_path / "Review").mkdir(exist_ok=True)
        (library_path / "GoogleTakeout").mkdir(exist_ok=True)

        assert library_path.exists()
        assert (library_path / "Photos & Videos").exists()
        assert (library_path / "Review").exists()
        assert (library_path / "GoogleTakeout").exists()

    def test_image_processing_workflow(self, temp_dir):
        """Test basic image processing workflow."""
        # Create source and destination directories
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "processed"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create a test image
        img = Image.new('RGB', (800, 600), color='red')
        img_path = source_dir / "test.jpg"
        img.save(img_path, 'JPEG', quality=95)

        # Verify image exists
        assert img_path.exists()
        assert img_path.stat().st_size > 0

        # Simulate processing: copy to destination
        import shutil
        processed_path = dest_dir / "test.jpg"
        shutil.copy(img_path, processed_path)

        assert processed_path.exists()
        assert processed_path.stat().st_size == img_path.stat().st_size

    def test_review_folder_organization(self, temp_dir):
        """Test organizing photos into review folders."""
        review_dir = temp_dir / "Review"
        review_dir.mkdir()

        # Create review categories
        categories = ["Duplicates", "Blurry", "Too Small"]
        for category in categories:
            (review_dir / category).mkdir()

        # Verify all categories exist
        for category in categories:
            assert (review_dir / category).exists()
            assert (review_dir / category).is_dir()

    def test_photo_count_in_directory(self, temp_dir):
        """Test counting photos in a directory."""
        photo_dir = temp_dir / "photos"
        photo_dir.mkdir()

        # Create multiple test images
        for i in range(5):
            img = Image.new('RGB', (100, 100), color=(i*50, 100, 150))
            img.save(photo_dir / f"photo_{i}.jpg", 'JPEG')

        # Count photos
        photo_extensions = {'.jpg', '.jpeg', '.png'}
        count = sum(1 for f in photo_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in photo_extensions)

        assert count == 5
