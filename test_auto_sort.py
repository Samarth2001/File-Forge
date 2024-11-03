# test_auto_sort.py
import os
import pytest
import shutil
import time
import logging
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from Auto_Sort import FileOrganizer


class TestFileOrganizer:
    @pytest.fixture
    def setup(self):
        # Create test directories
        self.test_source = "test_downloads"
        self.test_dest = "test_organized"
        os.makedirs(self.test_source, exist_ok=True)
        os.makedirs(self.test_dest, exist_ok=True)

        # Initialize organizer with proper timestamp
        self.organizer = FileOrganizer([self.test_source], self.test_dest)
        
        # Ensure the directories are created
        self.organizer._create_directories()

        yield

        # Cleanup after tests
        if os.path.exists(self.test_source):
            shutil.rmtree(self.test_source)
        if os.path.exists(self.test_dest):
            shutil.rmtree(self.test_dest)

    def create_test_file(self, filename, content="test"):
        filepath = os.path.join(self.test_source, filename)
        with open(filepath, "w") as f:
            f.write(content)
        time.sleep(0.1)  # Give a small delay for file creation
        return filepath

    def test_basic_file_types(self, setup):
        # Test one file from each category
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
            "random.xyz": "Others",
        }

        for filename, expected_category in test_files.items():
            filepath = self.create_test_file(filename)
            event = type("Event", (), {"src_path": filepath, "is_directory": False})
            self.organizer.on_created(event)
            time.sleep(0.5)  # Give time for file to be processed
            
            expected_path = os.path.join(self.test_dest, expected_category, filename)
            assert os.path.exists(expected_path), f"File not found at {expected_path}"

    def test_edge_cases(self, setup):
        # 1. File with no extension
        filepath = self.create_test_file("no_extension")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Others", "no_extension"))

        # 2. File with multiple extensions
        filepath = self.create_test_file("script.tar.gz")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Archives", "script.tar.gz"))

        # 3. File with uppercase extension
        filepath = self.create_test_file("image.JPG")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Images", "image.JPG"))

        # 4. File with spaces
        filepath = self.create_test_file("my document.pdf")
        event = type("Event", (), {"src_path": filepath, "is_directory": False})
        self.organizer.on_created(event)
        time.sleep(0.5)
        assert os.path.exists(os.path.join(self.test_dest, "Documents", "my document.pdf"))

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