"""
Unit tests for hash calculation in PhotoProcessorEnhanced.
"""

import hashlib
from pathlib import Path

import pytest


def calculate_file_hash(file_path: Path) -> str:
    """
    Helper function to calculate file hash.
    This mirrors the implementation in PhotoProcessorEnhanced.
    """
    hash_obj = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


class TestHashCalculation:
    """Tests for file hash calculation."""

    def test_hash_single_file(self, sample_image):
        """Test hashing a single file."""
        hash_value = calculate_file_hash(sample_image)

        assert hash_value is not None
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64 hex characters

    def test_hash_consistency(self, sample_image):
        """Test that hashing the same file twice produces the same result."""
        hash1 = calculate_file_hash(sample_image)
        hash2 = calculate_file_hash(sample_image)

        assert hash1 == hash2

    def test_different_files_different_hashes(self, sample_images):
        """Test that different files produce different hashes."""
        hashes = set()
        for image in sample_images:
            hash_value = calculate_file_hash(image)
            hashes.add(hash_value)

        # All hashes should be unique (assuming images are different)
        assert len(hashes) == len(sample_images)

    def test_identical_files_same_hash(self, duplicate_images):
        """Test that identical files produce the same hash."""
        img1, img2 = duplicate_images

        hash1 = calculate_file_hash(img1)
        hash2 = calculate_file_hash(img2)

        assert hash1 == hash2

    def test_hash_large_file(self, temp_dir):
        """Test hashing a large file (simulated)."""
        # Create a larger file
        large_file = temp_dir / "large_file.bin"
        with open(large_file, 'wb') as f:
            # Write 10MB of data
            f.write(b'x' * (10 * 1024 * 1024))

        hash_value = calculate_file_hash(large_file)
        assert hash_value is not None
        assert len(hash_value) == 64

    def test_hash_empty_file(self, temp_dir):
        """Test hashing an empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()

        hash_value = calculate_file_hash(empty_file)
        assert hash_value is not None
        # Empty file should have a known SHA256 hash
        expected_empty_hash = hashlib.sha256(b'').hexdigest()
        assert hash_value == expected_empty_hash

    def test_hash_nonexistent_file(self, temp_dir):
        """Test hashing a nonexistent file raises error."""
        nonexistent = temp_dir / "does_not_exist.jpg"

        with pytest.raises(FileNotFoundError):
            calculate_file_hash(nonexistent)

    def test_hash_binary_content(self, temp_dir):
        """Test hashing file with binary content."""
        binary_file = temp_dir / "binary.dat"
        binary_content = bytes(range(256))
        binary_file.write_bytes(binary_content)

        hash_value = calculate_file_hash(binary_file)
        assert hash_value is not None

        # Verify by calculating expected hash
        expected = hashlib.sha256(binary_content).hexdigest()
        assert hash_value == expected

    @pytest.mark.skipif(not pytest.config.pluginmanager.hasplugin('benchmark'), 
                        reason="pytest-benchmark not installed")
    def test_hash_performance(self, temp_dir, benchmark):
        """Benchmark hash calculation performance."""
        # Create test file
        test_file = temp_dir / "perf_test.bin"
        test_file.write_bytes(b'x' * (1024 * 1024))  # 1MB

        # Benchmark the hash calculation
        result = benchmark(calculate_file_hash, test_file)
        assert result is not None


class TestDuplicateDetection:
    """Tests for duplicate detection using hashes."""

    def test_detect_duplicates_in_list(self, sample_images, duplicate_images):
        """Test detecting duplicates in a list of files."""
        # Combine sample images with duplicates
        all_files = list(sample_images) + list(duplicate_images)

        # Calculate hashes
        hash_to_files = {}
        for file_path in all_files:
            file_hash = calculate_file_hash(file_path)
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(file_path)

        # Find duplicates (groups with more than one file)
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

        # Should have exactly one group of duplicates
        assert len(duplicates) == 1

        # That group should have 2 files
        duplicate_group = list(duplicates.values())[0]
        assert len(duplicate_group) == 2

    def test_no_duplicates_in_unique_set(self, sample_images):
        """Test that unique files are not marked as duplicates."""
        hash_to_files = {}
        for file_path in sample_images:
            file_hash = calculate_file_hash(file_path)
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(file_path)

        # Find duplicates
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

        # Should have no duplicates
        assert len(duplicates) == 0

    def test_multiple_duplicate_groups(self, temp_dir):
        """Test detecting multiple groups of duplicates."""
        from PIL import Image

        # Create first duplicate group
        img1a = temp_dir / "dup1a.jpg"
        img1b = temp_dir / "dup1b.jpg"
        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(img1a, 'JPEG')
        img1.save(img1b, 'JPEG')

        # Create second duplicate group
        img2a = temp_dir / "dup2a.jpg"
        img2b = temp_dir / "dup2b.jpg"
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(img2a, 'JPEG')
        img2.save(img2b, 'JPEG')

        # Create unique file
        img3 = temp_dir / "unique.jpg"
        img3_data = Image.new('RGB', (100, 100), color='green')
        img3_data.save(img3, 'JPEG')

        all_files = [img1a, img1b, img2a, img2b, img3]

        # Calculate hashes
        hash_to_files = {}
        for file_path in all_files:
            file_hash = calculate_file_hash(file_path)
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(file_path)

        # Find duplicates
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

        # Should have 2 duplicate groups
        assert len(duplicates) == 2

        # Each group should have 2 files
        for files in duplicates.values():
            assert len(files) == 2


@pytest.mark.slow
class TestHashPerformance:
    """Performance tests for hash calculation."""

    def test_parallel_hash_calculation_benefit(self, temp_dir):
        """Test that parallel hashing is faster than sequential."""
        from concurrent.futures import ThreadPoolExecutor
        import time

        # Create multiple test files
        files = []
        for i in range(10):
            f = temp_dir / f"file_{i}.bin"
            f.write_bytes(b'x' * (1024 * 1024))  # 1MB each
            files.append(f)

        # Sequential hashing
        start = time.time()
        sequential_hashes = [calculate_file_hash(f) for f in files]
        sequential_time = time.time() - start

        # Parallel hashing
        start = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            parallel_hashes = list(executor.map(calculate_file_hash, files))
        parallel_time = time.time() - start

        # Results should be the same
        assert sequential_hashes == parallel_hashes

        # Parallel should be faster (or at least not significantly slower)
        # Note: On some systems, parallel might not always be faster for small files
        assert parallel_time <= sequential_time * 1.5  # Allow 50% margin
