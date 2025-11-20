# Contributing to Google Photos Manager

First off, thank you for considering contributing to Google Photos Manager! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Familiarity with Python, OpenCV, and (optionally) Kivy for mobile development

### Quick Start

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/Mikes_GooglePhoto-Fixer.git
cd Mikes_GooglePhoto-Fixer

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

## Development Setup

### Using Installation Scripts

```bash
# Linux/macOS
./install.sh

# Windows
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Using Docker

```bash
# Start development environment
docker-compose up desktop-dev

# Run tests
docker-compose up test

# Build documentation
docker-compose up docs
```

### Manual Setup

1. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Mikes_GooglePhoto-Fixer.git
   cd Mikes_GooglePhoto-Fixer
   ```

2. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/NickNak86/Mikes_GooglePhoto-Fixer.git
   ```

3. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## How to Contribute

### Reporting Bugs

Found a bug? Please create an issue using our [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md).

**Before submitting:**
- Check if the issue already exists
- Provide clear reproduction steps
- Include system information
- Attach relevant logs

### Suggesting Enhancements

Have an idea? Create an issue using our [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).

**Include:**
- Clear description of the problem
- Proposed solution
- Use cases and examples
- Any alternatives you've considered

### Code Contributions

1. **Find or create an issue** to work on
2. **Comment** on the issue to let others know you're working on it
3. **Fork** the repository
4. **Create a branch** from `main`
5. **Make your changes**
6. **Test thoroughly**
7. **Submit a pull request**

## Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (enforced by Black)
- **Imports**: Organized by isort
- **Type hints**: Encouraged for all functions
- **Docstrings**: Google style for all public functions

### Code Formatting

We use automated tools to enforce consistency:

```bash
# Format code
black .
isort .

# Check formatting
black --check .
isort --check-only .
```

### Linting

```bash
# Run linting
flake8 .
mypy .
bandit -r .

# Or run all pre-commit hooks
pre-commit run --all-files
```

### Example Code Style

```python
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image


