"""
Unit tests for quality assessment functionality.
Tests blur detection and size checking.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image, ImageFilter


def calculate_blur_score(image_path: Path) -> tuple[bool, float]:
    """
    Calculate blur score using Laplacian variance method.
    Returns (is_blurry, blur_score).
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    threshold = 100.0
    is_blurry = laplacian_var < threshold

    return is_blurry, laplacian_var


def check_image_size(image_path: Path, min_size_mb: float = 0.5) -> tuple[bool, float]:
    """
    Check if image file size is above threshold.
    Returns (is_too_small, size_in_mb).
    """
    size_bytes = image_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    is_too_small = size_mb < min_size_mb

    return is_too_small, size_mb


@pytest.mark.requires_opencv
class TestBlurDetection:
    """Tests for blur detection functionality."""

    def test_sharp_image_not_blurry(self, sample_image):
        """Test that a sharp image is not detected as blurry."""
        is_blurry, score = calculate_blur_score(sample_image)

        # Sharp image should have high variance (not blurry)
        assert score > 100.0
        assert not is_blurry

    def test_blurry_image_detected(self, blurry_image):
        """Test that a blurry image is correctly detected."""
        is_blurry, score = calculate_blur_score(blurry_image)

        # Blurry image should have low variance
        assert is_blurry
        assert score < 100.0

    def test_blur_score_consistency(self, sample_image):
        """Test that blur score is consistent across multiple calculations."""
        score1 = calculate_blur_score(sample_image)[1]
        score2 = calculate_blur_score(sample_image)[1]

        # Scores should be identical
        assert score1 == score2

    def test_blur_detection_different_thresholds(self, sample_image):
        """Test blur detection with different threshold values."""
        _, score = calculate_blur_score(sample_image)

        # Test with very low threshold (almost everything is sharp)
        assert score > 50.0

        # Test with very high threshold (almost everything is blurry)
        # (threshold comparison would be done in the main code)

    def test_blur_detection_various_images(self, temp_dir):
        """Test blur detection on various synthetic images."""
        from PIL import ImageDraw

        # Create high-detail image (should be sharp)
        sharp_img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(sharp_img)
        for i in range(0, 800, 10):
            draw.line([(i, 0), (i, 600)], fill='black', width=1)
        sharp_path = temp_dir / "sharp.jpg"
        sharp_img.save(sharp_path, 'JPEG', quality=95)

        is_blurry, score = calculate_blur_score(sharp_path)
        assert not is_blurry
        assert score > 100.0

    def test_blur_detection_grayscale_image(self, temp_dir):
        """Test blur detection on grayscale images."""
        # Create grayscale image
        gray_img = Image.new('L', (800, 600), color=128)
        gray_path = temp_dir / "gray.jpg"
        gray_img.save(gray_path, 'JPEG', quality=95)

        is_blurry, score = calculate_blur_score(gray_path)
        # Should not raise error
        assert isinstance(score, float)
        assert isinstance(is_blurry, bool)

    def test_blur_detection_invalid_file(self, temp_dir):
        """Test blur detection with invalid image file."""
        invalid_file = temp_dir / "not_an_image.txt"
        invalid_file.write_text("This is not an image")

        with pytest.raises(ValueError):
            calculate_blur_score(invalid_file)

    def test_blur_detection_nonexistent_file(self, temp_dir):
        """Test blur detection with nonexistent file."""
        nonexistent = temp_dir / "does_not_exist.jpg"

        with pytest.raises(ValueError):
            calculate_blur_score(nonexistent)

    def test_varying_blur_levels(self, temp_dir):
        """Test detection of varying blur levels."""
        # Create images with different blur amounts
        base_img = Image.new('RGB', (400, 300))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(base_img)
        # Add some detail
        for i in range(20):
            draw.rectangle([(i*20, i*15), (i*20+10, i*15+10)], fill=(i*10, i*10, i*10))

        blur_scores = []

        for radius in [0, 2, 5, 10, 20]:
            if radius == 0:
                img = base_img
            else:
                img = base_img.filter(ImageFilter.GaussianBlur(radius=radius))

            path = temp_dir / f"blur_{radius}.jpg"
            img.save(path, 'JPEG', quality=95)

            _, score = calculate_blur_score(path)
            blur_scores.append(score)

        # Scores should generally decrease as blur increases
        # (allowing some variation due to JPEG compression)
        assert blur_scores[0] > blur_scores[-1]


