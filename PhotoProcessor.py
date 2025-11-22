"""
PhotoProcessor - Compatibility module
=====================================
This module provides backwards compatibility by re-exporting
classes from PhotoProcessorEnhanced.

Author: Claude Code
Date: 2025-11-21
"""

from PhotoProcessorEnhanced import PhotoProcessorEnhanced as PhotoProcessor
from PhotoProcessorEnhanced import ProcessingIssue, ProcessingProgress

__all__ = ['PhotoProcessor', 'ProcessingIssue', 'ProcessingProgress']
