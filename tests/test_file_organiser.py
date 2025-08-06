import os
import sys
import pytest
import shutil
import time
from pathlib import Path
from watchdog.events import FileSystemEvent

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.FileOrganiser import FileOrganizer

# Set working directory to test directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class TestFileOrganizer:
    @pytest.fixture
    def setup(self):
        self.test_source = Path("test_downloads")
        self.test_dest = Path("test_organized")

        # Clean and create directories
        if self.test_source.exists():
            shutil.rmtree(self.test_source)
        if self.test_dest.exists():
            shutil.rmtree(self.test_dest)
        
        self.test_source.mkdir()
        self.test_dest.mkdir()

        file_types = {
            "Images": [".jpg", ".png"],
            "Documents": [".pdf", ".txt", ".docx"],
            "Archives": [".zip", ".tar.gz"],
        }
        
        feature_flags = {
            "duplicates": True,
            "compression": False,
            "stats": True
        }
        
        temp_extensions = [".tmp", ".crdownload", ".part"]
        default_category = "Others"
        debounce_delay = 0.1

        self.organizer = FileOrganizer(
            source_dirs=[str(self.test_source)],
            dest_dir=str(self.test_dest),
            file_types=file_types,
            feature_flags=feature_flags,
            temp_extensions=temp_extensions,
            default_category=default_category,
            debounce_delay=debounce_delay
        )
        self.organizer.start_time = time.time() - 10 # Process all created files
        
        yield
        
        shutil.rmtree(self.test_source)
        shutil.rmtree(self.test_dest)

    def create_test_file(self, filename: str, content="test"):
        filepath = self.test_source / filename
        filepath.write_text(content)
        return str(filepath)

    def test_file_movement(self, setup):
        # Create a test file
        filepath = self.create_test_file("test.jpg")
        
        # Process the file
        dest_path = self.organizer.process_file(filepath)
        
        # Assert the file was moved correctly
        expected_dest_path = self.test_dest / "Images" / "test.jpg"
        assert expected_dest_path.exists(), f"File was not moved to {expected_dest_path}"
        assert dest_path == str(expected_dest_path), "The destination path returned was incorrect"

    def test_unsupported_file_type(self, setup):
        # Create a file with an unsupported extension
        filepath = self.create_test_file("test.xyz")
        
        # Process the file
        dest_path = self.organizer.process_file(filepath)
        
        # Assert the file was moved to the "Others" directory
        expected_dest_path = self.test_dest / "Others" / "test.xyz"
        assert expected_dest_path.exists(), "File with unsupported type was not moved to Others"
        assert dest_path == str(expected_dest_path), "The destination path returned was incorrect"
        
    def test_debounce_logic(self, setup):
        filepath = self.create_test_file("debounce_test.txt")
        
        # Simulate rapid events
        event1 = FileSystemEvent(filepath)
        event1.event_type = 'created'
        event2 = FileSystemEvent(filepath)
        event2.event_type = 'modified'
        
        self.organizer.on_any_event(event1)
        time.sleep(0.05)
        self.organizer.on_any_event(event2)
        
        # Wait for the debounce delay to pass
        time.sleep(self.organizer.debounce_delay + 0.1)
        
        # Assert the file was moved only once
        expected_dest_path = self.test_dest / "Documents" / "debounce_test.txt"
        assert expected_dest_path.exists(), "Debounced file was not moved"
        assert not (self.test_source / "debounce_test.txt").exists(), "Original file still exists after debouncing"

if __name__ == "__main__":
    pytest.main()
