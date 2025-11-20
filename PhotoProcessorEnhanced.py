"""
Google Photos Processor - Enhanced Version with Performance & Features
=======================================================================
Version 2.1 with threading, blur detection, cancellation, and progress tracking

Author: Claude Code
Date: 2025-11-20
Version: 2.1
"""

import os
import json
import hashlib
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import subprocess
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


# Try to import OpenCV for blur detection
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


@dataclass
class ProcessingProgress:
    """Track processing progress with detailed statistics"""
    current_step: str = ""
    total_steps: int = 9
    current_step_num: int = 0
    files_processed: int = 0
    total_files: int = 0
    bytes_processed: int = 0
    total_bytes: int = 0
    start_time: Optional[datetime] = None
    eta_seconds: Optional[float] = None

    def percent_complete(self) -> float:
        """Calculate overall percent complete"""
        if self.total_files == 0:
            return 0.0
        step_weight = (self.current_step_num / self.total_steps) * 100
        file_weight = (self.files_processed / max(1, self.total_files)) * (100 / self.total_steps)
        return min(100.0, step_weight + file_weight)

    def calculate_eta(self) -> Optional[str]:
        """Calculate estimated time remaining"""
        if not self.start_time or self.files_processed == 0:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.files_processed / elapsed  # files per second
        remaining_files = self.total_files - self.files_processed

        if rate > 0:
            eta_seconds = remaining_files / rate
            self.eta_seconds = eta_seconds

            if eta_seconds < 60:
                return f"{int(eta_seconds)}s"
            elif eta_seconds < 3600:
                return f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
            else:
                hours = int(eta_seconds / 3600)
                minutes = int((eta_seconds % 3600) / 60)
                return f"{hours}h {minutes}m"
        return None


@dataclass
class PhotoFile:
    """Represents a photo/video file with metadata"""
    path: Path
    hash: Optional[str] = None
    size: int = 0
    width: int = 0
    height: int = 0
    date_taken: Optional[datetime] = None
    is_blurry: bool = False
    blur_score: Optional[float] = None  # Variance of Laplacian (higher = sharper)
    is_corrupted: bool = False
    quality_score: float = 0.0
    has_json: bool = False
    json_path: Optional[Path] = None

    def __post_init__(self):
        if self.size == 0:
            self.size = self.path.stat().st_size if self.path.exists() else 0


@dataclass
class ProcessingIssue:
    """Represents an issue found during processing"""
    category: str
    files: List[PhotoFile] = field(default_factory=list)
    recommended_keep: Optional[PhotoFile] = None
    group_id: Optional[str] = None
    description: str = ""


