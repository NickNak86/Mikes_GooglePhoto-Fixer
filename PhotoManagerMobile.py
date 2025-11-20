"""
Google Photos Manager - Mobile Edition (Kivy)
==============================================
Cross-platform mobile app with Android-first design

Author: Claude Code
Date: 2025-11-20
Version: 2.1 Mobile
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.list import MDList, TwoLineListItem, ThreeLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.swiper import MDSwiper, MDSwiperItem
from kivy.uix.image import AsyncImage
from kivy.metrics import dp
from kivy.clock import Clock
from pathlib import Path
import json
import threading

# Import our processor
try:
    from PhotoProcessorEnhanced import PhotoProcessorEnhanced, ProcessingProgress, ProcessingIssue
except:
    from PhotoProcessor import PhotoProcessor as PhotoProcessorEnhanced
    ProcessingProgress = None
    ProcessingIssue = None

# Import mobile utilities
from mobile_utils import MobilePlatform, ConfigManager, StorageHelper


class MainScreen(MDScreen):
    """Main menu screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        self.config = ConfigManager()

        # Request permissions on Android
        if MobilePlatform.is_android():
            MobilePlatform.request_storage_permissions()

        # Top bar
        toolbar = MDTopAppBar(
            title="📸 Photos Manager",
            md_bg_color=(0.73, 0.53, 0.99, 1),  # Material Purple
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["menu", lambda x: self.open_drawer()]],
            right_action_items=[["cog", lambda x: self.open_settings()]]
        )
        self.add_widget(toolbar)

        # Statistics card
        stats_card = MDCard(
            size_hint=(0.9, None),
            height=dp(120),
            pos_hint={'center_x': 0.5, 'center_y': 0.75},
            elevation=4,
            padding=dp(16)
        )

        self.stats_label = MDLabel(
            text="📊 Library Statistics\n• Loading...",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='left',
            valign='top'
        )
        stats_card.add_widget(self.stats_label)
        self.add_widget(stats_card)

        # Load statistics
        Clock.schedule_once(lambda dt: self.load_statistics(), 0.5)

        # Action buttons
        self.process_btn = MDRaisedButton(
            text="🚀 Process New Takeout",
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            size_hint=(0.85, None),
            height=dp(56),
            md_bg_color=(0.73, 0.53, 0.99, 1),
            on_release=self.start_processing
        )
        self.add_widget(self.process_btn)

        self.review_btn = MDRaisedButton(
            text="👀 Review Flagged Photos",
            pos_hint={'center_x': 0.5, 'center_y': 0.42},
            size_hint=(0.85, None),
            height=dp(56),
            md_bg_color=(1, 0.65, 0.15, 1),  # Material Orange
            on_release=self.open_review
        )
        self.add_widget(self.review_btn)

        self.browse_btn = MDRaisedButton(
            text="📁 Browse Library",
            pos_hint={'center_x': 0.5, 'center_y': 0.29},
            size_hint=(0.85, None),
            height=dp(56),
            md_bg_color=(0.3, 0.69, 0.31, 1),  # Material Green
            on_release=self.browse_library
        )
        self.add_widget(self.browse_btn)

    def load_statistics(self):
        """Load and display library statistics"""
        try:
            base_path = Path(self.config.get('base_path'))
            photos_dir = base_path / "Photos & Videos"

            # Count photos
            photo_count = StorageHelper.get_photo_count(photos_dir)

            # Get folder size
            total_size = StorageHelper.get_folder_size(photos_dir)
            size_str = StorageHelper.format_size(total_size)

            # Check for items needing review
            review_folders = StorageHelper.get_review_folders(base_path)
            review_count = sum(StorageHelper.get_photo_count(folder) for folder in review_folders.values())

            # Update label
            stats_text = f"📊 Library Statistics\n"
            stats_text += f"• {photo_count:,} photos\n"
            stats_text += f"• {size_str} total\n"
            if review_count > 0:
                stats_text += f"• {review_count} need review"
            else:
                stats_text += f"• All photos reviewed ✓"

            self.stats_label.text = stats_text

        except Exception as e:
            self.stats_label.text = f"📊 Library Statistics\n• Error loading: {e}"

    def open_drawer(self):
        """Open navigation drawer"""
        pass

    def open_settings(self):
        """Open settings screen"""
        self.manager.current = 'settings'

    def start_processing(self, instance):
        """Start photo processing"""
        # Check permissions first
        if MobilePlatform.is_android() and not MobilePlatform.check_storage_permissions():
            self.show_permission_error()
            return

        self.manager.current = 'processing'
        # Trigger processing
        self.manager.get_screen('processing').start_processing()

    def open_review(self, instance):
        """Open review screen"""
        # Reload review screen data
        self.manager.get_screen('review').reload_groups()
        self.manager.current = 'review'

    def browse_library(self, instance):
        """Browse photo library"""
        # TODO: Implement gallery view
        pass

    def show_permission_error(self):
        """Show permission error dialog"""
        dialog = MDDialog(
            title="⚠️ Permissions Required",
            text="Storage permissions are needed to access your photos.",
            buttons=[
                MDFlatButton(
                    text="REQUEST",
                    on_release=lambda x: self.request_permissions_again(dialog)
                ),
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def request_permissions_again(self, dialog):
        """Request permissions again"""
        dialog.dismiss()
        MobilePlatform.request_storage_permissions()


class ProcessingScreen(MDScreen):
    """Processing progress screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'processing'
        self.processor = None

        # Top bar
        toolbar = MDTopAppBar(
            title="Processing...",
            md_bg_color=(0.73, 0.53, 0.99, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self.cancel_processing()]]
        )
        self.add_widget(toolbar)

        # Status label
        self.status_label = MDLabel(
            text="Initializing...",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.7},
            font_style='H6'
        )
        self.add_widget(self.status_label)

        # Progress bar
        self.progress_bar = MDProgressBar(
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            size_hint_x=0.8
        )
        self.add_widget(self.progress_bar)

        # Details label
        self.details_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=(0.7, 0.7, 0.7, 1),
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.details_label)

        # Cancel button
        self.cancel_btn = MDRaisedButton(
            text="Cancel",
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            size_hint=(0.5, None),
            height=dp(48),
            md_bg_color=(0.91, 0.40, 0.47, 1),  # Material Pink-Red
            on_release=lambda x: self.cancel_processing()
        )
        self.add_widget(self.cancel_btn)

    def start_processing(self):
        """Start the processing pipeline"""
        # Get settings
        config = ConfigManager()

        # Create processor
        self.processor = PhotoProcessorEnhanced(
            base_path=config.get('base_path'),
            max_workers=config.get('max_workers', 2)
        )

        # Set callbacks
        self.processor.progress_callback = self.update_progress
        self.processor.status_callback = self.update_status

        # Run in background thread
        thread = threading.Thread(target=self._run_processing, daemon=True)
        thread.start()

    def _run_processing(self):
        """Background processing thread"""
        try:
            stats, issues = self.processor.run_full_pipeline()

            # Show completion on main thread
            Clock.schedule_once(lambda dt: self.show_completion(stats, issues), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)

    def update_progress(self, progress: ProcessingProgress):
        """Update progress UI"""
        def update(dt):
            self.progress_bar.value = progress.percent_complete()
            eta = progress.calculate_eta()
            if eta:
                self.details_label.text = f"ETA: {eta}"

        Clock.schedule_once(update, 0)

    def update_status(self, message: str):
        """Update status message"""
        def update(dt):
            self.status_label.text = message

        Clock.schedule_once(update, 0)

    def cancel_processing(self):
        """Cancel processing and return to main"""
        if self.processor:
            self.processor.cancel()
        self.manager.current = 'main'

    def show_completion(self, stats: dict, issues: list):
        """Show completion dialog"""
        summary = f"""
Processing Complete! 🎉

• Total files: {stats['total_processed']}
• Duplicates: {stats['duplicates_found']}
• Blurry: {stats['blurry_found']}
• Bursts: {stats['bursts_found']}

{len(issues)} items need review
        """

        dialog = MDDialog(
            title="✅ Processing Complete!",
            text=summary,
            buttons=[
                MDFlatButton(
                    text="REVIEW",
                    on_release=lambda x: self.open_review_from_dialog(dialog)
                ),
                MDFlatButton(
                    text="CLOSE",
                    on_release=lambda x: self.close_dialog(dialog)
                )
            ]
        )
        dialog.open()

    def open_review_from_dialog(self, dialog):
        """Open review screen from dialog"""
        dialog.dismiss()
        self.manager.current = 'review'

    def close_dialog(self, dialog):
        """Close dialog and return to main"""
        dialog.dismiss()
        # Refresh main screen statistics
        main_screen = self.manager.get_screen('main')
        main_screen.load_statistics()
        self.manager.current = 'main'

    def show_error(self, error: str):
        """Show error dialog"""
        dialog = MDDialog(
            title="❌ Error",
            text=f"An error occurred:\n\n{error}",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.close_dialog(dialog)
                )
            ]
        )
        dialog.open()


class ReviewScreen(MDScreen):
    """Photo review screen with swipe gestures"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'review'
        self.config = ConfigManager()
        self.photo_groups = []
        self.current_group_index = 0
        self.decisions = {}  # Track user decisions

        # Top bar
        self.toolbar = MDTopAppBar(
            title="Review Photos (0/0)",
            md_bg_color=(1, 0.65, 0.15, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        self.add_widget(self.toolbar)

        # Photo display area
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout

        scroll = ScrollView(
            size_hint=(1, 0.7),
            pos_hint={'center_x': 0.5, 'y': 0.2}
        )

        self.photo_grid = GridLayout(
            cols=2,
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=None
        )
        self.photo_grid.bind(minimum_height=self.photo_grid.setter('height'))

        scroll.add_widget(self.photo_grid)
        self.add_widget(scroll)

        # Info label (category, count, etc.)
        self.info_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign='center',
            size_hint=(1, 0.08),
            pos_hint={'center_x': 0.5, 'y': 0.12}
        )
        self.add_widget(self.info_label)

        # Action buttons
        button_layout_y = 0.02

        self.keep_btn = MDRaisedButton(
            text="✓ Keep Best",
            pos_hint={'x': 0.05, 'y': button_layout_y},
            size_hint=(0.28, None),
            height=dp(48),
            md_bg_color=(0.3, 0.69, 0.31, 1),
            on_release=self.keep_best
        )
        self.add_widget(self.keep_btn)

        self.skip_btn = MDRaisedButton(
            text="Skip",
            pos_hint={'center_x': 0.5, 'y': button_layout_y},
            size_hint=(0.28, None),
            height=dp(48),
            md_bg_color=(0.5, 0.5, 0.5, 1),
            on_release=self.skip_group
        )
        self.add_widget(self.skip_btn)

        self.delete_btn = MDRaisedButton(
            text="✗ Delete All",
            pos_hint={'x': 0.67, 'y': button_layout_y},
            size_hint=(0.28, None),
            height=dp(48),
            md_bg_color=(0.91, 0.40, 0.47, 1),
            on_release=self.delete_all
        )
        self.add_widget(self.delete_btn)

    def reload_groups(self):
        """Reload photo groups from review folders"""
        self.photo_groups = []
        self.current_group_index = 0
        self.decisions = {}

        # Load photos from review folders
        base_path = Path(self.config.get('base_path'))
        review_folders = StorageHelper.get_review_folders(base_path)

        for category, folder in review_folders.items():
            if folder.exists():
                # Get all subfolders (each subfolder is a group)
                for group_folder in folder.iterdir():
                    if group_folder.is_dir():
                        photos = list(group_folder.glob('*'))
                        photos = [p for p in photos if p.suffix.lower() in
                                 {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.gif', '.bmp', '.webp'}]

                        if photos:
                            self.photo_groups.append({
                                'category': category,
                                'folder': group_folder,
                                'photos': photos,
                                'name': group_folder.name
                            })

        # Display first group
        if self.photo_groups:
            self.display_current_group()
        else:
            self.show_empty_state()

    def display_current_group(self):
        """Display the current photo group"""
        if not self.photo_groups or self.current_group_index >= len(self.photo_groups):
            self.show_completion()
            return

        group = self.photo_groups[self.current_group_index]

        # Update toolbar
        self.toolbar.title = f"Review Photos ({self.current_group_index + 1}/{len(self.photo_groups)})"

        # Update info label
        category_names = {
            'too_small': 'Too Small',
            'blur_corrupt': 'Blurry/Corrupt',
            'burst': 'Burst Photos',
            'duplicates': 'Duplicates'
        }
        cat_name = category_names.get(group['category'], group['category'])
        self.info_label.text = f"{cat_name}: {group['name']}\n{len(group['photos'])} photos"

        # Clear and populate photo grid
        self.photo_grid.clear_widgets()

        for photo_path in group['photos'][:6]:  # Show max 6 photos
            try:
                # Use AsyncImage for efficient loading
                img = AsyncImage(
                    source=str(photo_path),
                    size_hint_y=None,
                    height=dp(150),
                    allow_stretch=True,
                    keep_ratio=True
                )
                self.photo_grid.add_widget(img)
            except Exception as e:
                # If image fails to load, show placeholder
                placeholder = MDLabel(
                    text=f"[Error]\n{photo_path.name}",
                    halign='center',
                    size_hint_y=None,
                    height=dp(150)
                )
                self.photo_grid.add_widget(placeholder)

    def show_empty_state(self):
        """Show empty state when no photos to review"""
        self.toolbar.title = "Review Photos (0/0)"
        self.info_label.text = "No photos to review! 🎉"
        self.photo_grid.clear_widgets()

        placeholder = MDLabel(
            text="All photos have been reviewed\n\nRun processing to find more items",
            halign='center',
            valign='center'
        )
        self.photo_grid.add_widget(placeholder)

    def show_completion(self):
        """Show completion dialog"""
        # Apply all decisions
        self.apply_decisions()

        dialog = MDDialog(
            title="✅ Review Complete!",
            text=f"Reviewed {len(self.decisions)} groups of photos",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.close_completion_dialog(dialog)
                )
            ]
        )
        dialog.open()

    def close_completion_dialog(self, dialog):
        """Close completion dialog"""
        dialog.dismiss()
        self.manager.current = 'main'

    def keep_best(self, instance):
        """Keep only the best photo in the group"""
        if not self.photo_groups or self.current_group_index >= len(self.photo_groups):
            return

        group = self.photo_groups[self.current_group_index]
        # Keep first photo (processor should have sorted by quality)
        self.decisions[str(group['folder'])] = {
            'action': 'keep_best',
            'keep': [group['photos'][0]] if group['photos'] else []
        }

        self.next_group()

    def skip_group(self, instance):
        """Skip current group"""
        self.next_group()

    def delete_all(self, instance):
        """Delete all photos in group"""
        if not self.photo_groups or self.current_group_index >= len(self.photo_groups):
            return

        group = self.photo_groups[self.current_group_index]
        self.decisions[str(group['folder'])] = {
            'action': 'delete_all',
            'keep': []
        }

        self.next_group()

    def next_group(self):
        """Move to next group"""
        self.current_group_index += 1
        self.display_current_group()

    def apply_decisions(self):
        """Apply user decisions (keep/delete)"""
        import shutil

        for folder_path, decision in self.decisions.items():
            folder = Path(folder_path)

            if not folder.exists():
                continue

            if decision['action'] == 'keep_best' and decision['keep']:
                # Delete all except kept photos
                keep_set = set(decision['keep'])
                for photo in folder.iterdir():
                    if photo.is_file() and photo not in keep_set:
                        try:
                            photo.unlink()
                        except:
                            pass
            elif decision['action'] == 'delete_all':
                # Delete entire folder
                try:
                    shutil.rmtree(folder)
                except:
                    pass

    def go_back(self):
        """Return to main screen"""
        self.manager.current = 'main'


class SettingsScreen(MDScreen):
    """Settings screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'

        # Top bar
        toolbar = MDTopAppBar(
            title="⚙️ Settings",
            md_bg_color=(0.73, 0.53, 0.99, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        self.add_widget(toolbar)

        # Settings list
        settings_list = MDList()
        # TODO: Add actual settings

        placeholder = MDLabel(
            text="Settings coming soon...",
            halign='center',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(placeholder)

    def go_back(self):
        """Return to main screen"""
        self.manager.current = 'main'


class PhotosManagerMobileApp(MDApp):
    """Main mobile application"""

    def build(self):
        """Build the app"""
        # Set theme
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.material_style = "M3"  # Material You

        # Screen manager
        sm = ScreenManager(transition=SlideTransition())

        # Add screens
        sm.add_widget(MainScreen())
        sm.add_widget(ProcessingScreen())
        sm.add_widget(ReviewScreen())
        sm.add_widget(SettingsScreen())

        return sm


if __name__ == '__main__':
    PhotosManagerMobileApp().run()
