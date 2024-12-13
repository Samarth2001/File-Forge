# test_auto_sort.py
import os
import pytest
import shutil
import time
import logging
import datetime
import json
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from Auto_Arrange import FileOrganizer

# Set working directory to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def wait_for_file(filepath, timeout=5):
    """Helper function to wait for file existence with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(filepath):
            return True
        time.sleep(0.1)
    return False

class TestFileOrganizer:
    @pytest.fixture
    def setup(self):
        # Create test directories with cleanup handling
        self.test_source = "test_downloads"
        self.test_dest = "test_organized"
        
        # Clean up any leftover test directories first
        for path in [self.test_source, self.test_dest]:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    logging.warning(f"Cleanup of {path} failed: {e}")
        
        # Create fresh test directories
        os.makedirs(self.test_source, exist_ok=True)
        os.makedirs(self.test_dest, exist_ok=True)

        # Set start_time to a date far in the past
        start_time = datetime.datetime(2000, 1, 1)

        file_types = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
            "Documents": [".pdf", ".txt", ".doc", ".docx"],
            "Videos": [".mp4", ".mkv", ".avi"],
            "Audio": [".mp3", ".wav", ".flac"],
            "Archives": [".zip", ".rar", ".7z", ".tar.gz"],
            "Code": [".py", ".java", ".cpp"],
            "Executables": [".exe", ".msi"],
            "Fonts": [".ttf", ".otf"],
            "eBooks": [".epub", ".mobi"],
            "Others": []
        }

        self.organizer = FileOrganizer(
            [self.test_source],
            self.test_dest,
            start_time=start_time,
            file_types=file_types
        )
        self.organizer.batch_interval = 0

        yield

        # Safe cleanup with retry
        for path in [self.test_source, self.test_dest]:
            retry_count = 3
            while retry_count > 0:
                try:
                    if os.path.exists(path):
                        shutil.rmtree(path)
                    break
                except Exception as e:
                    logging.warning(f"Cleanup attempt {4-retry_count} failed: {e}")
                    time.sleep(0.5)
                    retry_count -= 1

    def create_test_file(self, filename, content="test"):
        """Create a test file with retry mechanism"""
        filepath = os.path.join(self.test_source, filename)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(filepath, "w") as f:
                    f.write(content)
                # Wait for file to be fully written
                if wait_for_file(filepath):
                    return filepath
            except Exception as e:
                if attempt == max_retries - 1:
                    pytest.fail(f"Failed to create test file after {max_retries} attempts: {e}")
                time.sleep(0.5)
        return filepath

    def test_basic_file_types(self, setup):
        test_files = {
            "test.jpg": "Images",
            "doc.pdf": "Documents",
            "video.mp4": "Videos",
            "song.mp3": "Audio",
            "archive.zip": "Archives",
            "script.py": "Code",
            "program.exe": "Executables",
            "font.ttf": "Fonts",
            "book.epub": "eBooks",
            "random.xyz": "Others"
        }

        for filename, expected_category in test_files.items():
            filepath = self.create_test_file(filename)
            event = type("Event", (), {"src_path": filepath, "is_directory": False})
            
            self.organizer.on_created(event)
            self.organizer.process_pending_files()

            expected_path = os.path.join(self.test_dest, expected_category, filename)
            
            # Wait for file movement with timeout
            assert wait_for_file(expected_path), f"File not moved to {expected_path}"

    def test_edge_cases(self, setup):
        # 1. File with no extension (keep this part as is)
        filepath = self.create_test_file("no_extension")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        self.organizer.process_pending_files()

        assert wait_for_file(os.path.join(self.test_dest, "Others", "no_extension")), "No extension file not moved"

        # 2. File with multiple extensions - Fixed version
        filepath = self.create_test_file("script.tar.gz")
        
        # Verify source file was created
        assert wait_for_file(filepath), "Source file not created"
        
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        self.organizer.process_pending_files()

        # Use wait_for_file instead of direct assert
        dest_path = os.path.join(self.test_dest, "Archives", "script.tar.gz")
        assert wait_for_file(dest_path), "File with multiple extensions not moved correctly"

 
    def test_duplicate_handling(self, setup):
        # Create duplicate files with the same name but different content
        filepath1 = self.create_test_file("test.txt", "original")
        event1 = type("Event", (), {"src_path": filepath1, "is_directory": False})
        self.organizer.on_created(event1)
        time.sleep(0.5)

        # Create a second file with the same name
        filepath2 = self.create_test_file("test.txt", "duplicate")
        event2 = type("Event", (), {"src_path": filepath2, "is_directory": False})
        self.organizer.on_created(event2)
        time.sleep(0.5)

        # Check that both files exist with different names
        assert os.path.exists(os.path.join(self.test_dest, "Documents", "test.txt"))
        assert os.path.exists(os.path.join(self.test_dest, "Documents", "test_1.txt"))

    def test_special_cases(self, setup):
        # Test temporary files
        filepath = self.create_test_file("download.tmp")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(filepath)  # Should not be moved as it's a temp file

        # Test very small files
        filepath = self.create_test_file("small.txt", "a")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Documents", "small.txt"))

        # Test file with special characters
        filepath = self.create_test_file("test@#$%.pdf")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Documents", "test@#$%.pdf"))
