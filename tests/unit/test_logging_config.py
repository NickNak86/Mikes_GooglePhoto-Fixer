"""
Unit tests for logging configuration helper.
"""

import logging
import os
import tempfile
from pathlib import Path

import pytest


class TestLoggingConfig:
    """Tests for utils.logging_config module."""

    def test_import_logging_config(self):
        """Test that the logging_config module can be imported."""
        from utils import logging_config
        assert hasattr(logging_config, 'configure_logging')

    def test_configure_logging_default(self):
        """Test logging configuration with default parameters."""
        from utils.logging_config import configure_logging
        
        # Use a temp directory for logs
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            configure_logging(log_path=log_path)
            
            # Verify log file was created
            assert os.path.exists(log_path)
            
            # Verify we can log to it
            test_logger = logging.getLogger("test_logger")
            test_logger.info("Test message")
            
            # Verify content was written
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Test message" in content

    def test_configure_logging_custom_level(self):
        """Test logging configuration with custom level."""
        from utils.logging_config import configure_logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_debug.log")
            configure_logging(log_path=log_path, level="DEBUG")
            
            # Get root logger
            logger = logging.getLogger()
            
            # Should be set to DEBUG
            assert logger.level == logging.DEBUG

    def test_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        from utils.logging_config import configure_logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "subdir", "nested", "test.log")
            
            # Directory doesn't exist yet
            assert not os.path.exists(os.path.dirname(log_path))
            
            # Configure logging (should create the directory)
            configure_logging(log_path=log_path)
            
            # Directory should now exist
            assert os.path.exists(os.path.dirname(log_path))
            assert os.path.exists(log_path)

    def test_duplicate_handler_prevention(self):
        """Test that duplicate handlers are not added on repeated calls."""
        from utils.logging_config import configure_logging
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_dup.log")
            
            # Get initial handler count
            logger = logging.getLogger()
            initial_count = len(logger.handlers)
            
            # Configure logging twice
            configure_logging(log_path=log_path)
            count_after_first = len(logger.handlers)
            
            configure_logging(log_path=log_path)
            count_after_second = len(logger.handlers)
            
            # Handler count should not increase on second call
            # (Note: in practice this test may need adjustment based on 
            # whether handlers from previous tests are still present)
            assert count_after_second == count_after_first
