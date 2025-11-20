# Google Photos Manager

Welcome to the **Google Photos Manager** documentation! This tool helps you organize, deduplicate, and manage your Google Photos Takeout archives with intelligent automation and quality assessment.

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Getting Started__

    ---

    Install and set up Google Photos Manager in minutes

    [:octicons-arrow-right-24: Quick Start](getting-started/quick-start.md)

-   :material-cellphone:{ .lg .middle } __Mobile App__

    ---

    Run on Android with native mobile support

    [:octicons-arrow-right-24: Mobile Guide](mobile/architecture.md)

-   :material-code-braces:{ .lg .middle } __API Reference__

    ---

    Detailed API documentation for developers

    [:octicons-arrow-right-24: API Docs](api/photo-processor.md)

-   :material-school:{ .lg .middle } __Tutorials__

    ---

    Step-by-step guides for common tasks

    [:octicons-arrow-right-24: Tutorials](tutorials/first-time-setup.md)

</div>

## Features

### :sparkles: Intelligent Processing

- **Duplicate Detection**: Find and manage duplicate photos using SHA256 hashing
- **Blur Detection**: Identify blurry photos using OpenCV's Laplacian variance
- **Burst Photo Grouping**: Group sequential photos taken within seconds
- **Size Filtering**: Flag photos below quality thresholds
- **Parallel Processing**: Multi-threaded for fast processing of large archives

### :iphone: Cross-Platform

- **Desktop**: Full-featured GUI for Windows, macOS, and Linux
- **Mobile**: Android app built with Kivy for on-the-go management
- **Cloud Ready**: Designed for Google Takeout archives

### :shield: Quality First

- **Non-Destructive**: Review before any deletions
- **Metadata Preservation**: Maintains EXIF data and creation times
- **Organized Output**: Structured by year/month for easy navigation

## Quick Example

```python
from PhotoProcessorEnhanced import PhotoProcessorEnhanced

# Initialize processor
processor = PhotoProcessorEnhanced(
    base_path="/path/to/PhotoLibrary",
    worker_threads=4
)

# Process Google Takeout
results = processor.process_google_takeout()

# Review and organize
processor.generate_review_report()
```

## Screenshots

=== "Desktop Application"

    ![Desktop App](../assets/screenshot-desktop.svg)

    Material Design dark mode interface with real-time progress tracking

=== "Mobile Application"

    ![Mobile App](../assets/screenshot-mobile.svg)

    Touch-optimized Android interface for mobile photo management

## Platform Support

| Platform | Status | Features |
|----------|--------|----------|
| :fontawesome-brands-windows: Windows | ✅ Full Support | Desktop GUI, All Features |
| :fontawesome-brands-apple: macOS | ✅ Full Support | Desktop GUI, All Features |
| :fontawesome-brands-linux: Linux | ✅ Full Support | Desktop GUI, Buildozer |
| :fontawesome-brands-android: Android | ✅ Mobile App | Kivy UI, Native Storage |
| :fontawesome-brands-apple: iOS | 🚧 Planned | Kivy iOS Toolchain |

## Technology Stack

<div class="grid" markdown>

- **Python 3.9+**: Core language
- **Pillow**: Image processing
- **OpenCV**: Blur detection
- **Kivy/KivyMD**: Mobile UI
- **tkinter**: Desktop GUI
- **NumPy**: Array operations

</div>

## Community

- 📝 [Report Issues](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/issues)
- 🤝 [Contributing Guide](development/contributing.md)
- 💬 [Discussions](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/discussions)
- ⭐ [Star on GitHub](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer)

## License

This project is licensed under the **MIT License** - see the [LICENSE](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/blob/main/LICENSE) file for details.

---

!!! tip "Ready to Get Started?"
    Follow the [Quick Start Guide](getting-started/quick-start.md) to install and configure Google Photos Manager!
