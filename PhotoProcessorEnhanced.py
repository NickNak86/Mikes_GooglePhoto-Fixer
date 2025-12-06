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
        Initialize enhanced processor with input validation and health check

        Args:
            base_path: Root directory
            exiftool_path: Path to exiftool executable
            max_workers: Number of threads for parallel processing
        """
        # Input validation
        if not base_path or not isinstance(base_path, str):
            raise ValueError("base_path must be a non-empty string")
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")
        if not self.base_path.is_dir():
            raise NotADirectoryError(f"Base path is not a directory: {self.base_path}")
        if not isinstance(max_workers, int) or max_workers < 1:
            raise ValueError("max_workers must be a positive integer")

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

    def self_test(self) -> Dict[str, str]:
        """
        Health/self-healing check for required directories, dependencies, and log writability.
        Returns a dict of health check results.
        """
        results = {}
        # Check base path
        if not self.base_path.exists():
            results['base_path'] = 'FAIL: Base path does not exist.'
        elif not self.base_path.is_dir():
            results['base_path'] = 'FAIL: Base path is not a directory.'
        else:
            results['base_path'] = 'OK'

        # Check log directory
        log_dir = self.base_path / "logs"
        try:
            log_dir.mkdir(exist_ok=True)
            test_file = log_dir / "health_test.log"
            with open(test_file, "w") as f:
                f.write("health test")
            test_file.unlink()
            results['log_dir'] = 'OK'
        except Exception as e:
            results['log_dir'] = f'FAIL: Log dir not writable: {e}'

        # Check review directories
        for key, dir_path in self.review_dirs.items():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                results[f'review_dir_{key}'] = 'OK'
            except Exception as e:
                results[f'review_dir_{key}'] = f'FAIL: {e}'

        # Check OpenCV
        if OPENCV_AVAILABLE:
            results['opencv'] = 'OK'
        else:
            results['opencv'] = 'FAIL: OpenCV not available.'

        # Check exiftool
        if self.exiftool_path and (os.path.exists(self.exiftool_path) or shutil.which(self.exiftool_path)):
            results['exiftool'] = 'OK'
        else:
            results['exiftool'] = 'FAIL: exiftool not found.'

        # Log health check results
        for k, v in results.items():
            self.logger.info(f"Health check: {k}: {v}")
        return results

    def notify_critical_failure(self, message: str):
        """
        Notification hook for critical failures (placeholder).
        """
        self.logger.error(f"CRITICAL FAILURE: {message}")
        # TODO: Integrate with email, desktop notification, etc.

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

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
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

    def extract_takeouts(self) -> int:
        """Extract Google Takeout zip files if any exist"""
        extracted_count = 0

        if not self.takeout_dir.exists():
            return 0

        # Look for zip files in the takeout directory
        zip_files = list(self.takeout_dir.glob("*.zip"))

        for zip_path in zip_files:
            try:
                self._update_progress(f"Extracting {zip_path.name}")
                self.logger.info(f"Extracting takeout archive: {zip_path}")

                # Create extraction directory
                extract_dir = self.takeout_dir / zip_path.stem
                extract_dir.mkdir(exist_ok=True)

                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                extracted_count += 1
                self.logger.info(f"Successfully extracted {zip_path.name}")

                # Optionally move the original zip to avoid re-extracting
                archive_dir = self.takeout_dir / "archives"
                archive_dir.mkdir(exist_ok=True)
                shutil.move(str(zip_path), str(archive_dir / zip_path.name))

            except Exception as e:
                self.logger.error(f"Failed to extract {zip_path.name}: {e}")
                self.issues.append(f"Failed to extract {zip_path.name}: {str(e)}")

        return extracted_count


    def scan_files(self):
        """
        Scan all relevant directories for photo/video files and associated JSON metadata.
        - Recursively walk the Photos & Videos and GoogleTakeout directories.
        - For each file, create a PhotoFile object, link JSON if present, and append to self.all_files.
        - Update progress and handle cancellation.
        """
        self._update_progress("Scanning for media files")
        self.all_files = []
        
        # Scan both source directories
        scan_dirs = []
        if self.photos_videos_dir.exists():
            scan_dirs.append(self.photos_videos_dir)
        if self.takeout_dir.exists():
            scan_dirs.append(self.takeout_dir)
        
        for scan_dir in scan_dirs:
            if self.is_cancelled():
                break
                
            self.logger.info(f"Scanning directory: {scan_dir}")
            
            for root, dirs, files in os.walk(scan_dir):
                if self.is_cancelled():
                    break
                    
                for filename in files:
                    if self.is_cancelled():
                        break
                        
                    file_path = Path(root) / filename
                    file_ext = file_path.suffix.lower()
                    
                    # Check if it's a media file
                    if file_ext in self.IMAGE_EXTENSIONS or file_ext in self.VIDEO_EXTENSIONS:
                        photo = PhotoFile(path=file_path)
                        
                        # Check for associated JSON metadata file
                        json_path = file_path.parent / f"{file_path.name}.json"
                        if json_path.exists():
                            photo.has_json = True
                            photo.json_path = json_path
                        
                        self.all_files.append(photo)
                        self._update_progress(files_delta=1)
        
        self.logger.info(f"Found {len(self.all_files)} media files")
        self.stats['total_processed'] = len(self.all_files)

    def restore_metadata(self):
        """
        Restore/correct file timestamps and metadata using JSON sidecars and exiftool.
        - For each PhotoFile with a JSON, parse date fields and update file timestamps.
        - Use exiftool to write correct EXIF data if available.
        - Log any failures or skipped files.
        """
        self._update_progress("Restoring metadata from JSON files")
        
        files_with_json = [f for f in self.all_files if f.has_json and f.json_path]
        self.progress.total_files = len(files_with_json)
        self.progress.files_processed = 0
        
        for photo in files_with_json:
            if self.is_cancelled():
                break
                
            try:
                # Read JSON metadata
                with open(photo.json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Extract date taken from JSON
                date_taken = None
                if 'photoTakenTime' in metadata:
                    timestamp = metadata['photoTakenTime'].get('timestamp')
                    if timestamp:
                        date_taken = datetime.fromtimestamp(int(timestamp))
                elif 'creationTime' in metadata:
                    timestamp = metadata['creationTime'].get('timestamp')
                    if timestamp:
                        date_taken = datetime.fromtimestamp(int(timestamp))
                
                if date_taken:
                    photo.date_taken = date_taken
                    
                    # Update file timestamps
                    timestamp = date_taken.timestamp()
                    os.utime(photo.path, (timestamp, timestamp))
                    
                    # Use exiftool to write EXIF data if available
                    if self.exiftool_path:
                        try:
                            date_str = date_taken.strftime('%Y:%m:%d %H:%M:%S')
                            subprocess.run(
                                [self.exiftool_path, f'-DateTimeOriginal={date_str}',
                                 '-overwrite_original', str(photo.path)],
                                capture_output=True,
                                timeout=10,
                                check=False
                            )
                        except Exception as e:
                            self.logger.warning(f"Failed to write EXIF for {photo.path}: {e}")
                
                self._update_progress(files_delta=1)
                
            except Exception as e:
                self.logger.error(f"Failed to restore metadata for {photo.path}: {e}")
        
        self.logger.info(f"Restored metadata for {self.progress.files_processed} files")

    def find_duplicates(self):
        """
        Detect duplicate files by hash and group them.
        - Build a hash-to-PhotoFile mapping.
        - For each group with >1 file, create a ProcessingIssue (category='duplicates').
        - Use _select_best_photo to recommend which to keep.
        - Update stats and self.issues.
        """
        self._update_progress("Finding duplicate files")
        
        # Build hash map
        hash_map = defaultdict(list)
        for photo in self.all_files:
            if photo.hash:
                hash_map[photo.hash].append(photo)
        
        # Find duplicates
        duplicate_groups = {h: photos for h, photos in hash_map.items() if len(photos) > 1}
        
        self.logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        
        for file_hash, photos in duplicate_groups.items():
            if self.is_cancelled():
                break
                
            # Select best photo to keep
            best_photo = self._select_best_photo(photos)
            
            issue = ProcessingIssue(
                category='duplicates',
                files=photos,
                recommended_keep=best_photo,
                group_id=file_hash[:8],
                description=f"Found {len(photos)} duplicate files"
            )
            self.issues.append(issue)
            self.stats['duplicates_found'] += len(photos) - 1
        
        self.logger.info(f"Total duplicate files: {self.stats['duplicates_found']}")

    def group_bursts(self):
        """
        Group burst photos (taken within a short time window) and flag for review.
        - Sort files by date_taken.
        - Group files within BURST_TIME_THRESHOLD seconds.
        - For each group, create a ProcessingIssue (category='burst').
        - Recommend best photo in each burst.
        """
        self._update_progress("Grouping burst photos")
        
        # Filter files with valid date_taken
        dated_files = [f for f in self.all_files if f.date_taken and not f.is_corrupted]
        dated_files.sort(key=lambda x: x.date_taken)
        
        # Group bursts
        burst_groups = []
        current_burst = []
        
        for i, photo in enumerate(dated_files):
            if self.is_cancelled():
                break
                
            if not current_burst:
                current_burst.append(photo)
            else:
                time_diff = (photo.date_taken - current_burst[-1].date_taken).total_seconds()
                
                if time_diff <= self.BURST_TIME_THRESHOLD:
                    current_burst.append(photo)
                else:
                    # Save burst if it has multiple photos
                    if len(current_burst) > 1:
                        burst_groups.append(current_burst)
                    current_burst = [photo]
        
        # Don't forget last burst
        if len(current_burst) > 1:
            burst_groups.append(current_burst)
        
        self.logger.info(f"Found {len(burst_groups)} burst photo groups")
        
        # Create issues for each burst
        for burst in burst_groups:
            if self.is_cancelled():
                break
                
            best_photo = self._select_best_photo(burst)
            
            issue = ProcessingIssue(
                category='burst',
                files=burst,
                recommended_keep=best_photo,
                description=f"Burst of {len(burst)} photos taken within {self.BURST_TIME_THRESHOLD}s"
            )
            self.issues.append(issue)
            self.stats['bursts_found'] += 1
        
        self.logger.info(f"Total burst groups: {self.stats['bursts_found']}")

    def organize_files(self):
        """
        Move/copy files to their final destinations and sort into review folders as needed.
        - For each file, decide if it goes to the main library or a review folder (too small, blurry, duplicate, burst, etc.).
        - Move/copy files, update stats, and log actions.
        - Handle errors and update progress.
        """
        self._update_progress("Organizing files")
        
        # Build set of files that need review
        review_files = set()
        for issue in self.issues:
            for photo in issue.files:
                # Don't move the recommended keeper to review
                if issue.recommended_keep and photo.path == issue.recommended_keep.path:
                    continue
                review_files.add(photo.path)
        
        self.progress.total_files = len(self.all_files)
        self.progress.files_processed = 0
        
        for photo in self.all_files:
            if self.is_cancelled():
                break
                
            try:
                # Determine destination
                if photo.path in review_files:
                    # Find which review folder
                    dest_dir = None
                    for issue in self.issues:
                        if photo in issue.files:
                            if issue.category == 'too_small':
                                dest_dir = self.review_dirs['too_small']
                            elif issue.category == 'blur_corrupt':
                                dest_dir = self.review_dirs['blur_corrupt']
                            elif issue.category == 'duplicates':
                                dest_dir = self.review_dirs['duplicates']
                            elif issue.category == 'burst':
                                dest_dir = self.review_dirs['burst']
                            break
                    
                    if dest_dir:
                        dest_path = dest_dir / photo.path.name
                        # Handle name conflicts
                        counter = 1
                        while dest_path.exists():
                            stem = photo.path.stem
                            suffix = photo.path.suffix
                            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                            counter += 1
                        
                        shutil.copy2(photo.path, dest_path)
                        
                        # Also copy JSON if present
                        if photo.has_json and photo.json_path and photo.json_path.exists():
                            json_dest = dest_path.parent / f"{dest_path.name}.json"
                            shutil.copy2(photo.json_path, json_dest)
                        
                        self.logger.info(f"Moved to review: {photo.path.name} -> {dest_dir.name}")
                else:
                    # Move to main library organized by date
                    if photo.date_taken:
                        year_month = photo.date_taken.strftime('%Y-%m')
                        dest_dir = self.photos_videos_dir / year_month
                    else:
                        dest_dir = self.photos_videos_dir / "Unknown Date"
                    
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest_path = dest_dir / photo.path.name
                    
                    # Handle name conflicts
                    counter = 1
                    while dest_path.exists():
                        stem = photo.path.stem
                        suffix = photo.path.suffix
                        dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    # Only move if not already in destination
                    if photo.path.parent != dest_dir:
                        shutil.move(str(photo.path), str(dest_path))
                        
                        # Also move JSON if present
                        if photo.has_json and photo.json_path and photo.json_path.exists():
                            json_dest = dest_path.parent / f"{dest_path.name}.json"
                            shutil.move(str(photo.json_path), str(json_dest))
                        
                        self.stats['moved_to_library'] += 1
                        self.logger.debug(f"Moved to library: {photo.path.name} -> {dest_dir}")
                
                self._update_progress(files_delta=1)
                
            except Exception as e:
                self.logger.error(f"Failed to organize {photo.path}: {e}")
        
        self.logger.info(f"Organized {self.progress.files_processed} files")

    def process(self):
        """
        Main entry point for the processing pipeline (for CLI and GUI).
        - Calls run_full_pipeline and returns stats, issues.
        - Handles exceptions and logs errors.
        """
        return self.run_full_pipeline()


def main():
    """CLI entry point for Google Photos Processor"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Google Photos Processor - Organize and deduplicate photos from Google Takeout"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Base directory for processing (will create Photos & Videos, GoogleTakeout, etc. subdirectories)"
    )
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=4,
        help="Number of processing threads (default: 4)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--exiftool",
        help="Path to exiftool executable (auto-detected if not specified)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup paths
    base_dir = Path(args.input).resolve()
    if not base_dir.exists():
        print(f"ERROR: Input directory does not exist: {base_dir}")
        return 1
    
    print(f"\n{'='*60}")
    print(f"Google Photos Processor v2.1")
    print(f"{'='*60}")
    print(f"Base Directory: {base_dir}")
    print(f"Threads: {args.threads}")
    print(f"{'='*60}\n")
    
    # Create processor
    processor = PhotoProcessorEnhanced(
        base_path=str(base_dir),
        exiftool_path=args.exiftool,
        max_workers=args.threads
    )
    
    # Setup progress callback
    def print_progress(progress: ProcessingProgress):
        percent = progress.percent_complete()
        eta = progress.calculate_eta()
        eta_str = f" ETA: {eta}" if eta else ""
        
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        status = f"{progress.current_step} [{progress.files_processed}/{progress.total_files}]"
        print(f"\r{bar} {percent:.1f}% {status}{eta_str}", end='', flush=True)
    
    processor.progress_callback = print_progress
    
    try:
        # Run processing
        stats, issues = processor.process()
        
        print(f"\n\n{'='*60}")
        print("Processing Complete!")
        print(f"{'='*60}")
        print(f"Files processed: {stats.get('files_processed', 0)}")
        print(f"Duplicates found: {stats.get('duplicates', 0)}")
        print(f"Issues found: {len(issues)}")
        
        if issues:
            print(f"\nIssues:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"  - {issue}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
        
        print(f"\nOutput saved to: {base_dir}")
        print(f"{'='*60}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nProcessing cancelled by user")
        return 130
    except Exception as e:
        print(f"\n\nERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
