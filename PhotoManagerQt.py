"""
Google Photos Manager - PyQt6 Edition
======================================
Modern Material Design GUI for photo management.

Author: Claude Code
Date: 2025-11-22
Version: 3.0 (PyQt6 Migration)
"""

import sys
import json
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QFrame,
    QDialog, QLineEdit, QFileDialog, QMessageBox, QScrollArea,
    QSizePolicy, QSpacerItem, QGridLayout, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QObject
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QShortcut, QKeySequence

from PhotoProcessor import PhotoProcessor, ProcessingIssue

class PhotoManagerQt(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Google Photos Manager - PyQt6 Edition")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(QSize(480, 320))

        # Central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Header
        self.header = QFrame(self.central_widget)
        self.header.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout.addWidget(self.header)

        self.title = QLabel("Google Photos Manager", self.header)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.title.setFont(font)

        # Photo display area
        self.photo_display = QScrollArea(self.central_widget)
        self.photo_display.setWidgetResizable(True)
        self.layout.addWidget(self.photo_display)

        # Photo information area
        self.info_area = QFrame(self.central_widget)
        self.info_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout.addWidget(self.info_area)

        self.info_layout = QVBoxLayout(self.info_area)

        self.photo_name = QLabel("Photo Name: ", self.info_area)
        self.info_layout.addWidget(self.photo_name)

        self.photo_date = QLabel("Date Taken: ", self.info_area)
        self.info_layout.addWidget(self.photo_date)

        self.photo_location = QLabel("Location: ", self.info_area)
        self.info_layout.addWidget(self.photo_location)

        # Control buttons
        self.controls = QFrame(self.central_widget)
        self.controls.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout.addWidget(self.controls)

        self.controls_layout = QHBoxLayout(self.controls)

        self.load_button = QPushButton("Load Photos", self.controls)
        self.load_button.clicked.connect(self.load_photos)
        self.controls_layout.addWidget(self.load_button)

        self.process_button = QPushButton("Process Photos", self.controls)
        self.process_button.clicked.connect(self.process_photos)
        self.controls_layout.addWidget(self.process_button)

        self.save_button = QPushButton("Save Changes", self.controls)
        self.save_button.clicked.connect(self.save_changes)
        self.controls_layout.addWidget(self.save_button)

        # Status bar
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)

        # Initialize variables
        self.photo_paths = []
        self.current_photo_index = 0

    def load_photos(self):
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self, "Select Photo Directory", options=options)
        if directory:
            self.photo_paths = [str(Path(directory) / file) for file in os.listdir(directory) if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
            self.current_photo_index = 0
            self.show_photo()

    def show_photo(self):
        if self.photo_paths:
            photo_path = self.photo_paths[self.current_photo_index]
            self.photo_name.setText(f"Photo Name: {os.path.basename(photo_path)}")
            # Date taken and location are not always available, handle exceptions
            try:
                processor = PhotoProcessor(photo_path)
                self.photo_date.setText(f"Date Taken: {processor.date_taken.strftime('%Y-%m-%d %H:%M:%S')}")
                self.photo_location.setText(f"Location: {processor.location}")
            except Exception as e:
                self.photo_date.setText("Date Taken: N/A")
                self.photo_location.setText("Location: N/A")
                self.status.showMessage(f"Error processing photo metadata: {e}", 5000)

    def process_photos(self):
        if not self.photo_paths:
            return

        # Disable buttons to prevent re-entrance
        self.load_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.save_button.setEnabled(False)

        # Create and start the processing thread
        self.thread = QThread()
        self.worker = PhotoProcessorWorker(self.photo_paths)
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.thread.started.connect(self.worker.process_photos)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.progress.connect(self.update_progress)

        self.thread.start()

    def update_progress(self, value):
        self.status.showMessage(f"Processing photos... {value}%", 5000)

    def on_processing_finished(self):
        self.status.showMessage("Processing finished.", 5000)
        self.load_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.show_photo()  # Update the displayed photo info

    def save_changes(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Photo List", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'w') as json_file:
                    json.dump(self.photo_paths, json_file)
                self.status.showMessage(f"Changes saved to {file_name}", 5000)
            except Exception as e:
                self.status.showMessage(f"Error saving changes: {e}", 5000)

class PhotoProcessorWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, photo_paths):
        super().__init__()
        self.photo_paths = photo_paths

    def process_photos(self):
        total_photos = len(self.photo_paths)
        for index, photo_path in enumerate(self.photo_paths):
            # Simulate processing time
            QThread.sleep(1)
            # Emit progress signal
            self.progress.emit(int((index + 1) / total_photos * 100))
        self.finished.emit()

def main():
    app = QApplication(sys.argv)
    window = PhotoManagerQt()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()