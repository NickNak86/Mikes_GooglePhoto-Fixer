"""
Google Photos Manager - Modern Material Design GUI
===================================================
Professional photo management interface for non-technical users.

Author: Claude Code
Date: 2025-11-20
Version: 2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import json
import os
from datetime import datetime
from PhotoProcessor import PhotoProcessor, ProcessingIssue


class MaterialButton(tk.Canvas):
    """Custom Material Design style button"""

    def __init__(self, parent, text, command, color="#1a73e8", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)

        self.color = color
        self.hover_color = self._lighten_color(color)
        self.command = command
        self.text = text

        self.config(height=50, bg=color, cursor="hand2")

        # Text
        self.create_text(
            self.winfo_reqwidth() // 2 if self.winfo_reqwidth() > 1 else 150,
            25,
            text=text,
            fill="white",
            font=("Segoe UI", 12, "bold"),
            tags="text"
        )

        # Bindings
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _lighten_color(self, color):
        """Lighten a hex color"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * 1.1))
        g = min(255, int(g * 1.1))
        b = min(255, int(b * 1.1))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _on_enter(self, event):
        self.config(bg=self.hover_color)

    def _on_leave(self, event):
        self.config(bg=self.color)


class PhotoManagerGUI:
    """Main GUI application"""

    # Material Design Dark Mode colors
    PRIMARY = "#BB86FC"      # Material Purple
    SUCCESS = "#4CAF50"      # Material Green
    WARNING = "#FFA726"      # Material Orange
    DANGER = "#CF6679"       # Material Pink-Red
    SECONDARY = "#03DAC6"    # Material Teal
    BG_DARK = "#121212"      # Very dark gray (main background)
    BG_SURFACE = "#1e1e1e"   # Dark gray (cards/surfaces)
    BG_ELEVATED = "#2d2d2d"  # Slightly lighter (elevated elements)
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B0B0B0"
    DIVIDER = "#2d2d2d"

    def __init__(self, root):
        self.root = root
        self.root.title("📸 Google Photos Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg=self.BG_DARK)

        # State
        self.config_file = Path(__file__).parent / "config.json"
        self.settings = self.load_settings()
        self.processor = None
        self.is_processing = False

        # Build UI
        self.create_ui()

        # Center window
        self.center_window()

    def load_settings(self) -> dict:
        """Load settings from config file"""
        default_settings = {
            "base_path": str(Path.home() / "PhotoLibrary"),
            "exiftool_path": "exiftool"  # Assumes exiftool is in PATH
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return default_settings

    def save_settings(self):
        """Save settings to config file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def create_ui(self):
        """Create the user interface"""

        # Header
        header = tk.Frame(self.root, bg=self.BG_ELEVATED, height=120)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="📸 Google Photos Manager",
            font=("Segoe UI", 28, "bold"),
            bg=self.BG_ELEVATED,
            fg=self.PRIMARY
        )
        title.pack(pady=(20, 5))

        subtitle = tk.Label(
            header,
            text="Organize your photo library automatically",
            font=("Segoe UI", 12),
            bg=self.BG_ELEVATED,
            fg=self.TEXT_SECONDARY
        )
        subtitle.pack()

        # Main content area
        content = tk.Frame(self.root, bg=self.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Create cards
        self._create_action_card(content)
        self._create_progress_card(content)
        self._create_log_card(content)

        # Bottom bar
        bottom = tk.Frame(self.root, bg=self.BG_DARK, height=50)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=30, pady=(0, 20))

        settings_btn = tk.Button(
            bottom,
            text="⚙️ Settings",
            command=self.show_settings,
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 10),
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            activebackground=self.BG_SURFACE,
            activeforeground=self.TEXT_PRIMARY
        )
        settings_btn.pack(side=tk.LEFT, padx=5)

        help_btn = tk.Button(
            bottom,
            text="❓ Help",
            command=self.show_help,
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 10),
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            activebackground=self.BG_SURFACE,
            activeforeground=self.TEXT_PRIMARY
        )
        help_btn.pack(side=tk.LEFT, padx=5)

    def _create_action_card(self, parent):
        """Create the action buttons card"""
        card = tk.Frame(parent, bg=self.BG_SURFACE, relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, pady=(0, 20))

        # Add subtle border
        card.config(highlightbackground=self.DIVIDER, highlightthickness=1)

        card_title = tk.Label(
            card,
            text="Quick Actions",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        )
        card_title.pack(anchor=tk.W, padx=20, pady=(20, 10))

        # Button container
        btn_container = tk.Frame(card, bg=self.BG_SURFACE)
        btn_container.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Main action button
        self.process_btn = tk.Button(
            btn_container,
            text="🚀 Process New Google Takeout",
            command=self.start_processing,
            bg=self.PRIMARY,
            fg=self.BG_DARK,
            font=("Segoe UI", 14, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=15,
            activebackground=self._lighten_color(self.PRIMARY),
            activeforeground=self.BG_DARK
        )
        self.process_btn.pack(fill=tk.X, pady=(0, 10))

        # Secondary buttons
        btn_frame = tk.Frame(btn_container, bg=self.BG_SURFACE)
        btn_frame.pack(fill=tk.X)

        review_btn = tk.Button(
            btn_frame,
            text="👀 Review Flagged Photos",
            command=self.open_review,
            bg=self.WARNING,
            fg=self.BG_DARK,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12,
            activebackground=self._lighten_color(self.WARNING),
            activeforeground=self.BG_DARK
        )
        review_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        folder_btn = tk.Button(
            btn_frame,
            text="📁 Open Library",
            command=self.open_library,
            bg=self.SUCCESS,
            fg=self.BG_DARK,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12,
            activebackground=self._lighten_color(self.SUCCESS),
            activeforeground=self.BG_DARK
        )
        folder_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def _create_progress_card(self, parent):
        """Create the progress indicator card"""
        card = tk.Frame(parent, bg=self.BG_SURFACE, relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, pady=(0, 20))
        card.config(highlightbackground=self.DIVIDER, highlightthickness=1)

        card_title = tk.Label(
            card,
            text="Progress",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        )
        card_title.pack(anchor=tk.W, padx=20, pady=(20, 10))

        # Status label
        self.status_label = tk.Label(
            card,
            text="Ready to process photos",
            font=("Segoe UI", 11),
            bg=self.BG_SURFACE,
            fg=self.TEXT_SECONDARY
        )
        self.status_label.pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.BG_DARK,
            bordercolor=self.BG_SURFACE,
            background=self.PRIMARY,
            lightcolor=self.PRIMARY,
            darkcolor=self.PRIMARY
        )

        self.progress_bar = ttk.Progressbar(
            card,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, padx=20, pady=(0, 20))

    def _create_log_card(self, parent):
        """Create the activity log card"""
        card = tk.Frame(parent, bg=self.BG_SURFACE, relief=tk.FLAT, bd=0)
        card.pack(fill=tk.BOTH, expand=True)
        card.config(highlightbackground=self.DIVIDER, highlightthickness=1)

        card_title = tk.Label(
            card,
            text="Activity Log",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        )
        card_title.pack(anchor=tk.W, padx=20, pady=(20, 10))

        # Log text area
        log_frame = tk.Frame(card, bg=self.BG_SURFACE)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        scrollbar = tk.Scrollbar(log_frame, bg=self.BG_ELEVATED)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            font=("Consolas", 9),
            bg=self.BG_DARK,
            fg=self.TEXT_PRIMARY,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD,
            insertbackground=self.PRIMARY
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Add initial message
        self.log("Welcome to Google Photos Manager!")
        self.log("Click 'Process New Google Takeout' to get started.")

    def _lighten_color(self, color):
        """Lighten a hex color for hover effects"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _darken_color(self, color):
        """Darken a hex color"""
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        return f'#{r:02x}{g:02x}{b:02x}'

    def log(self, message: str):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.config(text=message)
        self.log(message)
        self.root.update()

    def update_progress(self, percent: float):
        """Update progress bar"""
        self.progress_bar['value'] = percent
        self.root.update()

    def start_processing(self):
        """Start the photo processing pipeline"""
        if self.is_processing:
            messagebox.showwarning(
                "Processing",
                "Processing is already in progress. Please wait."
            )
            return

        # Verify base path exists
        base_path = Path(self.settings['base_path'])
        if not base_path.exists():
            messagebox.showerror(
                "Path Not Found",
                f"The base path does not exist:\n{base_path}\n\nPlease check your settings."
            )
            return

        # Confirm
        result = messagebox.askyesno(
            "Process Photos",
            "This will:\n\n"
            "• Extract Google Takeout archives\n"
            "• Restore metadata from JSON files\n"
            "• Find and organize duplicates\n"
            "• Detect quality issues\n"
            "• Group burst photos\n"
            "• Sort good photos by date\n\n"
            "Continue?",
            icon='question'
        )

        if not result:
            return

        # Disable button
        self.process_btn.config(state=tk.DISABLED)
        self.is_processing = True

        # Run in background thread
        thread = threading.Thread(target=self._process_photos, daemon=True)
        thread.start()

    def _process_photos(self):
        """Background processing thread"""
        try:
            # Create processor
            self.processor = PhotoProcessor(
                base_path=self.settings['base_path'],
                exiftool_path=self.settings.get('exiftool_path')
            )

            # Set callbacks
            self.processor.progress_callback = self.update_progress
            self.processor.status_callback = self.update_status

            # Run pipeline
            stats, issues = self.processor.run_full_pipeline()

            # Show summary
            summary = self.processor.get_summary()
            self.root.after(0, lambda: self._show_completion(summary, stats))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"An error occurred during processing:\n\n{str(e)}"
            ))
            self.log(f"❌ Error: {str(e)}")

        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.update_progress(0))

    def _show_completion(self, summary: str, stats: dict):
        """Show processing completion dialog"""
        self.update_status("✅ Processing complete!")

        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Processing Complete")
        dialog.geometry("500x400")
        dialog.configure(bg=self.BG_SURFACE)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header = tk.Label(
            dialog,
            text="✅ Processing Complete!",
            font=("Segoe UI", 20, "bold"),
            bg=self.SUCCESS,
            fg=self.BG_DARK,
            pady=20
        )
        header.pack(fill=tk.X)

        # Summary
        summary_text = tk.Text(
            dialog,
            font=("Segoe UI", 11),
            bg=self.BG_DARK,
            fg=self.TEXT_PRIMARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
            height=12,
            insertbackground=self.PRIMARY
        )
        summary_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        summary_text.insert("1.0", summary)
        summary_text.config(state=tk.DISABLED)

        # Buttons
        btn_frame = tk.Frame(dialog, bg=self.BG_SURFACE)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        review_btn = tk.Button(
            btn_frame,
            text="👀 Review Flagged Photos",
            command=lambda: [dialog.destroy(), self.open_review()],
            bg=self.WARNING,
            fg=self.BG_DARK,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        review_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        close_btn = tk.Button(
            btn_frame,
            text="Close",
            command=dialog.destroy,
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        close_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def open_review(self):
        """Open the review interface"""
        review_dir = Path(self.settings['base_path']) / "Pics Waiting for Approval"

        if not review_dir.exists() or not any(review_dir.iterdir()):
            messagebox.showinfo(
                "No Items to Review",
                "There are no flagged photos to review.\n\nRun processing first!"
            )
            return

        # Open review window
        from ReviewInterface import ReviewInterface
        ReviewInterface(self.root, review_dir, self.settings['base_path'])

    def open_library(self):
        """Open the Photos & Videos library in file explorer"""
        library_path = Path(self.settings['base_path']) / "Photos & Videos"

        if not library_path.exists():
            messagebox.showinfo(
                "Library Not Found",
                "The photo library hasn't been created yet.\n\nRun processing first!"
            )
            return

        # Open in file explorer
        if os.name == 'nt':  # Windows
            os.startfile(str(library_path))
        else:  # macOS/Linux
            import subprocess
            subprocess.Popen(['xdg-open', str(library_path)])

    def show_settings(self):
        """Show settings dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("600x300")
        dialog.configure(bg=self.BG_SURFACE)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header = tk.Label(
            dialog,
            text="⚙️ Settings",
            font=("Segoe UI", 18, "bold"),
            bg=self.BG_ELEVATED,
            fg=self.PRIMARY,
            pady=15
        )
        header.pack(fill=tk.X)

        # Settings form
        form = tk.Frame(dialog, bg=self.BG_SURFACE)
        form.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Base path
        tk.Label(
            form,
            text="Base Folder:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        base_path_var = tk.StringVar(value=self.settings['base_path'])
        base_entry = tk.Entry(
            form,
            textvariable=base_path_var,
            font=("Segoe UI", 10),
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            insertbackground=self.PRIMARY,
            width=50
        )
        base_entry.grid(row=1, column=0, pady=(0, 15), sticky=tk.EW)

        browse_btn = tk.Button(
            form,
            text="Browse...",
            command=lambda: self._browse_folder(base_path_var),
            bg=self.PRIMARY,
            fg="white",
            font=("Segoe UI", 9),
            cursor="hand2",
            relief=tk.FLAT
        )
        browse_btn.grid(row=1, column=1, padx=(10, 0), pady=(0, 15))

        # ExifTool path
        tk.Label(
            form,
            text="ExifTool Path:",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        ).grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        exiftool_var = tk.StringVar(value=self.settings.get('exiftool_path', ''))
        exiftool_entry = tk.Entry(
            form,
            textvariable=exiftool_var,
            font=("Segoe UI", 10),
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            insertbackground=self.PRIMARY,
            width=50
        )
        exiftool_entry.grid(row=3, column=0, pady=(0, 15), sticky=tk.EW)

        browse_exe_btn = tk.Button(
            form,
            text="Browse...",
            command=lambda: self._browse_file(exiftool_var),
            bg=self.PRIMARY,
            fg="white",
            font=("Segoe UI", 9),
            cursor="hand2",
            relief=tk.FLAT
        )
        browse_exe_btn.grid(row=3, column=1, padx=(10, 0), pady=(0, 15))

        form.columnconfigure(0, weight=1)

        # Buttons
        btn_frame = tk.Frame(dialog, bg=self.BG_SURFACE)
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))

        def save_and_close():
            self.settings['base_path'] = base_path_var.get()
            self.settings['exiftool_path'] = exiftool_var.get()
            self.save_settings()
            self.log("Settings saved")
            dialog.destroy()

        save_btn = tk.Button(
            btn_frame,
            text="💾 Save",
            command=save_and_close,
            bg=self.SUCCESS,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            bg=self.TEXT_SECONDARY,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        cancel_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def _browse_folder(self, var):
        """Browse for folder"""
        folder = filedialog.askdirectory(initialdir=var.get())
        if folder:
            var.set(folder)

    def _browse_file(self, var):
        """Browse for file"""
        file = filedialog.askopenfilename(initialdir=os.path.dirname(var.get()))
        if file:
            var.set(file)

    def show_help(self):
        """Show help dialog"""
        help_text = """
🌟 Google Photos Manager - Quick Guide

GETTING STARTED:
1. Download your Google Takeout and save the ZIP file to:
   <Your PhotoLibrary>/GoogleTakeout/

2. Click "Process New Google Takeout" to automatically:
   • Extract the archive
   • Restore photo dates and locations
   • Find duplicates
   • Detect blurry/corrupted photos
   • Group burst photos
   • Organize everything by date

3. Review flagged photos:
   • Click "Review Flagged Photos" to see items needing attention
   • The software recommends which photos to keep
   • You make the final decision

FOLDER STRUCTURE:
📁 PhotoLibrary
  ├── GoogleTakeout (drop ZIP files here)
  ├── Photos & Videos (your organized library)
  └── Pics Waiting for Approval (flagged items)

TIPS:
• The app automatically picks the best photo in duplicates/bursts
• All flagged items are shown for your review
• Nothing is deleted automatically - you're in control
• Processing is safe - files are moved, not deleted

Need more help? Check the README.md file!
        """

        dialog = tk.Toplevel(self.root)
        dialog.title("Help")
        dialog.geometry("700x600")
        dialog.configure(bg=self.BG_SURFACE)
        dialog.transient(self.root)

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header = tk.Label(
            dialog,
            text="❓ Help",
            font=("Segoe UI", 18, "bold"),
            bg=self.BG_ELEVATED,
            fg=self.PRIMARY,
            pady=15
        )
        header.pack(fill=tk.X)

        # Help text
        text = tk.Text(
            dialog,
            font=("Segoe UI", 10),
            bg=self.BG_DARK,
            fg=self.TEXT_PRIMARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
            padx=20,
            pady=20
        )
        text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        text.insert("1.0", help_text)
        text.config(state=tk.DISABLED)

        # Close button
        close_btn = tk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            bg=self.PRIMARY,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10,
            padx=40
        )
        close_btn.pack(pady=(0, 20))

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')


def main():
    """Main entry point"""
    root = tk.Tk()
    app = PhotoManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
