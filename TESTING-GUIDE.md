# GooglePhoto-Fixer Testing Guide

## Overview

This guide explains how to test GooglePhoto-Fixer using the comprehensive testing infrastructure.

## Quick Start

### 1. Generate Test Data

Create realistic test files for testing:

```bash
python generate_test_data.py ./test-data
```

This creates:
- 10 good photos (various formats and resolutions)
- 5 sets of duplicates (20 files)
- 5 blurry photos
- 3 corrupted files
- 10 burst photos
- 3 video placeholders
- 8 Google Takeout format photos with JSON
- 5 edge case files

**Total:** 72 test files in organized subdirectories.

### 2. Run Automated Tests

Run the comprehensive test suite:

```bash
python run_all_tests.py --test-data ./test-data --base-path ./test-output --clean
```

**Options:**
- `--test-data DIR` - Path to test data directory (default: ./test-data)
- `--base-path DIR` - Path for test processing (default: ./test-output)
- `--clean` - Clean output directory before running

**Output:**
- Console: Real-time test results
- `TEST-REPORT.md` - Detailed test report
- `test_runner.log` - Full test execution log

### 3. Manual Testing

#### Test Web Interface

```bash
python PhotoManagerWeb.py
```

**Access:** http://localhost:5000

**Test Scenarios:**

1. **Invalid Base Path:**
   - Set base path to non-existent directory
   - Click "Organize My Photos"
   - **Expected:** Clear error in Activity Log: "Directory not found: /path/to/dir"

2. **Permission Errors:**
   - Set base path to read-only directory
   - Click "Organize My Photos"
   - **Expected:** "Permission denied" error with helpful tip

3. **Empty Directory:**
   - Set base path to empty directory
   - Click "Organize My Photos"
   - **Expected:** Completes successfully, reports 0 files processed

