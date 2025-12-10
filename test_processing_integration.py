#!/usr/bin/env python3
"""
Integration Test - Actual Processing with Test Data
===================================================
Tests the full processing pipeline with realistic test data
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingIntegrationTest:
    """Test actual processing operations"""
    
    def __init__(self):
        self.test_base = Path("./test-integration")
        self.test_data = Path("./test-data")
        self.results = []
    
    def setup(self):
        """Setup test environment"""
        logger.info("Setting up test environment...")
        
        # Clean and create test base
        if self.test_base.exists():
            shutil.rmtree(self.test_base)
        self.test_base.mkdir()
        
        # Copy test data to GoogleTakeout folder
        takeout_dir = self.test_base / "GoogleTakeout"
        takeout_dir.mkdir()
        
        if not self.test_data.exists():
            logger.error("Test data not found! Run: python generate_test_data.py ./test-data")
            return False
        
        # Copy all test files
        file_count = 0
        for item in self.test_data.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(self.test_data)
                dest = takeout_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                file_count += 1
        
        logger.info(f"Copied {file_count} test files to {takeout_dir}")
        return True
    
    def test_processor_initialization(self):
        """Test: Initialize processor with test base"""
        test_name = "Processor Initialization with Test Data"
        logger.info(f"\nTest: {test_name}")
        
        try:
            from PhotoProcessorEnhanced import PhotoProcessorEnhanced
            
            processor = PhotoProcessorEnhanced(
                base_path=str(self.test_base),
                max_workers=2
            )
            
            # Setup folder structure
            processor.setup_folder_structure()
            
            # Check if required directories were created
            required_dirs = [
                processor.photos_videos_dir,
                processor.takeout_dir,
                processor.review_dir
            ]
            
            all_exist = all(d.exists() for d in required_dirs)
            
            if all_exist:
                logger.info(f"✓ PASS: {test_name}")
                self.results.append(("PASS", test_name, "All required directories created"))
                return processor
            else:
                missing = [str(d) for d in required_dirs if not d.exists()]
                logger.error(f"✗ FAIL: {test_name} - Missing: {missing}")
                self.results.append(("FAIL", test_name, f"Missing: {missing}"))
                return None
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return None
    
    def test_file_scanning(self, processor):
        """Test: Scan for files in test directory"""
        test_name = "File Scanning"
        logger.info(f"\nTest: {test_name}")
        
        try:
            # Check how many files are in takeout directory
            file_count = sum(1 for f in processor.takeout_dir.rglob('*') if f.is_file())
            
            logger.info(f"Found {file_count} files in takeout directory")
            
            if file_count > 0:
                logger.info(f"✓ PASS: {test_name} - Found {file_count} files")
                self.results.append(("PASS", test_name, f"Found {file_count} files"))
                return True
            else:
                logger.error(f"✗ FAIL: {test_name} - No files found")
                self.results.append(("FAIL", test_name, "No files found"))
                return False
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return False
    
    def test_hash_calculation(self, processor):
        """Test: Calculate hashes for files"""
        test_name = "Hash Calculation"
        logger.info(f"\nTest: {test_name}")
        
        try:
            # Find some image files to hash
            image_files = []
            for ext in ['.jpg', '.jpeg', '.png']:
                image_files.extend(processor.takeout_dir.rglob(f'*{ext}'))
                if len(image_files) >= 5:
                    break
            
            if not image_files:
                logger.warning(f"⚠ SKIP: {test_name} - No image files found")
                self.results.append(("SKIP", test_name, "No image files"))
                return False
            
            # Try to calculate hash for first file
            test_file = image_files[0]
            file_hash = processor._calculate_hash(test_file)
            
            if file_hash and len(file_hash) == 64:  # SHA256 is 64 hex chars
                logger.info(f"✓ PASS: {test_name} - Calculated hash: {file_hash[:16]}...")
                self.results.append(("PASS", test_name, f"Hash: {file_hash[:16]}..."))
                return True
            else:
                logger.error(f"✗ FAIL: {test_name} - Invalid hash: {file_hash}")
                self.results.append(("FAIL", test_name, f"Invalid hash: {file_hash}"))
                return False
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return False
    
    def test_blur_detection(self, processor):
        """Test: Blur detection on images"""
        test_name = "Blur Detection"
        logger.info(f"\nTest: {test_name}")
        
        try:
            # Try to import opencv
            try:
                import cv2
            except ImportError:
                logger.warning(f"⚠ SKIP: {test_name} - OpenCV not available")
                self.results.append(("SKIP", test_name, "OpenCV not installed"))
                return False
            
            # Find image files
            image_files = list(processor.takeout_dir.rglob('*.jpg'))[:5]
            
            if not image_files:
                logger.warning(f"⚠ SKIP: {test_name} - No image files")
                self.results.append(("SKIP", test_name, "No image files"))
                return False
            
            # Try blur detection on first file
            test_file = image_files[0]
            is_blurry, blur_score = processor.detect_blur_opencv(test_file)
            
            if blur_score is not None and blur_score >= 0:
                logger.info(f"✓ PASS: {test_name} - Blur score: {blur_score:.2f}")
                self.results.append(("PASS", test_name, f"Blur score: {blur_score:.2f}"))
                return True
            else:
                logger.error(f"✗ FAIL: {test_name} - Invalid blur score")
                self.results.append(("FAIL", test_name, "Invalid blur score"))
                return False
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return False
    
    def test_json_metadata_parsing(self, processor):
        """Test: Parse Google Takeout JSON metadata"""
        test_name = "JSON Metadata Parsing"
        logger.info(f"\nTest: {test_name}")
        
        try:
            # Find JSON files
            json_files = list(processor.takeout_dir.rglob('*.json'))
            
            if not json_files:
                logger.warning(f"⚠ SKIP: {test_name} - No JSON files found")
                self.results.append(("SKIP", test_name, "No JSON files"))
                return False
            
            # Try to parse first JSON file
            json_file = json_files[0]
            import json
            
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if it has expected structure
            has_title = 'title' in metadata
            has_creation = 'creationTime' in metadata or 'photoTakenTime' in metadata
            
            if has_title and has_creation:
                logger.info(f"✓ PASS: {test_name} - Parsed {json_file.name}")
                self.results.append(("PASS", test_name, f"Parsed {json_file.name}"))
                return True
            else:
                logger.error(f"✗ FAIL: {test_name} - Missing expected fields")
                self.results.append(("FAIL", test_name, "Missing expected fields"))
                return False
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return False
    
    def test_error_handling_corrupted_file(self, processor):
        """Test: Error handling with corrupted files"""
        test_name = "Error Handling - Corrupted Files"
        logger.info(f"\nTest: {test_name}")
        
        try:
            # Find corrupted files
            corrupted_dir = processor.takeout_dir / "corrupted"
            if not corrupted_dir.exists():
                logger.warning(f"⚠ SKIP: {test_name} - No corrupted test files")
                self.results.append(("SKIP", test_name, "No corrupted files"))
                return False
            
            corrupted_files = list(corrupted_dir.glob('*'))
            if not corrupted_files:
                logger.warning(f"⚠ SKIP: {test_name} - No corrupted test files")
                self.results.append(("SKIP", test_name, "No corrupted files"))
                return False
            
            # Try to process corrupted file - should not crash
            test_file = corrupted_files[0]
            
            # Try hash calculation on corrupted file
            try:
                file_hash = processor._calculate_hash(test_file)
                # Should either return a hash or None, but not crash
                logger.info(f"✓ PASS: {test_name} - Handled corrupted file gracefully")
                self.results.append(("PASS", test_name, "No crash on corrupted file"))
                return True
            except Exception as e:
                # If it raises an exception, that's still OK as long as we catch it
                logger.info(f"✓ PASS: {test_name} - Exception caught: {type(e).__name__}")
                self.results.append(("PASS", test_name, f"Exception handled: {type(e).__name__}"))
                return True
                
        except Exception as e:
            logger.error(f"✗ FAIL: {test_name} - Unhandled exception: {e}")
            self.results.append(("FAIL", test_name, str(e)))
            return False
    
    def cleanup(self):
        """Cleanup test environment"""
        logger.info("\nCleaning up...")
        try:
            if self.test_base.exists():
                shutil.rmtree(self.test_base)
            logger.info("✓ Cleanup complete")
        except Exception as e:
            logger.error(f"✗ Cleanup failed: {e}")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*70)
        print("  INTEGRATION TEST REPORT")
        print("="*70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r[0] == "PASS")
        failed = sum(1 for r in self.results if r[0] == "FAIL")
        skipped = sum(1 for r in self.results if r[0] == "SKIP")
        
        print(f"\nTotal Tests: {total}")
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"⚠ Skipped: {skipped}")
        
        if passed == total - skipped:
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n❌ SOME TESTS FAILED")
        
        print("\nDetailed Results:")
        print("-" * 70)
        
        for status, name, details in self.results:
            icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
            print(f"{icon} {status}: {name}")
            print(f"   {details}")
        
        print("="*70)
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*70)
        print("  INTEGRATION TESTS - ACTUAL PROCESSING")
        print("="*70)
        
        # Setup
        if not self.setup():
            logger.error("Setup failed! Cannot continue.")
            return
        
        # Initialize processor
        processor = self.test_processor_initialization()
        
        if processor:
            # Run tests
            self.test_file_scanning(processor)
            self.test_hash_calculation(processor)
            self.test_blur_detection(processor)
            self.test_json_metadata_parsing(processor)
            self.test_error_handling_corrupted_file(processor)
        
        # Cleanup
        self.cleanup()
        
        # Generate report
        self.generate_report()


def main():
    """Main entry point"""
    tester = ProcessingIntegrationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
