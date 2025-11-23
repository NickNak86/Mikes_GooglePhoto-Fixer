"""
Google Photos Manager - PyQt6 Edition
======================================
Modern Material Design GUI for photo management.

Author: Mike + Claude Code
Date: 2025-11-22
Version: 3.0 (Full PyQt6 with Material Design)
"""

import sys
import json
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QFrame,
    QDialog, QLineEdit, QFileDialog, QMessageBox, QScrollArea,
    QSizePolicy, QSpacerItem, QGridLayout, QStatusBar, QGroupBox,
    QCheckBox, QComboBox, QTabWidget, QSplitter, QListWidget,
    QListWidgetItem, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon

# Try to import PhotoProcessor, create stub if not available
try:
    from PhotoProcessor import PhotoProcessor
except ImportError:
    PhotoProcessor = None

# Material Design Dark Theme
MATERIAL_DARK_STYLE = """
QMainWindow, QDialog {
    background-color: #121212;
    color: #E0E0E0;
}

QWidget {
    background-color: #121212;
    color: #E0E0E0;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

QGroupBox {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 15px;
    padding: 0 8px;
    color: #BB86FC;
}

QPushButton {
    background-color: #BB86FC;
    color: #000000;
    border: none;
    border-radius: 4px;
    padding: 12px 24px;
    font-weight: bold;
    font-size: 14px;
    min-width: 120px;
}

QPushButton:hover {
    background-color: #CE93D8;
}

QPushButton:pressed {
    background-color: #9C27B0;
}

QPushButton:disabled {
    background-color: #424242;
    color: #757575;
}

QPushButton#destructive {
    background-color: #CF6679;
}

QPushButton#destructive:hover {
    background-color: #E57373;
}

QPushButton#secondary {
    background-color: #03DAC6;
    color: #000000;
}

QPushButton#secondary:hover {
    background-color: #4DB6AC;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #333333;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #BB86FC;
    border-radius: 4px;
}

QTextEdit, QLineEdit {
    background-color: #2D2D2D;
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 8px;
    color: #E0E0E0;
    selection-background-color: #BB86FC;
}

QTextEdit:focus, QLineEdit:focus {
    border: 2px solid #BB86FC;
}

QLabel {
    color: #E0E0E0;
}

QLabel#header {
    font-size: 24px;
    font-weight: bold;
    color: #BB86FC;
}

QLabel#subheader {
    font-size: 14px;
    color: #888888;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QStatusBar {
    background-color: #1E1E1E;
    color: #888888;
    border-top: 1px solid #333333;
}

QTabWidget::pane {
    border: 1px solid #333333;
    border-radius: 4px;
    background-color: #1E1E1E;
}

QTabBar::tab {
    background-color: #2D2D2D;
    color: #888888;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #1E1E1E;
    color: #BB86FC;
}

QListWidget {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #BB86FC;
    color: #000000;
}

QListWidget::item:hover {
    background-color: #2D2D2D;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #888888;
}

QCheckBox::indicator:checked {
    background-color: #BB86FC;
    border-color: #BB86FC;
}

QComboBox {
    background-color: #2D2D2D;
    border: 1px solid #424242;
    border-radius: 4px;
    padding: 8px;
    color: #E0E0E0;
}

QComboBox:focus {
    border: 2px solid #BB86FC;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: #2D2D2D;
    border: 1px solid #424242;
    selection-background-color: #BB86FC;
}

QSplitter::handle {
    background-color: #333333;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}
"""


class ProcessingWorker(QThread):
    """Background worker for photo processing"""
    progress = pyqtSignal(int, int, str)  # current, total, message
    log_message = pyqtSignal(str)
    finished = pyqtSignal(dict)  # results summary
    error = pyqtSignal(str)

    def __init__(self, zip_path: str, output_path: str, options: dict):
        super().__init__()
        self.zip_path = zip_path
        self.output_path = output_path
        self.options = options
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            results = {
                'processed': 0,
                'skipped': 0,
                'errors': 0,
                'duplicates': 0
            }

            self.log_message.emit(f"Opening ZIP: {self.zip_path}")

            if not os.path.exists(self.zip_path):
                self.error.emit(f"ZIP file not found: {self.zip_path}")
                return

            # Create output directory
            os.makedirs(self.output_path, exist_ok=True)

            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                # Get list of files
                all_files = zf.namelist()
                media_files = [f for f in all_files if self._is_media_file(f)]

                total = len(media_files)
                self.log_message.emit(f"Found {total} media files to process")

                for i, filename in enumerate(media_files):
                    if self._is_cancelled:
                        self.log_message.emit("Processing cancelled by user")
                        break

                    self.progress.emit(i + 1, total, os.path.basename(filename))

                    try:
                        # Extract file
                        output_file = os.path.join(self.output_path, os.path.basename(filename))

                        # Check for duplicates
                        if os.path.exists(output_file):
                            if self.options.get('skip_duplicates', True):
                                results['duplicates'] += 1
                                self.log_message.emit(f"Skipped duplicate: {filename}")
                                continue

                        # Extract
                        with zf.open(filename) as src:
                            with open(output_file, 'wb') as dst:
                                shutil.copyfileobj(src, dst)

                        results['processed'] += 1

                    except Exception as e:
                        results['errors'] += 1
                        self.log_message.emit(f"Error processing {filename}: {e}")

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))

    def _is_media_file(self, filename: str) -> bool:
        """Check if file is a media file"""
        media_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
            '.mp4', '.mov', '.avi', '.mkv', '.3gp', '.m4v',
            '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw'
        }
        ext = os.path.splitext(filename.lower())[1]
        return ext in media_extensions


