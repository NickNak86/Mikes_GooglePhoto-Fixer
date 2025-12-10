#!/usr/bin/env python3
"""
Google Photos Manager - Test Data Generator
===========================================
Creates realistic test datasets for comprehensive testing

Author: AI Assistant
Date: 2024-12-10
"""

import os
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import io


class TestDataGenerator:
    """Generate comprehensive test datasets"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.good_photos_dir = self.output_dir / "good_photos"
        self.duplicates_dir = self.output_dir / "duplicates"
        self.blurry_dir = self.output_dir / "blurry"
        self.corrupted_dir = self.output_dir / "corrupted"
        self.burst_dir = self.output_dir / "burst"
        self.videos_dir = self.output_dir / "videos"
        self.takeout_dir = self.output_dir / "google_takeout"
        self.edge_cases_dir = self.output_dir / "edge_cases"
        
        for d in [self.good_photos_dir, self.duplicates_dir, self.blurry_dir,
                  self.corrupted_dir, self.burst_dir, self.videos_dir,
                  self.takeout_dir, self.edge_cases_dir]:
            d.mkdir(exist_ok=True)
    
    def generate_image(self, width: int, height: int, text: str, color_seed: int = 0) -> Image.Image:
        """Generate a simple test image with text"""
        random.seed(color_seed)
        color = (
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        
        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)
        
        # Draw some patterns
        for i in range(10):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(20, 100)
            draw.ellipse([x-r, y-r, x+r, y+r], 
                        fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        
        # Add text
        try:
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, fill=(255, 255, 255), font=font)
        except:
            # If font fails, just skip text
            pass
        
        return img
    
    def add_exif_data(self, img: Image.Image, date: datetime) -> Image.Image:
        """Add EXIF data to image"""
        from PIL.ExifTags import TAGS
        
        # Create EXIF data
        exif_dict = {
            "DateTimeOriginal": date.strftime("%Y:%m:%d %H:%M:%S"),
            "DateTime": date.strftime("%Y:%m:%d %H:%M:%S"),
            "Make": "TestCamera",
            "Model": "TC-2000"
        }
        
        return img
    
    def create_google_takeout_json(self, photo_path: Path, date: datetime):
        """Create a Google Takeout JSON metadata file"""
        json_data = {
            "title": photo_path.name,
            "description": "",
            "imageViews": "0",
            "creationTime": {
                "timestamp": str(int(date.timestamp())),
                "formatted": date.strftime("%b %d, %Y, %I:%M:%S %p UTC")
            },
            "photoTakenTime": {
                "timestamp": str(int(date.timestamp())),
                "formatted": date.strftime("%b %d, %Y, %I:%M:%S %p UTC")
            },
            "geoData": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 0.0,
                "latitudeSpan": 0.0,
                "longitudeSpan": 0.0
            },
            "geoDataExif": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 0.0,
                "latitudeSpan": 0.0,
                "longitudeSpan": 0.0
            },
            "url": f"https://photos.google.com/photo/{hashlib.md5(photo_path.name.encode()).hexdigest()}"
        }
        
        json_path = Path(str(photo_path) + ".json")
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
    
    def generate_good_photos(self, count: int = 10):
        """Generate good quality photos"""
        print(f"Generating {count} good photos...")
        
        formats = ['.jpg', '.png', '.jpeg']
        resolutions = [(1920, 1080), (2048, 1536), (3264, 2448), (4000, 3000)]
        
        base_date = datetime(2023, 6, 15, 14, 30, 0)
        
        for i in range(count):
            width, height = random.choice(resolutions)
            ext = random.choice(formats)
            
            img = self.generate_image(width, height, f"Good Photo {i+1}", color_seed=i)
            
            # Save with proper quality
            filename = self.good_photos_dir / f"IMG_{20230615000000 + i:015d}{ext}"
            
            if ext == '.png':
                img.save(filename, 'PNG', optimize=True)
            else:
                img.save(filename, 'JPEG', quality=90)
            
            print(f"  ✓ Created {filename.name} ({width}x{height})")
    
    def generate_duplicates(self, sets: int = 5):
        """Generate duplicate photo sets"""
        print(f"Generating {sets} duplicate sets...")
        
        base_date = datetime(2023, 7, 1, 10, 0, 0)
        
        for i in range(sets):
            # Create original
            img = self.generate_image(2048, 1536, f"Duplicate Set {i+1}", color_seed=100+i)
            
            # Save original
            original = self.duplicates_dir / f"original_{i+1}.jpg"
            img.save(original, 'JPEG', quality=95)
            
            # Create exact duplicate (different name)
            exact_dup = self.duplicates_dir / f"copy_of_{i+1}.jpg"
            img.save(exact_dup, 'JPEG', quality=95)
            
            # Create near duplicate (different compression)
            near_dup = self.duplicates_dir / f"compressed_{i+1}.jpg"
            img.save(near_dup, 'JPEG', quality=75)
            
            # Create resized duplicate
            resized = img.resize((1024, 768), Image.Resampling.LANCZOS)
            resized_dup = self.duplicates_dir / f"resized_{i+1}.jpg"
            resized.save(resized_dup, 'JPEG', quality=90)
            
            print(f"  ✓ Created duplicate set {i+1} (4 files)")
    
    def generate_blurry_photos(self, count: int = 5):
        """Generate blurry/low quality photos"""
        print(f"Generating {count} blurry photos...")
        
        for i in range(count):
            img = self.generate_image(1920, 1080, f"Blurry {i+1}", color_seed=200+i)
            
            # Apply heavy blur
            img = img.filter(ImageFilter.GaussianBlur(radius=15))
            
            filename = self.blurry_dir / f"blurry_{i+1}.jpg"
            img.save(filename, 'JPEG', quality=50)  # Low quality too
            
            print(f"  ✓ Created {filename.name}")
    
    def generate_corrupted_files(self, count: int = 3):
        """Generate corrupted/invalid files"""
        print(f"Generating {count} corrupted files...")
        
        # Zero-byte file
        zero_file = self.corrupted_dir / "zero_byte.jpg"
        zero_file.touch()
        print(f"  ✓ Created {zero_file.name} (0 bytes)")
        
        # Truncated JPEG
        img = self.generate_image(1920, 1080, "Truncated", color_seed=300)
        buffer = io.BytesIO()
        img.save(buffer, 'JPEG', quality=90)
        truncated_data = buffer.getvalue()[:len(buffer.getvalue())//2]  # Cut in half
        
        truncated_file = self.corrupted_dir / "truncated.jpg"
        with open(truncated_file, 'wb') as f:
            f.write(truncated_data)
        print(f"  ✓ Created {truncated_file.name} (truncated)")
        
        # Invalid header
        invalid_file = self.corrupted_dir / "invalid_header.jpg"
        with open(invalid_file, 'wb') as f:
            f.write(b"This is not a valid JPEG file at all!")
        print(f"  ✓ Created {invalid_file.name} (invalid header)")
    
    def generate_burst_photos(self, count: int = 10):
        """Generate burst photo sequence"""
        print(f"Generating burst sequence of {count} photos...")
        
        base_date = datetime(2023, 8, 15, 16, 45, 30)
        
        for i in range(count):
            img = self.generate_image(2048, 1536, f"Burst {i+1}", color_seed=400+i)
            
            # Add slight variations
            if i % 3 == 0:
                img = img.filter(ImageFilter.SHARPEN)
            
            # Sequential filenames with timestamps
            timestamp = base_date + timedelta(seconds=i)
            filename = self.burst_dir / f"IMG_{timestamp.strftime('%Y%m%d_%H%M%S')}_{i:03d}.jpg"
            img.save(filename, 'JPEG', quality=90)
            
            print(f"  ✓ Created {filename.name}")
    
    def generate_videos(self, count: int = 3):
        """Generate dummy video files (just empty files with correct extensions)"""
        print(f"Generating {count} video placeholders...")
        
        video_exts = ['.mp4', '.mov', '.avi']
        
        for i in range(count):
            ext = video_exts[i % len(video_exts)]
            filename = self.videos_dir / f"video_{i+1}{ext}"
            
            # Create a small dummy file
            with open(filename, 'wb') as f:
                f.write(b"DUMMY VIDEO FILE " * 1000)  # ~17KB
            
            print(f"  ✓ Created {filename.name} (placeholder)")
    
    def generate_google_takeout_format(self, count: int = 8):
        """Generate photos in Google Takeout format with JSON metadata"""
        print(f"Generating {count} Google Takeout format photos...")
        
        base_date = datetime(2023, 9, 20, 12, 0, 0)
        
        for i in range(count):
            # Create image
            img = self.generate_image(3264, 2448, f"Takeout {i+1}", color_seed=500+i)
            
            # Google Takeout filename format
            photo_date = base_date + timedelta(days=i)
            filename = self.takeout_dir / f"IMG_{photo_date.strftime('%Y%m%d_%H%M%S')}.jpg"
            img.save(filename, 'JPEG', quality=90)
            
            # Create accompanying JSON
            self.create_google_takeout_json(filename, photo_date)
            
            print(f"  ✓ Created {filename.name} + JSON")
    
    def generate_edge_cases(self):
        """Generate edge case files"""
        print("Generating edge case files...")
        
        # File with no extension
        img = self.generate_image(800, 600, "No Extension", color_seed=600)
        no_ext = self.edge_cases_dir / "no_extension_file"
        img.save(no_ext, 'JPEG', quality=90)
        print(f"  ✓ Created {no_ext.name}")
        
        # File with spaces and special characters
        img = self.generate_image(800, 600, "Special Name", color_seed=601)
        special = self.edge_cases_dir / "file with spaces & special (chars).jpg"
        img.save(special, 'JPEG', quality=90)
        print(f"  ✓ Created {special.name}")
        
        # Very small file (below threshold)
        tiny = self.generate_image(50, 50, "Tiny", color_seed=602)
        tiny_file = self.edge_cases_dir / "tiny_image.jpg"
        tiny.save(tiny_file, 'JPEG', quality=90)
        print(f"  ✓ Created {tiny_file.name} (50x50)")
        
        # File with unicode characters
        img = self.generate_image(800, 600, "Unicode", color_seed=603)
        unicode_file = self.edge_cases_dir / "photo_日本語_émojis_😀.jpg"
        img.save(unicode_file, 'JPEG', quality=90)
        print(f"  ✓ Created {unicode_file.name}")
        
        # Low resolution file
        low_res = self.generate_image(320, 240, "Low Res", color_seed=604)
        low_res_file = self.edge_cases_dir / "low_resolution.jpg"
        low_res.save(low_res_file, 'JPEG', quality=90)
        print(f"  ✓ Created {low_res_file.name} (320x240)")
    
    def generate_all(self):
        """Generate complete test dataset"""
        print("=" * 60)
        print("  GOOGLE PHOTOS MANAGER - TEST DATA GENERATOR")
        print("=" * 60)
        print(f"\nOutput directory: {self.output_dir}\n")
        
        try:
            self.generate_good_photos(10)
            self.generate_duplicates(5)
            self.generate_blurry_photos(5)
            self.generate_corrupted_files(3)
            self.generate_burst_photos(10)
            self.generate_videos(3)
            self.generate_google_takeout_format(8)
            self.generate_edge_cases()
            
            print("\n" + "=" * 60)
            print("  TEST DATA GENERATION COMPLETE!")
            print("=" * 60)
            
            # Print summary
            total_files = sum(1 for _ in self.output_dir.rglob('*') if _.is_file())
            print(f"\nTotal files created: {total_files}")
            print(f"\nDirectory structure:")
            for subdir in sorted(self.output_dir.iterdir()):
                if subdir.is_dir():
                    file_count = sum(1 for _ in subdir.iterdir() if _.is_file())
                    print(f"  - {subdir.name}: {file_count} files")
            
            print(f"\n✓ Test data ready at: {self.output_dir}")
            
        except Exception as e:
            print(f"\n✗ Error generating test data: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate realistic test data for Google Photos Manager"
    )
    parser.add_argument(
        'output_dir',
        nargs='?',
        default='./test-data',
        help='Output directory for test data (default: ./test-data)'
    )
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir)
    generator.generate_all()


if __name__ == "__main__":
    main()