4. **With Test Data:**
   - Copy test-data/* to base_path/GoogleTakeout/
   - Click "Organize My Photos"
   - **Expected:** Processing completes, files organized, Activity Log shows progress

#### Check Logging

All operations are logged to `photo_manager_web.log`:

```bash
# Watch logs in real-time
tail -f photo_manager_web.log

# Check for errors
grep ERROR photo_manager_web.log

# Check for warnings
grep WARNING photo_manager_web.log
```

## Test Data Structure

```
test-data/
├── good_photos/          # 10 normal photos
│   ├── IMG_*.jpg
│   ├── IMG_*.png
│   └── IMG_*.jpeg
├── duplicates/           # 5 sets of duplicates
│   ├── original_*.jpg
│   ├── copy_of_*.jpg
│   ├── compressed_*.jpg
│   └── resized_*.jpg
├── blurry/              # 5 blurry photos
│   └── blurry_*.jpg
├── corrupted/           # 3 corrupted files
│   ├── zero_byte.jpg
│   ├── truncated.jpg
│   └── invalid_header.jpg
├── burst/               # 10 burst sequence
│   └── IMG_20230815_164530_*.jpg
├── videos/              # 3 video placeholders
│   ├── video_*.mp4
│   ├── video_*.mov
│   └── video_*.avi
├── google_takeout/      # 8 photos + JSON
│   ├── IMG_20230920_*.jpg
│   └── IMG_20230920_*.jpg.json
└── edge_cases/          # 5 edge cases
    ├── no_extension_file
    ├── file with spaces & special (chars).jpg
    ├── photo_日本語_émojis_😀.jpg
    ├── tiny_image.jpg
    └── low_resolution.jpg
```

## Automated Tests

### Current Tests

1. **Import PhotoProcessor** - Module loads successfully
2. **Initialize PhotoProcessor** - Can create instance with valid path
3. **Invalid base path handling** - Rejects non-existent paths
4. **Setup folder structure** - Creates required directories
5. **Web interface import** - PhotoManagerWeb loads
6. **Config file handling** - Can read/write JSON config
7. **Empty directory handling** - No crash on empty directory
8. **Copy test data** - Can copy files for processing
9. **Scan files** - Can scan directory for photos

### Test Report Format

After running tests, check `TEST-REPORT.md`:

```markdown
# Google Photos Manager - Test Report

**Generated:** 2025-12-10 11:12:33

## Summary
- **Total Tests:** 10
- **Passed:** 10 (100.0%)
- **Failed:** 0 (0.0%)

## Test Results

### ✅ Import PhotoProcessor
- **Result:** PASS
- **Timestamp:** 2025-12-10T11:12:32.657292
- **Details:** Successfully imported PhotoProcessorEnhanced

...
```

## Error Handling Tests

### Test Invalid Directory

```python
# This should fail gracefully with clear error
python -c "
from PhotoProcessorEnhanced import PhotoProcessorEnhanced
try:
    p = PhotoProcessorEnhanced('/nonexistent/path')
except FileNotFoundError as e:
    print('✓ Correctly caught:', e)
"
```

### Test Permission Error

```bash
# Create read-only directory
mkdir -p /tmp/readonly_test
chmod 444 /tmp/readonly_test

# Try to process it
python -c "
from PhotoProcessorEnhanced import PhotoProcessorEnhanced
try:
    p = PhotoProcessorEnhanced('/tmp/readonly_test')
    # Try to create subdirectory
    (p.base_path / 'test').mkdir()
except PermissionError as e:
    print('✓ Correctly caught:', e)
"

# Cleanup
chmod 755 /tmp/readonly_test
rm -rf /tmp/readonly_test
```

## Web Interface Testing

### Test API Endpoints

```bash
# Start server
python PhotoManagerWeb.py &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test settings endpoint
curl -X GET http://localhost:5000/api/settings

# Test invalid settings
curl -X POST http://localhost:5000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"base_path": "/nonexistent/path"}'
# Expected: {"success": false, "error": "Directory does not exist: /nonexistent/path"}

# Test status endpoint
curl -X GET http://localhost:5000/api/status

# Stop server
kill $SERVER_PID
```

### Test Error Scenarios

1. **Start processing with no base path:**
   - Clear config.json or set empty base_path
   - Click "Organize My Photos"
   - **Expected:** Error message: "No base path configured. Please set base path in settings first."

2. **Start processing while already processing:**
   - Start a long operation
   - Try to start another
   - **Expected:** 409 error: "Already processing"

3. **Review non-existent photos:**
   - Navigate to /review
   - No review directory exists
   - **Expected:** "No photos to review" message

## Logging Verification

### Check Activity Log Updates

The Activity Log should show:
- ✓ Operation started
- ✓ Current step
- ✓ Progress updates
- ✗ Errors with details
- ✓ Operation complete

### Check Log Files

**photo_manager_web.log:**
```
2025-12-10 11:12:32,099 - __main__ - INFO - Starting photo processing workflow
2025-12-10 11:12:32,099 - __main__ - INFO - Using base path: /path/to/test
2025-12-10 11:12:32,100 - __main__ - INFO - Initializing photo processor...
...
2025-12-10 11:12:45,678 - __main__ - ERROR - Processing failed with exception:
Traceback (most recent call last):
  ...
```

## Performance Testing

### Small Dataset (72 files)
```bash
time python run_all_tests.py
```
**Expected:** < 5 seconds

### Medium Dataset (1000 files)
```bash
# Generate more test data
for i in {1..14}; do
  python generate_test_data.py ./test-data-large
done

# Process it
python run_all_tests.py --test-data ./test-data-large --base-path ./test-output-large
```

### Large Dataset (Real Data)
```bash
# User's actual photos (do this manually)
# Set base_path to actual photo directory
# Monitor memory usage and processing time
```

## Troubleshooting

### Tests Fail

1. Check `test_runner.log` for details
2. Look for ERROR entries
3. Fix issue and re-run specific test

### No Test Data

```bash
# Regenerate test data
rm -rf test-data
python generate_test_data.py ./test-data
```

### Web Server Won't Start

```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing process
kill $(lsof -t -i :5000)

# Check logs
tail -20 photo_manager_web.log
```

### Permission Errors

```bash
# Make sure test directories are writable
chmod -R 755 test-output
rm -rf test-output
```

## Test Coverage

### Covered
- ✅ Module imports
- ✅ Initialization with valid/invalid paths
- ✅ Directory structure creation
- ✅ Config file handling
- ✅ Empty directory handling
- ✅ Test data copying
- ✅ Basic file scanning

### Not Yet Covered (TODO)
- ⏳ Full processing pipeline
- ⏳ Duplicate detection accuracy
- ⏳ Blur detection accuracy
- ⏳ Burst photo grouping
- ⏳ Metadata extraction
- ⏳ Quality assessment
- ⏳ Large dataset processing (300GB)
- ⏳ Memory leak detection
- ⏳ Concurrent operations
- ⏳ Cancellation handling

## Next Steps

1. **Run Basic Tests:**
   ```bash
   python generate_test_data.py ./test-data
   python run_all_tests.py --clean
   ```

2. **Manual Web Testing:**
   ```bash
   python PhotoManagerWeb.py
   # Test each feature in browser
   ```

3. **Check Logs:**
   ```bash
   tail -f photo_manager_web.log
   # Verify all operations log properly
   ```

4. **Review Test Report:**
   ```bash
   cat TEST-REPORT.md
   # Ensure all tests pass
   ```

5. **Test with Real Data (Small Sample):**
   - Copy a few of your actual photos to test directory
   - Run processing
   - Verify results are correct

6. **Full Production Test:**
   - Backup your photos first!
   - Set base_path to your photo library
   - Run full processing pipeline
   - Monitor with logs

## Success Criteria

- ✅ All automated tests pass
- ✅ No silent failures
- ✅ All errors logged to file
- ✅ All errors shown in Activity Log
- ✅ Application doesn't crash
- ✅ User gets helpful error messages
- ⏳ Can process 300GB without issues (user testing)

## Support

If you encounter issues:

1. Check `photo_manager_web.log` for detailed errors
2. Check `TEST-REPORT.md` for test failures
3. Run tests with `--clean` to start fresh
4. Regenerate test data if corrupted
5. Check file permissions on directories

For bugs or questions, include:
- Relevant log excerpts from `photo_manager_web.log`
- Test report if applicable
- Steps to reproduce
- Expected vs actual behavior
