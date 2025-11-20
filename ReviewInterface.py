"""
Review Interface - DupeGuru-style Photo Review
===============================================
User-friendly interface for reviewing flagged photos.

Author: Claude Code
Date: 2025-11-20
Version: 2.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk
import os
import shutil
from typing import List, Optional


class PhotoGroup:
    """Represents a group of related photos (duplicates, bursts, etc.)"""

    def __init__(self, folder: Path, category: str):
        self.folder = folder
        self.category = category
        self.photos = []
        self.best_photo = None

        # Find all photos in folder
        image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.webp'}
        for ext in image_extensions:
            self.photos.extend(list(folder.glob(f"*{ext}")))
            self.photos.extend(list(folder.glob(f"*{ext.upper()}")))

        # Find the recommended best photo
        for photo in self.photos:
            if photo.name.startswith("BEST_"):
                self.best_photo = photo
                break

        # If no BEST_ prefix, first photo is default
        if not self.best_photo and self.photos:
            self.best_photo = self.photos[0]

        # Sort photos: best first, then others
        if self.best_photo:
            self.photos = [self.best_photo] + [p for p in self.photos if p != self.best_photo]

    @property
    def name(self):
        """Get friendly name for this group"""
        return self.folder.name

    @property
    def count(self):
        """Number of photos in group"""
        return len(self.photos)


class ReviewInterface:
    """DupeGuru-style review interface"""

    PRIMARY = "#BB86FC"
    SUCCESS = "#4CAF50"
    WARNING = "#FFA726"
    DANGER = "#CF6679"
    SECONDARY = "#03DAC6"
    BG_DARK = "#121212"
    BG_SURFACE = "#1e1e1e"
    BG_ELEVATED = "#2d2d2d"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B0B0B0"
    DIVIDER = "#2d2d2d"

    def __init__(self, parent, review_dir: Path, base_path: str):
        self.review_dir = review_dir
        self.base_path = Path(base_path)
        self.photos_dir = self.base_path / "Photos & Videos"

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("👀 Review Flagged Photos")
        self.window.geometry("1200x800")
        self.window.configure(bg=self.BG_DARK)

        # Load groups
        self.groups = self._load_groups()
        self.current_group_idx = 0
        self.selected_photo = None

        # Decisions
        self.decisions = {}  # group_folder -> list of photos to keep

        # Build UI
        self.create_ui()

        # Center window
        self.center_window()

        # Load first group
        if self.groups:
            self.load_group(0)
        else:
            messagebox.showinfo(
                "No Items",
                "No flagged photos found to review!"
            )
            self.window.destroy()

    def _load_groups(self) -> List[PhotoGroup]:
        """Load all photo groups from review directory"""
        groups = []

        # Check each category folder
        categories = {
            "NEEDS ATTENTION - Duplicates": "duplicates",
            "NEEDS ATTENTION - Burst Photos": "burst",
            "NEEDS ATTENTION - Blurry or Corrupt": "quality",
            "NEEDS ATTENTION - Too Small": "quality"
        }

        for cat_folder, cat_type in categories.items():
            cat_path = self.review_dir / cat_folder
            if not cat_path.exists():
                continue

            # For duplicates and bursts, each subfolder is a group
            if cat_type in ['duplicates', 'burst']:
                for subfolder in cat_path.iterdir():
                    if subfolder.is_dir():
                        group = PhotoGroup(subfolder, cat_type)
                        if group.photos:
                            groups.append(group)
            else:
                # For quality issues, the category folder itself contains photos
                if any(cat_path.iterdir()):
                    group = PhotoGroup(cat_path, cat_type)
                    if group.photos:
                        groups.append(group)

        return groups

    def create_ui(self):
        """Create the user interface"""

        # Header
        header = tk.Frame(self.window, bg=self.WARNING, height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="👀 Review Flagged Photos",
            font=("Segoe UI", 22, "bold"),
            bg=self.WARNING,
            fg=self.BG_DARK
        )
        title.pack(pady=(15, 5))

        # Counter
        self.counter_label = tk.Label(
            header,
            text=f"Group 1 of {len(self.groups)}",
            font=("Segoe UI", 11),
            bg=self.WARNING,
            fg=self.BG_DARK
        )
        self.counter_label.pack()

        # Main content
        content = tk.Frame(self.window, bg=self.BG_DARK)
        content.pack(fill=tk.BOTH, expand=True)

        # Left panel: Photo list
        left_panel = tk.Frame(content, bg=self.BG_SURFACE, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(20, 10), pady=20)
        left_panel.pack_propagate(False)

        tk.Label(
            left_panel,
            text="Photos in Group",
            font=("Segoe UI", 12, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        ).pack(pady=(10, 10))

        # Photo listbox
        list_frame = tk.Frame(left_panel, bg=self.BG_SURFACE)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.photo_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 9),
            bg=self.BG_DARK,
            fg=self.TEXT_PRIMARY,
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT
        )
        self.photo_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.photo_listbox.yview)

        self.photo_listbox.bind('<<ListboxSelect>>', self.on_photo_select)

        # Right panel: Preview and actions
        right_panel = tk.Frame(content, bg=self.BG_SURFACE)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 20), pady=20)

        # Group info
        info_frame = tk.Frame(right_panel, bg=self.BG_SURFACE)
        info_frame.pack(fill=tk.X, padx=20, pady=(10, 10))

        self.group_name_label = tk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 14, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY,
            anchor=tk.W
        )
        self.group_name_label.pack(fill=tk.X)

        self.group_desc_label = tk.Label(
            info_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.BG_SURFACE,
            fg=self.TEXT_SECONDARY,
            anchor=tk.W
        )
        self.group_desc_label.pack(fill=tk.X, pady=(5, 0))

        # Photo preview
        preview_frame = tk.Frame(right_panel, bg=self.BG_DARK, relief=tk.FLAT)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.preview_label = tk.Label(
            preview_frame,
            text="Select a photo to preview",
            font=("Segoe UI", 12),
            bg=self.BG_DARK,
            fg=self.TEXT_SECONDARY
        )
        self.preview_label.pack(expand=True)

        # Photo info
        self.photo_info_label = tk.Label(
            right_panel,
            text="",
            font=("Segoe UI", 9),
            bg=self.BG_SURFACE,
            fg=self.TEXT_SECONDARY,
            justify=tk.LEFT
        )
        self.photo_info_label.pack(padx=20, pady=(0, 10))

        # Action buttons
        action_frame = tk.Frame(right_panel, bg=self.BG_SURFACE)
        action_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Quick actions for groups
        tk.Label(
            action_frame,
            text="Quick Actions:",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_SURFACE,
            fg=self.TEXT_PRIMARY
        ).pack(anchor=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(action_frame, bg=self.BG_SURFACE)
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        self.keep_best_btn = tk.Button(
            btn_frame,
            text="⭐ Keep Best Only",
            command=self.keep_best_only,
            bg=self.SUCCESS,
            fg=self.BG_DARK,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        self.keep_best_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.keep_all_btn = tk.Button(
            btn_frame,
            text="Keep All",
            command=self.keep_all,
            bg=self.PRIMARY,
            fg=self.BG_DARK,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        self.keep_all_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 5))

        self.delete_all_btn = tk.Button(
            btn_frame,
            text="❌ Delete All",
            command=self.delete_all,
            bg=self.DANGER,
            fg=self.BG_DARK,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=10
        )
        self.delete_all_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Navigation
        nav_frame = tk.Frame(self.window, bg=self.BG_DARK, height=70)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=(0, 20))
        nav_frame.pack_propagate(False)

        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Previous Group",
            command=self.prev_group,
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12,
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.skip_btn = tk.Button(
            nav_frame,
            text="Skip (Decide Later)",
            command=self.skip_group,
            bg=self.WARNING,
            fg=self.BG_DARK,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12
        )
        self.skip_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))

        self.next_btn = tk.Button(
            nav_frame,
            text="Next Group ▶",
            command=self.next_group,
            bg=self.SUCCESS,
            fg=self.BG_DARK,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12
        )
        self.next_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.done_btn = tk.Button(
            nav_frame,
            text="✅ Finish Review",
            command=self.finish_review,
            bg=self.PRIMARY,
            fg=self.BG_DARK,
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            pady=12,
            padx=30
        )
        self.done_btn.pack(side=tk.RIGHT)

    def load_group(self, idx: int):
        """Load a specific group"""
        if idx < 0 or idx >= len(self.groups):
            return

        self.current_group_idx = idx
        group = self.groups[idx]

        # Update counter
        self.counter_label.config(text=f"Group {idx + 1} of {len(self.groups)}")

        # Update group info
        self.group_name_label.config(text=group.name)

        category_labels = {
            'duplicates': '👯 Duplicate Photos',
            'burst': '📸 Burst Photo Sequence',
            'quality': '⚠️ Quality Issues'
        }
        desc = category_labels.get(group.category, 'Unknown')
        desc += f" - {group.count} photo(s)"
        self.group_desc_label.config(text=desc)

        # Populate photo list
        self.photo_listbox.delete(0, tk.END)
        for photo in group.photos:
            name = photo.name
            if photo == group.best_photo:
                name = f"⭐ {name.replace('BEST_', '')}"
            size_kb = photo.stat().st_size / 1024
            self.photo_listbox.insert(tk.END, f"{name} ({size_kb:.1f} KB)")

        # Select first photo
        if group.photos:
            self.photo_listbox.selection_set(0)
            self.on_photo_select(None)

        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if idx > 0 else tk.DISABLED)
        self.next_btn.config(
            text="Next Group ▶" if idx < len(self.groups) - 1 else "Last Group"
        )

    def on_photo_select(self, event):
        """Handle photo selection"""
        selection = self.photo_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        group = self.groups[self.current_group_idx]
        photo = group.photos[idx]
        self.selected_photo = photo

        # Load and display image
        try:
            img = Image.open(photo)

            # Resize to fit preview (maintain aspect ratio)
            max_size = (600, 400)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo_img = ImageTk.PhotoImage(img)

            # Update preview
            self.preview_label.config(image=photo_img, text="")
            self.preview_label.image = photo_img  # Keep reference

            # Update info
            info = f"File: {photo.name}\n"
            info += f"Size: {photo.stat().st_size / 1024:.1f} KB\n"
            info += f"Dimensions: {img.width} x {img.height} pixels"
            if photo == group.best_photo:
                info += "\n⭐ Recommended as best quality"
            self.photo_info_label.config(text=info)

        except Exception as e:
            self.preview_label.config(
                text=f"Cannot preview this file\n{str(e)}",
                image=""
            )
            self.photo_info_label.config(text=f"File: {photo.name}\nError loading preview")

    def keep_best_only(self):
        """Keep only the recommended best photo"""
        group = self.groups[self.current_group_idx]
        if group.best_photo:
            self.decisions[group.folder] = [group.best_photo]
            self.next_group()

    def keep_all(self):
        """Keep all photos in group"""
        group = self.groups[self.current_group_idx]
        self.decisions[group.folder] = group.photos.copy()
        self.next_group()

    def delete_all(self):
        """Delete all photos in group"""
        result = messagebox.askyesno(
            "Confirm Delete All",
            "Are you sure you want to delete ALL photos in this group?\n\n"
            "This cannot be undone!",
            icon='warning'
        )
        if result:
            self.decisions[self.groups[self.current_group_idx].folder] = []
            self.next_group()

    def skip_group(self):
        """Skip this group, decide later"""
        # Don't record a decision
        self.next_group()

    def prev_group(self):
        """Go to previous group"""
        if self.current_group_idx > 0:
            self.load_group(self.current_group_idx - 1)

    def next_group(self):
        """Go to next group"""
        if self.current_group_idx < len(self.groups) - 1:
            self.load_group(self.current_group_idx + 1)
        else:
            # Last group
            self.finish_review()

    def finish_review(self):
        """Finish the review and apply decisions"""
        # Count skipped groups
        skipped = len(self.groups) - len(self.decisions)

        if skipped > 0:
            result = messagebox.askyesno(
                "Confirm Finish",
                f"You have {skipped} group(s) that you haven't decided on.\n\n"
                "These will remain in the review folder.\n\n"
                "Continue anyway?",
                icon='question'
            )
            if not result:
                return

        # Apply decisions
        self.apply_decisions()

        # Show summary
        kept = sum(len(photos) for photos in self.decisions.values())
        deleted = sum(
            group.count - len(self.decisions.get(group.folder, group.photos))
            for group in self.groups
        )

        messagebox.showinfo(
            "Review Complete",
            f"Review complete!\n\n"
            f"• Kept: {kept} photos\n"
            f"• Deleted: {deleted} photos\n"
            f"• Skipped: {skipped} groups\n\n"
            "Kept photos have been moved to your library."
        )

        self.window.destroy()

    def apply_decisions(self):
        """Apply all decisions (move/delete files)"""
        for group_folder, photos_to_keep in self.decisions.items():
            group_folder = Path(group_folder)

            # Get all photos in folder
            all_photos = []
            image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.webp'}
            for ext in image_extensions:
                all_photos.extend(list(group_folder.glob(f"*{ext}")))
                all_photos.extend(list(group_folder.glob(f"*{ext.upper()}")))

            # Delete photos not in keep list
            for photo in all_photos:
                if photo not in photos_to_keep:
                    try:
                        photo.unlink()
                        # Also delete companion JSON if exists
                        json_file = photo.with_suffix(photo.suffix + '.json')
                        if json_file.exists():
                            json_file.unlink()
                    except Exception as e:
                        print(f"Error deleting {photo}: {e}")

            # Move kept photos to library
            for photo in photos_to_keep:
                try:
                    self._move_to_library(photo)
                except Exception as e:
                    print(f"Error moving {photo}: {e}")

            # Remove empty group folder
            try:
                if group_folder.exists() and not any(group_folder.iterdir()):
                    group_folder.rmdir()
            except:
                pass

    def _move_to_library(self, photo: Path):
        """Move a photo to the Photos & Videos library"""
        # Try to get date from exif or filename
        # For now, use modification time
        from datetime import datetime
        date = datetime.fromtimestamp(photo.stat().st_mtime)

        # Create folder: YYYY/YYYY-MM-Month/
        year = date.strftime('%Y')
        month = date.strftime('%Y-%m-%B')

        dest_dir = self.photos_dir / year / month
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Remove BEST_ prefix if present
        dest_name = photo.name.replace('BEST_', '')
        dest = dest_dir / dest_name

        # Handle duplicates in destination
        counter = 1
        while dest.exists():
            stem = photo.stem.replace('BEST_', '')
            suffix = photo.suffix
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # Move file
        shutil.move(str(photo), str(dest))

        # Move JSON if exists
        json_file = photo.with_suffix(photo.suffix + '.json')
        if json_file.exists():
            json_dest = dest_dir / (dest.name + '.json')
            shutil.move(str(json_file), str(json_dest))

    def center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