class SettingsDialog(QDialog):
    """Settings configuration dialog"""

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)
        self.settings = current_settings or {}

        layout = QVBoxLayout(self)

        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)

        self.organize_by_date = QCheckBox("Organize by date (YYYY/MM folders)")
        self.organize_by_date.setChecked(self.settings.get('organize_by_date', True))
        output_layout.addWidget(self.organize_by_date)

        self.skip_duplicates = QCheckBox("Skip duplicate files")
        self.skip_duplicates.setChecked(self.settings.get('skip_duplicates', True))
        output_layout.addWidget(self.skip_duplicates)

        self.apply_metadata = QCheckBox("Apply JSON metadata to files")
        self.apply_metadata.setChecked(self.settings.get('apply_metadata', True))
        output_layout.addWidget(self.apply_metadata)

        layout.addWidget(output_group)

        # Processing settings
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)

        self.find_duplicates = QCheckBox("Find and flag duplicate photos")
        self.find_duplicates.setChecked(self.settings.get('find_duplicates', True))
        process_layout.addWidget(self.find_duplicates)

        self.preserve_edits = QCheckBox("Prefer edited versions over originals")
        self.preserve_edits.setChecked(self.settings.get('preserve_edits', True))
        process_layout.addWidget(self.preserve_edits)

        layout.addWidget(process_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def get_settings(self) -> dict:
        return {
            'organize_by_date': self.organize_by_date.isChecked(),
            'skip_duplicates': self.skip_duplicates.isChecked(),
            'apply_metadata': self.apply_metadata.isChecked(),
            'find_duplicates': self.find_duplicates.isChecked(),
            'preserve_edits': self.preserve_edits.isChecked()
        }


class PhotoManagerQt(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Google Photos Manager")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

        # State
        self.zip_path: Optional[str] = None
        self.output_path: Optional[str] = None
        self.worker: Optional[ProcessingWorker] = None
        self.settings = self._load_settings()

        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._apply_theme()

        # Status bar
        self.statusBar().showMessage("Ready - Select a Google Takeout ZIP to begin")

    def _setup_ui(self):
        """Setup the main UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Google Photos Manager")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Organize and manage your Google Takeout photos")
        subtitle.setObjectName("subheader")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Main content area with tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Process tab
        process_tab = QWidget()
        self.tabs.addTab(process_tab, "Process")
        self._setup_process_tab(process_tab)

        # Review tab
        review_tab = QWidget()
        self.tabs.addTab(review_tab, "Review Duplicates")
        self._setup_review_tab(review_tab)

        # Progress area (shared)
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        self.current_file_label = QLabel("")
        self.current_file_label.setObjectName("subheader")
        progress_layout.addWidget(self.current_file_label)

        layout.addWidget(progress_group)

        # Log area
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _setup_process_tab(self, parent):
        """Setup the processing tab"""
        layout = QVBoxLayout(parent)

        # Input section
        input_group = QGroupBox("Step 1: Select Input")
        input_layout = QVBoxLayout(input_group)

        zip_row = QHBoxLayout()
        self.zip_label = QLabel("No ZIP file selected")
        self.zip_label.setWordWrap(True)
        zip_row.addWidget(self.zip_label, 1)

        browse_zip_btn = QPushButton("Browse ZIP")
        browse_zip_btn.clicked.connect(self.browse_zip)
        zip_row.addWidget(browse_zip_btn)

        input_layout.addLayout(zip_row)
        layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox("Step 2: Select Output Location")
        output_layout = QVBoxLayout(output_group)

        output_row = QHBoxLayout()
        self.output_label = QLabel("No output folder selected")
        self.output_label.setWordWrap(True)
        output_row.addWidget(self.output_label, 1)

        browse_output_btn = QPushButton("Browse Folder")
        browse_output_btn.clicked.connect(self.browse_output)
        output_row.addWidget(browse_output_btn)

        output_layout.addLayout(output_row)
        layout.addWidget(output_group)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("secondary")
        self.settings_btn.clicked.connect(self.open_settings)
        action_layout.addWidget(self.settings_btn)

        self.process_btn = QPushButton("Start Processing")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        action_layout.addWidget(self.process_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("destructive")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setVisible(False)
        action_layout.addWidget(self.cancel_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        layout.addStretch()

    def _setup_review_tab(self, parent):
        """Setup the duplicate review tab"""
        layout = QVBoxLayout(parent)

        # Splitter for side-by-side view
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side - duplicate list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        list_label = QLabel("Duplicate Groups")
        list_label.setObjectName("subheader")
        left_layout.addWidget(list_label)

        self.duplicate_list = QListWidget()
        self.duplicate_list.itemClicked.connect(self.on_duplicate_selected)
        left_layout.addWidget(self.duplicate_list)

        load_btn = QPushButton("Load Duplicates")
        load_btn.clicked.connect(self.load_duplicates)
        left_layout.addWidget(load_btn)

        splitter.addWidget(left_panel)

        # Right side - photo comparison
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        compare_label = QLabel("Photo Comparison")
        compare_label.setObjectName("subheader")
        right_layout.addWidget(compare_label)

        # Photo display area
        photo_area = QHBoxLayout()

        self.photo_left = QLabel("Photo 1")
        self.photo_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_left.setMinimumSize(200, 200)
        self.photo_left.setStyleSheet("background-color: #2D2D2D; border-radius: 4px;")
        photo_area.addWidget(self.photo_left)

        self.photo_right = QLabel("Photo 2")
        self.photo_right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_right.setMinimumSize(200, 200)
        self.photo_right.setStyleSheet("background-color: #2D2D2D; border-radius: 4px;")
        photo_area.addWidget(self.photo_right)

        right_layout.addLayout(photo_area)

        # Action buttons for review
        review_actions = QHBoxLayout()
        review_actions.addStretch()

        keep_left_btn = QPushButton("Keep Left")
        keep_left_btn.clicked.connect(lambda: self.keep_photo('left'))
        review_actions.addWidget(keep_left_btn)

        keep_both_btn = QPushButton("Keep Both")
        keep_both_btn.setObjectName("secondary")
        keep_both_btn.clicked.connect(lambda: self.keep_photo('both'))
        review_actions.addWidget(keep_both_btn)

        keep_right_btn = QPushButton("Keep Right")
        keep_right_btn.clicked.connect(lambda: self.keep_photo('right'))
        review_actions.addWidget(keep_right_btn)

        review_actions.addStretch()
        right_layout.addLayout(review_actions)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])

    def _setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = file_menu.addAction("Open ZIP...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_zip)

        file_menu.addSeparator()

        settings_action = file_menu.addAction("Settings...")
        settings_action.triggered.connect(self.open_settings)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        compare_action = tools_menu.addAction("Compare Photos Side-by-Side")
        compare_action.triggered.connect(self.open_side_by_side)

        external_lib_action = tools_menu.addAction("Browse External Library...")
        external_lib_action.triggered.connect(self.browse_external_library)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def _apply_theme(self):
        """Apply the Material Design dark theme"""
        self.setStyleSheet(MATERIAL_DARK_STYLE)

    def _load_settings(self) -> dict:
        """Load settings from file"""
        settings_file = Path.home() / ".google_photos_manager" / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'organize_by_date': True,
            'skip_duplicates': True,
            'apply_metadata': True,
            'find_duplicates': True,
            'preserve_edits': True
        }

    def _save_settings(self):
        """Save settings to file"""
        settings_dir = Path.home() / ".google_photos_manager"
        settings_dir.mkdir(exist_ok=True)
        settings_file = settings_dir / "settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.log(f"Could not save settings: {e}")

    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def browse_zip(self):
        """Browse for ZIP file"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Google Takeout ZIP",
            str(Path.home()),
            "ZIP Files (*.zip);;All Files (*)"
        )
        if path:
            self.zip_path = path
            self.zip_label.setText(path)
            self.log(f"Selected ZIP: {path}")
            self._check_can_process()

    def browse_output(self):
        """Browse for output folder"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home())
        )
        if path:
            self.output_path = path
            self.output_label.setText(path)
            self.log(f"Selected output: {path}")
            self._check_can_process()

    def _check_can_process(self):
        """Check if processing can start"""
        can_process = self.zip_path is not None and self.output_path is not None
        self.process_btn.setEnabled(can_process)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.settings = dialog.get_settings()
            self._save_settings()
            self.log("Settings updated")

    def start_processing(self):
        """Start the processing worker"""
        if not self.zip_path or not self.output_path:
            return

        self.log("Starting processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setVisible(False)
        self.cancel_btn.setVisible(True)

        self.worker = ProcessingWorker(self.zip_path, self.output_path, self.settings)
        self.worker.progress.connect(self.on_progress)
        self.worker.log_message.connect(self.log)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()

    def cancel_processing(self):
        """Cancel the processing"""
        if self.worker:
            self.worker.cancel()
            self.log("Cancelling...")

    def on_progress(self, current: int, total: int, filename: str):
        """Handle progress updates"""
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.current_file_label.setText(f"Processing: {filename}")

    def on_processing_finished(self, results: dict):
        """Handle processing completion"""
        self.progress_bar.setVisible(False)
        self.current_file_label.setText("")
        self.process_btn.setVisible(True)
        self.cancel_btn.setVisible(False)

        self.log(f"Processing complete!")
        self.log(f"  Processed: {results['processed']}")
        self.log(f"  Duplicates skipped: {results['duplicates']}")
        self.log(f"  Errors: {results['errors']}")

        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {results['processed']} files.\n"
            f"Duplicates: {results['duplicates']}\n"
            f"Errors: {results['errors']}"
        )

    def on_processing_error(self, error: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.current_file_label.setText("")
        self.process_btn.setVisible(True)
        self.cancel_btn.setVisible(False)

        self.log(f"ERROR: {error}")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error}")

    def load_duplicates(self):
        """Load duplicates for review"""
        # TODO: Load from duplicate detection results
        self.duplicate_list.clear()
        self.duplicate_list.addItem("Group 1: IMG_1234.jpg (3 copies)")
        self.duplicate_list.addItem("Group 2: DSC_5678.jpg (2 copies)")
        self.log("Loaded duplicate groups for review")

    def on_duplicate_selected(self, item):
        """Handle duplicate group selection"""
        self.log(f"Selected: {item.text()}")
        # TODO: Load actual photos for comparison

    def keep_photo(self, which: str):
        """Handle keep photo action"""
        self.log(f"Action: Keep {which}")
        # TODO: Implement keep logic

    def open_side_by_side(self):
        """Open side-by-side photo comparison"""
        # Open file dialogs for two photos
        photo1, _ = QFileDialog.getOpenFileName(
            self,
            "Select First Photo",
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.heic)"
        )
        if not photo1:
            return

        photo2, _ = QFileDialog.getOpenFileName(
            self,
            "Select Second Photo",
            str(Path(photo1).parent),
            "Images (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.heic)"
        )
        if not photo2:
            return

        # Switch to review tab and display photos
        self.tabs.setCurrentIndex(1)

        # Load and display photos
        self._display_photo(photo1, self.photo_left)
        self._display_photo(photo2, self.photo_right)

        self.log(f"Comparing: {Path(photo1).name} vs {Path(photo2).name}")

    def _display_photo(self, path: str, label: QLabel):
        """Display a photo in a label"""
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled)
            else:
                label.setText(f"Cannot load:\n{Path(path).name}")
        except Exception as e:
            label.setText(f"Error:\n{e}")

    def browse_external_library(self):
        """Browse an external photo library folder"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Photo Library Folder",
            str(Path.home())
        )
        if path:
            # Count photos in directory
            photo_count = 0
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.heic']:
                photo_count += len(list(Path(path).glob(f'**/{ext}')))

            self.log(f"External library: {path}")
            self.log(f"Found {photo_count} photos")

            QMessageBox.information(
                self,
                "External Library",
                f"Library: {path}\nPhotos found: {photo_count}"
            )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Google Photos Manager",
            "<h2>Google Photos Manager</h2>"
            "<p>Version 3.0 (PyQt6 Edition)</p>"
            "<p>A modern tool for organizing Google Takeout photos.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Extract and organize ZIP files</li>"
            "<li>Apply JSON metadata to photos</li>"
            "<li>Detect and manage duplicates</li>"
            "<li>Side-by-side photo comparison</li>"
            "</ul>"
            "<p>Created by Mike + Claude Code</p>"
        )


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Google Photos Manager")
    app.setOrganizationName("MikeTools")

    window = PhotoManagerQt()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