class PhotoProcessorEnhanced:
    """Enhanced processing engine with threading and advanced features"""

    # File extensions
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.webp'}
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.m4v', '.3gp'}

    # Quality thresholds
    MIN_FILE_SIZE_KB = 50
    MIN_RESOLUTION = 100000
    BLUR_THRESHOLD = 100.0  # Laplacian variance threshold
    BURST_TIME_THRESHOLD = 10

    def __init__(self, base_path: str, exiftool_path: str = None, max_workers: int = 4):
        """
        Initialize enhanced processor

        Args:
            base_path: Root directory
            exiftool_path: Path to exiftool executable
            max_workers: Number of threads for parallel processing
        """
        self.base_path = Path(base_path)
        self.exiftool_path = exiftool_path or self._find_exiftool()
        self.max_workers = max_workers

        # Folder structure
        self.photos_videos_dir = self.base_path / "Photos & Videos"
        self.takeout_dir = self.base_path / "GoogleTakeout"
        self.review_dir = self.base_path / "Pics Waiting for Approval"

        # Review subdirectories
        self.review_dirs = {
            'too_small': self.review_dir / "NEEDS ATTENTION - Too Small",
            'blur_corrupt': self.review_dir / "NEEDS ATTENTION - Blurry or Corrupt",
            'burst': self.review_dir / "NEEDS ATTENTION - Burst Photos",
            'duplicates': self.review_dir / "NEEDS ATTENTION - Duplicates"
        }

        # Processing state
        self.all_files: List[PhotoFile] = []
        self.issues: List[ProcessingIssue] = []
        self.stats = {
            'total_processed': 0,
            'duplicates_found': 0,
            'blurry_found': 0,
            'corrupted_found': 0,
            'bursts_found': 0,
            'too_small_found': 0,
            'moved_to_library': 0
        }

        # Progress tracking
        self.progress = ProcessingProgress()
        self.progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None

        # Cancellation support
        self.cancelled = False
        self.cancel_lock = threading.Lock()

        # Logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging to file"""
        log_dir = self.base_path / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"PhotoProcessor initialized - OpenCV available: {OPENCV_AVAILABLE}")

    def cancel(self):
        """Request cancellation of current operation"""
        with self.cancel_lock:
            self.cancelled = True
            self.logger.info("Cancellation requested")

    def is_cancelled(self) -> bool:
        """Check if operation was cancelled"""
        with self.cancel_lock:
            return self.cancelled

    def _find_exiftool(self) -> Optional[str]:
        """Try to find exiftool in common locations"""
        common_paths = [
            r"C:\Users\Mike\AppData\Local\Programs\ExifTool\exiftool.exe",
            r"C:\Program Files\ExifTool\exiftool.exe",
            r"C:\exiftool\exiftool.exe",
            "exiftool"
        ]

        for path in common_paths:
            if os.path.exists(path) or shutil.which(path):
                return path
        return None

    def _update_progress(self, message: str = None, files_delta: int = 0):
        """Update progress tracking"""
        if message:
            self.progress.current_step = message

        self.progress.files_processed += files_delta

        # Calculate ETA
        eta = self.progress.calculate_eta()

        # Notify callbacks
        if self.status_callback and message:
            status_msg = f"{message}"
            if self.progress.total_files > 0:
                status_msg += f" ({self.progress.files_processed}/{self.progress.total_files})"
            if eta:
                status_msg += f" - ETA: {eta}"
            self.status_callback(status_msg)

        if self.progress_callback:
            self.progress_callback(self.progress)

    def detect_blur_opencv(self, image_path: Path) -> Tuple[bool, float]:
        """
        Detect blur using OpenCV Laplacian variance

        Returns:
            (is_blurry, blur_score) - Lower score means more blurry
        """
        if not OPENCV_AVAILABLE:
            return False, 0.0

        try:
            # Read image
            image = cv2.imread(str(image_path))
            if image is None:
                return True, 0.0  # Corrupted

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Calculate Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Lower variance = more blurry
            is_blurry = laplacian_var < self.BLUR_THRESHOLD

            return is_blurry, float(laplacian_var)

        except Exception as e:
            self.logger.error(f"Error detecting blur for {image_path}: {e}")
            return False, 0.0

    def calculate_hashes_parallel(self):
        """Calculate file hashes using thread pool"""
        self._update_progress("Calculating file hashes (parallel)")

        self.progress.total_files = len(self.all_files)
        self.progress.start_time = datetime.now()

        def hash_file(photo: PhotoFile) -> Tuple[PhotoFile, Optional[str]]:
            """Hash a single file"""
            if self.is_cancelled():
                return photo, None
            try:
                photo.hash = self._calculate_hash(photo.path)
                return photo, photo.hash
            except Exception as e:
                self.logger.error(f"Error hashing {photo.path}: {e}")
                return photo, None

        # Process in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(hash_file, photo): photo for photo in self.all_files}

            for future in as_completed(futures):
                if self.is_cancelled():
                    executor.shutdown(wait=False)
                    break

                photo, hash_val = future.result()
                self._update_progress(files_delta=1)

    def assess_quality_parallel(self):
        """Assess photo quality with parallel processing and real blur detection"""
        self._update_progress("Assessing photo quality (parallel)")

        self.progress.total_files = len(self.all_files)
        self.progress.files_processed = 0
        self.progress.start_time = datetime.now()

        def assess_photo(photo: PhotoFile) -> Tuple[PhotoFile, Optional[ProcessingIssue]]:
            """Assess a single photo"""
            if self.is_cancelled():
                return photo, None

            # Check file size
            size_kb = photo.size / 1024
            if size_kb < self.MIN_FILE_SIZE_KB:
                issue = ProcessingIssue(
                    category='too_small',
                    files=[photo],
                    description=f"File size only {size_kb:.1f} KB"
                )
                return photo, issue

            # Get dimensions
            try:
                if self.exiftool_path:
                    result = subprocess.run(
                        [self.exiftool_path, '-ImageWidth', '-ImageHeight', '-s3', str(photo.path)],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5
                    )
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2 and lines[0].isdigit() and lines[1].isdigit():
                        photo.width = int(lines[0])
                        photo.height = int(lines[1])

                        if photo.width * photo.height < self.MIN_RESOLUTION:
                            issue = ProcessingIssue(
                                category='too_small',
                                files=[photo],
                                description=f"Low resolution: {photo.width}x{photo.height}"
                            )
                            return photo, issue
            except Exception as e:
                self.logger.error(f"Error getting dimensions for {photo.path}: {e}")
                photo.is_corrupted = True
                issue = ProcessingIssue(
                    category='blur_corrupt',
                    files=[photo],
                    description="Corrupted or unreadable file"
                )
                return photo, issue

            # Blur detection with OpenCV
            if OPENCV_AVAILABLE and photo.path.suffix.lower() in self.IMAGE_EXTENSIONS:
                try:
                    is_blurry, blur_score = self.detect_blur_opencv(photo.path)
                    photo.is_blurry = is_blurry
                    photo.blur_score = blur_score

                    if is_blurry:
                        issue = ProcessingIssue(
                            category='blur_corrupt',
                            files=[photo],
                            description=f"Blurry (score: {blur_score:.1f})"
                        )
                        return photo, issue
                except Exception as e:
                    self.logger.error(f"Error detecting blur for {photo.path}: {e}")

            return photo, None

        # Process in parallel
        issues_found = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(assess_photo, photo): photo for photo in self.all_files}

            for future in as_completed(futures):
                if self.is_cancelled():
                    executor.shutdown(wait=False)
                    break

                photo, issue = future.result()
                if issue:
                    issues_found.append(issue)
                    if issue.category == 'too_small':
                        self.stats['too_small_found'] += 1
                    elif issue.category == 'blur_corrupt':
                        if photo.is_blurry:
                            self.stats['blurry_found'] += 1
                        else:
                            self.stats['corrupted_found'] += 1

                self._update_progress(files_delta=1)

        # Add issues to main list
        self.issues.extend(issues_found)

    def _select_best_photo(self, photos: List[PhotoFile]) -> PhotoFile:
        """Select the best photo with blur score consideration"""
        for photo in photos:
            score = 0.0

            # File size
            score += photo.size / 1024 / 1024

            # Resolution
            score += (photo.width * photo.height) / 1000000

            # Blur score (if available)
            if photo.blur_score is not None:
                score += photo.blur_score / 100  # Normalize

            # Has JSON
            if photo.has_json:
                score += 10

            # Not blurry
            if not photo.is_blurry:
                score += 5

            photo.quality_score = score

        return max(photos, key=lambda p: p.quality_score)

    def run_full_pipeline(self):
        """Run the complete enhanced processing pipeline"""
        try:
            self.progress.start_time = datetime.now()
            self.progress.current_step_num = 0

            # Step 1
            self.progress.current_step_num = 1
            self.setup_folder_structure()

            # Step 2
            self.progress.current_step_num = 2
            extracted = self.extract_takeouts()
            if extracted > 0:
                self._update_progress(f"Extracted {extracted} archive(s)")

            # Step 3
            self.progress.current_step_num = 3
            self.scan_files()
            self._update_progress(f"Found {len(self.all_files)} media files")

            # Step 4
            self.progress.current_step_num = 4
            self.restore_metadata()

            # Step 5 - Parallel hashing
            self.progress.current_step_num = 5
            if not self.is_cancelled():
                self.calculate_hashes_parallel()

            # Step 6
            self.progress.current_step_num = 6
            if not self.is_cancelled():
                self.find_duplicates()

            # Step 7 - Parallel quality assessment with blur detection
            self.progress.current_step_num = 7
            if not self.is_cancelled():
                self.assess_quality_parallel()

            # Step 8
            self.progress.current_step_num = 8
            if not self.is_cancelled():
                self.group_bursts()

            # Step 9
            self.progress.current_step_num = 9
            if not self.is_cancelled():
                self.organize_files()

            if self.is_cancelled():
                self._update_progress("Processing cancelled")
                self.logger.info("Processing cancelled by user")
            else:
                self._update_progress("Processing complete!")
                self.logger.info("Processing completed successfully")

            return self.stats, self.issues

        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {e}", exc_info=True)
            raise

    # Import remaining methods from original PhotoProcessor
    # (setup_folder_structure, extract_takeouts, scan_files, etc.)
    # For brevity, I'll note these should be copied from the original file

    def setup_folder_structure(self):
        """Create folder structure - same as original"""
        self._update_progress("Setting up folder structure")
        self.photos_videos_dir.mkdir(parents=True, exist_ok=True)
        self.takeout_dir.mkdir(parents=True, exist_ok=True)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        for dir_path in self.review_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    # ... (Other methods from original PhotoProcessor should be included here)
    # For the complete implementation, copy all methods from PhotoProcessor.py