class TestSizeChecking:
    """Tests for file size checking functionality."""

    def test_large_file_not_too_small(self, sample_image):
        """Test that a normal-sized image passes size check."""
        is_too_small, size = check_image_size(sample_image, min_size_mb=0.01)

        # Sample images should be larger than 0.01 MB
        assert not is_too_small
        assert size > 0.01

    def test_small_file_detected(self, temp_dir):
        """Test that a small file is correctly detected."""
        # Create very small image
        small_img = Image.new('RGB', (10, 10), color='red')
        small_path = temp_dir / "tiny.jpg"
        small_img.save(small_path, 'JPEG', quality=10)

        is_too_small, size = check_image_size(small_path, min_size_mb=0.5)

        # Should be detected as too small
        assert is_too_small
        assert size < 0.5

    def test_size_check_threshold(self, sample_image):
        """Test size checking with different thresholds."""
        _, actual_size = check_image_size(sample_image)

        # With threshold below actual size
        is_small, _ = check_image_size(sample_image, min_size_mb=actual_size - 0.1)
        assert not is_small

        # With threshold above actual size
        is_small, _ = check_image_size(sample_image, min_size_mb=actual_size + 0.1)
        assert is_small

    def test_size_calculation_accuracy(self, temp_dir):
        """Test that size calculation is accurate."""
        # Create file with known size
        test_file = temp_dir / "known_size.bin"
        test_data = b'x' * (1024 * 1024)  # Exactly 1 MB
        test_file.write_bytes(test_data)

        is_too_small, size = check_image_size(test_file, min_size_mb=0.5)

        # Size should be approximately 1 MB
        assert 0.99 < size < 1.01
        assert not is_too_small

    def test_zero_size_file(self, temp_dir):
        """Test handling of zero-size file."""
        empty_file = temp_dir / "empty.jpg"
        empty_file.touch()

        is_too_small, size = check_image_size(empty_file, min_size_mb=0.1)

        assert size == 0.0
        assert is_too_small

    def test_size_check_nonexistent_file(self, temp_dir):
        """Test size check with nonexistent file."""
        nonexistent = temp_dir / "does_not_exist.jpg"

        with pytest.raises(FileNotFoundError):
            check_image_size(nonexistent)


class TestQualityAssessmentCombined:
    """Tests for combined quality assessment."""

    def test_high_quality_image(self, sample_image):
        """Test assessment of high-quality image."""
        is_blurry, blur_score = calculate_blur_score(sample_image)
        is_too_small, file_size = check_image_size(sample_image, min_size_mb=0.01)

        # High quality image should pass both checks
        assert not is_blurry
        assert not is_too_small
        assert blur_score > 100.0
        assert file_size > 0.01

    def test_low_quality_image(self, temp_dir):
        """Test assessment of low-quality image (small and blurry)."""
        # Create small, blurry image
        small_img = Image.new('RGB', (100, 100), color='gray')
        blurred = small_img.filter(ImageFilter.GaussianBlur(radius=15))
        path = temp_dir / "low_quality.jpg"
        blurred.save(path, 'JPEG', quality=10)

        is_blurry, blur_score = calculate_blur_score(path)
        is_too_small, file_size = check_image_size(path, min_size_mb=0.5)

        # Should fail both quality checks
        assert is_blurry or is_too_small  # At least one should fail

    def test_assessment_multiple_images(self, sample_images):
        """Test assessment of multiple images."""
        results = []

        for img_path in sample_images:
            is_blurry, blur_score = calculate_blur_score(img_path)
            is_too_small, file_size = check_image_size(img_path)

            results.append({
                'path': img_path,
                'is_blurry': is_blurry,
                'blur_score': blur_score,
                'is_too_small': is_too_small,
                'file_size': file_size
            })

        # Should have results for all images
        assert len(results) == len(sample_images)

        # All results should have valid data
        for result in results:
            assert isinstance(result['blur_score'], float)
            assert isinstance(result['file_size'], float)
            assert result['blur_score'] >= 0
            assert result['file_size'] >= 0


@pytest.mark.slow
@pytest.mark.requires_opencv
class TestQualityPerformance:
    """Performance tests for quality assessment."""

    def test_blur_detection_performance(self, temp_dir, benchmark):
        """Benchmark blur detection performance."""
        if not hasattr(pytest, 'benchmark'):
            pytest.skip("pytest-benchmark not installed")

        # Create test image
        img = Image.new('RGB', (1920, 1080), color='blue')
        path = temp_dir / "perf_test.jpg"
        img.save(path, 'JPEG', quality=90)

        # Benchmark
        result = benchmark(calculate_blur_score, path)
        assert result is not None

    def test_size_check_performance(self, sample_image, benchmark):
        """Benchmark size checking performance."""
        if not hasattr(pytest, 'benchmark'):
            pytest.skip("pytest-benchmark not installed")

        result = benchmark(check_image_size, sample_image)
        assert result is not None

    def test_combined_assessment_performance(self, sample_image, benchmark):
        """Benchmark combined quality assessment."""
        if not hasattr(pytest, 'benchmark'):
            pytest.skip("pytest-benchmark not installed")

        def combined_assessment(img_path):
            blur_result = calculate_blur_score(img_path)
            size_result = check_image_size(img_path)
            return blur_result, size_result

        result = benchmark(combined_assessment, sample_image)
        assert result is not None
