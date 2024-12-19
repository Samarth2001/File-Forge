import os
import shutil
import logging
import time
import mimetypes
from pathlib import Path

class FileHandler:
    def __init__(self, destination_base_dir):
        self.destination_base_dir = destination_base_dir
        self.start_time = time.time()  # Track when program started
        self.temp_extensions = {'.crdownload', '.tmp', '.part'}
        
    def _is_new_file(self, filepath):
        """Check if file was created after program started"""
        try:
            creation_time = os.path.getctime(filepath)
            return creation_time > self.start_time
        except OSError:
            return False
            
    def _is_download_complete(self, filepath):
        """Check if file is completely downloaded"""
        # Check for temporary extensions
        file_ext = Path(filepath).suffix.lower()
        if file_ext in self.temp_extensions:
            return False
            
        # Check if file is being written to
        try:
            with open(filepath, 'rb') as f:
                # Try to read the file
                f.read(1)
            return True
        except (IOError, PermissionError):
            return False
    
    def _get_actual_extension(self, filepath):
        """Get actual file extension by checking file signature/content"""
        try:
            # First try getting extension from filepath
            file_ext = Path(filepath).suffix.lower()
            
            # Verify with mime type
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type:
                if mime_type.startswith('image/'):
                    detected_ext = '.' + mime_type.split('/')[-1]
                    return detected_ext if detected_ext != '.jpeg' else '.jpg'
                elif mime_type.startswith('video/'):
                    return '.' + mime_type.split('/')[-1]
                elif mime_type.startswith('audio/'):
                    return '.' + mime_type.split('/')[-1]
            return file_ext
        except:
            return Path(filepath).suffix.lower()
            
    def move_file(self, source, destination_category, filename):
        try:
            # Skip if file existed before program start
            if not self._is_new_file(source):
                logging.debug(f"Skipping existing file: {source}")
                return None
                
            # Wait for download to complete
            if not self._is_download_complete(source):
                logging.debug(f"File {source} is still being downloaded")
                return None
                
            # Get actual file extension
            actual_ext = self._get_actual_extension(source)
            if actual_ext != Path(filename).suffix.lower():
                filename = Path(filename).stem + actual_ext
                
            # Create category directory if it doesn't exist
            dest_dir = os.path.join(self.destination_base_dir, destination_category)
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_path = os.path.join(dest_dir, filename)
            
            # Handle duplicates
            if os.path.exists(dest_path):
                base_name = Path(filename).stem
                ext = Path(filename).suffix
                counter = 1
                while os.path.exists(dest_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(dest_dir, new_name)
                    counter += 1
                    
            shutil.move(source, dest_path)
            logging.info(f"Moved {filename} to {destination_category}")
            return dest_path
            
        except Exception as e:
            logging.error(f"Error moving file {source}: {str(e)}")
            return None