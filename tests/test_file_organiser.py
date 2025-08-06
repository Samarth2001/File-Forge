import os
import sys
import pytest
import shutil
import time
from pathlib import Path

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

        self.organizer = FileOrganizer(
            source_dirs=[str(self.test_source)],
            dest_dir=str(self.test_dest),
            file_types=file_types
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
        
if __name__ == "__main__":
    pytest.main()
