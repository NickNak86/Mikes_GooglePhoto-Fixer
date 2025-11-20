# Changelog

All notable changes to Google Photos Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- iOS support via Kivy
- Cloud sync with Google Drive
- Progressive Web App (PWA) version
- Multi-device review (family sharing)
- Automatic update checker
- Custom blur detection thresholds in settings
- Batch photo editing capabilities

## [2.1.0] - 2025-11-20

### Added
- 🚀 **Mobile Application** - Complete Android app with Material Design
  - Kivy/KivyMD-based cross-platform mobile UI
  - Touch-optimized review interface
  - Android storage permissions handling
  - Real-time progress tracking with ETA
  - Material Design Dark Mode theme
- 🎨 **Enhanced Desktop UI** - Material Design Dark Mode
  - Modern, cohesive interface matching mobile app
  - Improved visual hierarchy
  - Better progress indicators
- 🧵 **Parallel Processing** - Multi-threaded operations
  - Parallel hash calculation
  - Parallel quality assessment
  - Configurable worker threads (2-4)
- 🔍 **Real Blur Detection** - OpenCV-based analysis
  - Laplacian variance calculation
  - Configurable blur threshold
  - Blur score for each image
- 📊 **Progress Tracking** - Detailed progress monitoring
  - Step-by-step progress indication
  - ETA calculation
  - File count tracking
  - Bytes processed tracking
- ⏸️ **Cancellation Support** - User-controlled processing
  - Cancel button in UI
  - Clean shutdown on cancellation
  - Thread-safe cancel mechanism
- 📱 **Mobile Platform Utilities**
  - Platform detection (Android vs Desktop)
  - Permission management
  - Platform-specific storage paths
  - Configuration management
- 🏗️ **Build System**
  - Buildozer configuration for Android APK
  - Multi-architecture support (arm64-v8a, armeabi-v7a)
  - Automated build workflow ready

### Changed
- ♻️ **Refactored Backend** - PhotoProcessorEnhanced
  - Cleaner separation of concerns
  - Better error handling
  - Improved logging
  - Thread-safe operations
- 📝 **Enhanced Documentation**
  - Comprehensive mobile architecture guide
  - Detailed build instructions
  - Implementation summary
  - Setup guide for public release
- 🎯 **Quality Selection** - Improved best photo algorithm
  - Considers blur score
  - Weights multiple quality factors
  - Better duplicate ranking

### Fixed
- 🐛 Bug fixes in duplicate detection edge cases
- 🐛 Memory leak in parallel processing
- 🐛 Proper cleanup of temporary files
- 🐛 Date parsing for various formats

## [2.0.0] - 2025-11-15

### Added
- 🖼️ **Review Interface** - DupeGuru-style photo review
  - Visual preview of flagged photos
  - Group-based review workflow
  - Quick actions (keep best, keep all, delete all)
  - Progress tracking through review sessions
- 🔄 **Burst Photo Detection** - Automatic grouping
  - Time-based grouping (10-second threshold)
  - Quality ranking within bursts
  - Recommended photo selection
- 🎯 **Quality Assessment** - Multi-factor analysis
  - File size checking
  - Resolution validation
  - Basic blur detection (file-based)
  - Corruption detection
- 📂 **Organized Structure** - Review folders
  - Separate folders for different issue types
  - BEST_ prefix for recommended photos
  - Group folders for duplicates and bursts
  - Hierarchical organization

### Changed
- 🏗️ **Architecture Improvements**
  - Dataclass-based models
  - Better type hints
  - Cleaner code organization
- 📊 **Statistics Tracking**
  - Detailed processing statistics
  - Issue categorization
  - Count tracking per category

## [1.0.0] - 2025-11-10

### Added
- ✨ **Initial Release** - Core functionality
  - Google Takeout ZIP extraction
  - Metadata restoration from JSON files
  - Duplicate detection via file hashing
  - Date-based photo organization
  - Folder structure creation
- 🖥️ **Desktop GUI** - tkinter-based interface
  - Settings dialog for configuration
  - Processing progress indicator
  - Status messages
  - Basic error handling
- 📅 **Date Organization**
  - Year/Month folder structure
  - EXIF date extraction
  - Fallback to file dates
- 🔧 **ExifTool Integration**
  - Metadata reading
  - Date extraction
  - Dimension detection
- 📝 **Logging System**
  - File-based logging
  - Console output
  - Error tracking

### Technical Details
- Python 3.9+ requirement
- Pillow for image processing
- tkinter for desktop GUI
- ExifTool for metadata

## Development Versions

### [0.9.0] - 2025-11-05 (Beta)
- Beta testing with sample dataset
- Bug fixes and performance improvements
- Documentation improvements

### [0.5.0] - 2025-11-01 (Alpha)
- Initial prototype
- Basic processing pipeline
- Command-line interface
- Manual review workflow

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

## Links

- [GitHub Repository](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer)
- [Issue Tracker](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
- [Releases](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/releases)

[Unreleased]: https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/releases/tag/v2.1.0
[2.0.0]: https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/releases/tag/v2.0.0
[1.0.0]: https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/releases/tag/v1.0.0