def calculate_blur_score(
    image_path: Path,
    threshold: float = 100.0
) -> Tuple[bool, float]:
    """
    Calculate blur score for an image using Laplacian variance.

    Args:
        image_path: Path to the image file
        threshold: Blur detection threshold (default: 100.0)

    Returns:
        Tuple of (is_blurry, blur_score)

    Raises:
        ValueError: If image cannot be read

    Example:
        >>> blur_score = calculate_blur_score(Path("photo.jpg"))
        >>> is_blurry, score = blur_score
        >>> print(f"Blur score: {score:.2f}")
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    is_blurry = laplacian_var < threshold
    return is_blurry, laplacian_var
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(mobile): Add swipe gestures for photo review

Implements left/right swipe gestures in the review interface
for quick photo decisions on mobile devices.

Closes #123
```

```
fix(desktop): Resolve crash when processing corrupted images

Added error handling to skip corrupted files instead of crashing.
Now logs warnings for problematic files.

Fixes #456
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_mobile_utils.py

# Run specific test function
pytest tests/unit/test_mobile_utils.py::test_storage_path

# Run tests matching pattern
pytest -k "test_blur"
```

### Writing Tests

Use pytest and follow these guidelines:

```python
import pytest
from pathlib import Path


def test_blur_detection_sharp_image(sample_image):
    """Test that sharp images are not detected as blurry."""
    is_blurry, score = calculate_blur_score(sample_image)

    assert not is_blurry, "Sharp image incorrectly marked as blurry"
    assert score > 100.0, f"Expected score > 100, got {score}"


@pytest.mark.slow
def test_large_dataset_processing(temp_dir):
    """Test processing a large number of photos."""
    # Test implementation
    pass
```

### Test Organization

```
tests/
├── unit/              # Unit tests for individual functions
├── integration/       # Integration tests for workflows
├── performance/       # Performance benchmarks
├── compatibility/     # Compatibility tests
└── conftest.py       # Shared fixtures
```

## Documentation

### Docstring Style

Use Google-style docstrings:

```python
def process_photos(
    input_dir: Path,
    output_dir: Path,
    worker_threads: int = 4
) -> Dict[str, int]:
    """
    Process photos from input directory to output directory.

    This function scans the input directory for photos, processes them
    using multiple worker threads, and organizes them in the output
    directory by date.

    Args:
        input_dir: Directory containing photos to process
        output_dir: Directory where processed photos will be saved
        worker_threads: Number of parallel workers (default: 4)

    Returns:
        Dictionary with processing statistics:
            - 'total': Total photos processed
            - 'duplicates': Number of duplicates found
            - 'blurry': Number of blurry photos flagged

    Raises:
        ValueError: If input_dir doesn't exist
        PermissionError: If output_dir is not writable

    Example:
        >>> stats = process_photos(
        ...     Path("/photos/input"),
        ...     Path("/photos/output"),
        ...     worker_threads=8
        ... )
        >>> print(f"Processed {stats['total']} photos")
    """
    pass
```

### Documentation Site

We use MkDocs with Material theme:

```bash
# Install docs dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve locally
mkdocs serve

# Build
mkdocs build
```

Add documentation in `docs/` directory:
- User guides in `docs/user-guide/`
- API reference in `docs/api/`
- Tutorials in `docs/tutorials/`

## Pull Request Process

### Before Submitting

1. **Update your branch** with latest main
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**
   ```bash
   # Format code
   black .
   isort .

   # Run linters
   flake8 .
   mypy .

   # Run tests
   pytest

   # Or run all pre-commit hooks
   pre-commit run --all-files
   ```

3. **Update documentation** if needed

4. **Add tests** for new functionality

5. **Update CHANGELOG.md** under "Unreleased" section

### Submitting the PR

1. **Push** your branch to your fork
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open a Pull Request** on GitHub

3. **Fill out the PR template** completely

4. **Link related issues** (e.g., "Closes #123")

5. **Request review** from maintainers

### PR Review Process

1. **Automated checks** must pass (CI, tests, linting)
2. **Code review** by at least one maintainer
3. **Changes requested** - address feedback and push updates
4. **Approval** - PR will be merged by maintainer

### After Merge

1. **Delete your branch** (optional but recommended)
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/amazing-feature

# 2. Make changes
# ... edit files ...

# 3. Test changes
pytest

# 4. Commit changes
git add .
git commit -m "feat: Add amazing feature"

# 5. Push to fork
git push origin feature/amazing-feature

# 6. Open Pull Request on GitHub
```

### Bug Fixes

```bash
# 1. Create fix branch
git checkout -b fix/bug-description

# 2. Fix the bug
# ... edit files ...

# 3. Add regression test
# ... write test ...

# 4. Verify fix
pytest

# 5. Commit and push
git add .
git commit -m "fix: Resolve bug description"
git push origin fix/bug-description

# 6. Open Pull Request
```

## Project Structure

Understanding the codebase:

```
Mikes_GooglePhoto-Fixer/
├── PhotoManager.py              # Desktop GUI (tkinter)
├── PhotoManagerMobile.py        # Mobile app (Kivy)
├── ReviewInterface.py           # Review interface
├── PhotoProcessorEnhanced.py    # Core processing engine
├── mobile_utils.py              # Mobile platform utilities
├── tests/                       # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── performance/            # Performance tests
│   └── conftest.py             # Shared fixtures
├── docs/                        # Documentation
├── .github/                     # GitHub config
│   ├── workflows/              # CI/CD workflows
│   └── ISSUE_TEMPLATE/         # Issue templates
└── assets/                      # Visual assets
```

## Key Modules

### PhotoProcessorEnhanced.py
Core processing engine - handles:
- File scanning
- Hash calculation (parallel)
- Blur detection (OpenCV)
- Duplicate detection
- Quality assessment
- File organization

### mobile_utils.py
Platform abstraction layer:
- Android permissions
- Storage path management
- Configuration management
- Platform detection

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions)
- **Bugs**: Create an [Issue](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
- **Chat**: Join discussions in existing issues and PRs

## Recognition

Contributors will be:
- Listed in [CHANGELOG.md](CHANGELOG.md)
- Mentioned in release notes
- Added to the Contributors section (coming soon)

Thank you for contributing! 🎉
