"""
Review Interface - PyQt6 Edition
================================
Enhanced photo review interface with side-by-side comparison.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QScrollArea,
    QSplitter, QMessageBox, QSizePolicy, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence, QWheelEvent

class PhotoItem(QListWidgetItem):
    """Custom QListWidgetItem to hold photo information."""

    def __init__(self, file_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.setText(os.path.basename(file_path))

class ReviewWindow(QMainWindow):
    """Main window for reviewing photos."""

    def __init__(self, directory: Path, library_path: str):
        super().__init__()
        self.setWindowTitle("Photo Review Interface")
        self.setMinimumSize(QSize(800, 600))

        self.directory = directory
        self.library_path = library_path
        self.photo_items: List[PhotoItem] = []
        self.current_index = 0

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Header
        self.header = QFrame()
        self.header.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout.addWidget(self.header)

        # Title label
        self.title_label = QLabel("Photo Review Interface")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)

        # Photo display area
        self.photo_display = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.photo_display)

        # Left side - Photo
        self.photo_view = QGraphicsView()
        self.photo_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.photo_display.addWidget(self.photo_view)

        # Right side - Controls and Info
        self.info_widget = QWidget()
        self.info_layout = QVBoxLayout(self.info_widget)
        self.photo_display.addWidget(self.info_widget)

        # Photo info
        self.photo_info_label = QLabel("Photo Info")
        self.info_layout.addWidget(self.photo_info_label)

        # Navigation buttons
        self.nav_buttons_layout = QHBoxLayout()
        self.info_layout.addLayout(self.nav_buttons_layout)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_photo)
        self.nav_buttons_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_photo)
        self.nav_buttons_layout.addWidget(self.next_button)

        # Approval buttons
        self.approval_buttons_layout = QHBoxLayout()
        self.info_layout.addLayout(self.approval_buttons_layout)

        self.approve_button = QPushButton("Approve")
        self.approve_button.clicked.connect(self.approve_photo)
        self.approval_buttons_layout.addWidget(self.approve_button)

        self.reject_button = QPushButton("Reject")
        self.reject_button.clicked.connect(self.reject_photo)
        self.approval_buttons_layout.addWidget(self.reject_button)

        # Thumbnails list
        self.thumbnails_list = QListWidget()
        self.thumbnails_list.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.thumbnails_list.itemClicked.connect(self.thumbnail_clicked)
        self.info_layout.addWidget(self.thumbnails_list)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Load photos
        self.load_photos()

        # Show first photo
        if self.photo_items:
            self.show_photo(0)

    def load_photos(self):
        """Load photo files from the directory."""
        self.photo_items.clear()
        self.thumbnails_list.clear()

        supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        for file in os.listdir(self.directory):
            if any(file.endswith(ext) for ext in supported_formats):
                file_path = os.path.join(self.directory, file)
                item = PhotoItem(file_path)
                self.photo_items.append(item)
                self.thumbnails_list.addItem(item)

    def show_photo(self, index: int):
        """Display the photo at the given index."""
        if 0 <= index < len(self.photo_items):
            self.current_index = index
            photo_item = self.photo_items[index]

            # Update title
            self.setWindowTitle(f"Photo Review Interface - {photo_item.text()}")

            # Load photo in the viewer
            pixmap = QPixmap(photo_item.file_path)
            self.photo_view.setScene(QGraphicsScene(self))
            self.photo_view.scene().addItem(QGraphicsPixmapItem(pixmap))

            # Update photo info
            self.photo_info_label.setText(f"Photo Info - {photo_item.text()}")

            # Update status bar
            self.statusBar().showMessage(f"Showing photo {index + 1} of {len(self.photo_items)}")

    def show_next_photo(self):
        """Show the next photo in the list."""
        if self.current_index + 1 < len(self.photo_items):
            self.show_photo(self.current_index + 1)

    def show_previous_photo(self):
        """Show the previous photo in the list."""
        if self.current_index - 1 >= 0:
            self.show_photo(self.current_index - 1)

    def approve_photo(self):
        """Approve the current photo."""
        self.move_photo_to_library("Approved")

    def reject_photo(self):
        """Reject the current photo."""
        self.move_photo_to_library("Rejected")

    def move_photo_to_library(self, subfolder: str):
        """Move the current photo to the library folder (Approved or Rejected)."""
        if self.photo_items:
            photo_item = self.photo_items[self.current_index]
            target_dir = Path(self.library_path) / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(photo_item.file_path, target_dir / photo_item.text())

            # Remove from the list and update display
            self.photo_items.pop(self.current_index)
            self.thumbnails_list.takeItem(self.thumbnails_list.row(photo_item))
            if self.photo_items:
                new_index = min(self.current_index, len(self.photo_items) - 1)
                self.show_photo(new_index)
            else:
                self.photo_view.setScene(QGraphicsScene(self))
                self.photo_info_label.setText("")
                self.statusBar().showMessage("No more photos to display")

    def thumbnail_clicked(self, item: QListWidgetItem):
        """Handle thumbnail click event."""
        if isinstance(item, PhotoItem):
            self.show_photo(self.photo_items.index(item))

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel event for zooming."""
        factor = 1.2
        if event.angleDelta().y() < 0:
            factor = 1 / factor
        self.photo_view.scale(factor, factor)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    test_dir = Path.home() / "PhotoLibrary" / "Pics Waiting for Approval"
    if test_dir.exists():
        window = ReviewWindow(test_dir, str(Path.home() / "PhotoLibrary"))
        window.show()
        sys.exit(app.exec())