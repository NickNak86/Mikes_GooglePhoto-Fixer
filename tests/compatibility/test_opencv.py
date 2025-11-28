"""
Compatibility tests for OpenCV library.
"""

import pytest
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


@pytest.mark.skipif(not HAS_OPENCV, reason="OpenCV not installed")
class TestOpenCVCompatibility:
    """Tests for OpenCV library compatibility."""

    def test_opencv_import(self):
        """Test that OpenCV can be imported."""
        assert cv2 is not None
        assert hasattr(cv2, '__version__')

    def test_image_read_write(self, temp_dir):
        """Test reading and writing images with OpenCV."""
        # Create test image with Pillow
        img_path = temp_dir / "test.jpg"
        pil_img = Image.new('RGB', (100, 100), color='red')
        pil_img.save(img_path, 'JPEG')

        # Read with OpenCV
        cv_img = cv2.imread(str(img_path))
        assert cv_img is not None
        assert cv_img.shape[:2] == (100, 100)

        # Write with OpenCV
        out_path = temp_dir / "output.jpg"
        cv2.imwrite(str(out_path), cv_img)
        assert out_path.exists()

    def test_color_conversion(self, temp_dir):
        """Test color space conversions."""
        img_path = temp_dir / "color.jpg"
        pil_img = Image.new('RGB', (50, 50), color='blue')
        pil_img.save(img_path, 'JPEG')

        img = cv2.imread(str(img_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        assert gray is not None
        assert len(gray.shape) == 2
        assert gray.shape == (50, 50)

    def test_laplacian_operation(self, temp_dir):
        """Test Laplacian operation for blur detection."""
        img_path = temp_dir / "laplacian.jpg"
        pil_img = Image.new('RGB', (100, 100), color='white')
        pil_img.save(img_path, 'JPEG')

        img = cv2.imread(str(img_path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        assert isinstance(variance, (float, np.floating))
        assert variance >= 0

    def test_numpy_integration(self):
        """Test that OpenCV works with numpy arrays."""
        # Create numpy array
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[:, :] = [255, 0, 0]  # Red image

        # Convert to grayscale
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        assert gray.shape == (100, 100)
        assert gray.dtype == np.uint8
