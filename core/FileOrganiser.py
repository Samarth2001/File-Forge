import os
import shutil
import time
import logging
from watchdog.events import FileSystemEventHandler
import datetime
from core.file_handler import FileHandler
from features.stats import StatsManager
from features.duplicates import DuplicateHandler
from features.compression import CompressionHandler

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, source_dirs, dest_dir, file_types=None):
        self.source_dirs = source_dirs
        self.dest_dir = dest_dir
        self.destination_base_dir = dest_dir  # Add this to fix attribute error
        self.file_types = file_types or {}
        
        # Initialize configuration
        self.config = {
            'enable_compression': False,
            'enable_stats': True,
            'enable_duplicates': True,
            'get_category': self._get_category  # Add method for category determination
        }
        
        # Initialize handlers
        self.file_handler = FileHandler(self.dest_dir)
        self.stats_manager = StatsManager()
        self.duplicate_handler = DuplicateHandler()
        self.compression_handler = CompressionHandler()
        
        # Initialize processing variables
        self.processed_files = set()
        self.pending_files = []
        self.last_batch_time = time.time()
        self.batch_interval = 5
        self.max_pending = 50
        self.start_time = time.time()
        
        self._create_directories()

    def process_pending_files(self):
        # Process any files that might be waiting
        time.sleep(0.1)  # Small delay to ensure file operations complete
        current_time = time.time()
        if not self.pending_files or (current_time - self.last_batch_time) < self.batch_interval:
            return

        files_to_process = self.pending_files[:self.max_pending]
        self.pending_files = self.pending_files[self.max_pending:]

        for event in files_to_process:
            self._process_file(event)

        self.last_batch_time = current_time

        if len(self.processed_files) > 1000:
            self.processed_files.clear()

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def process_file(self, file_path):
        """Process a single file"""
        try:
            if not os.path.exists(file_path):
                return

            if self._is_temp_file(file_path):
                return

            category = self._get_category(file_path)
            filename = os.path.basename(file_path)
            dest_dir = os.path.join(self.dest_dir, category)
            
            # Ensure category directory exists
            os.makedirs(dest_dir, exist_ok=True)
            
            # Handle duplicates
            dest_path = os.path.join(dest_dir, filename)
            if os.path.exists(dest_path):
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(dest_dir, new_name)
                    counter += 1

            # Move the file
            shutil.move(file_path, dest_path)
            logging.info(f"Moved {filename} to {category}")
            return dest_path

        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return None

    def _is_temp_file(self, path):
        return path.endswith((".tmp", ".crdownload"))

    def _is_new_file(self, filepath):
        """Check if file was created after the program started"""
        try:
            creation_time = os.path.getctime(filepath)
            return creation_time > self.start_time
        except OSError:
            return False

    def _process_file(self, event):
        try:
            if not os.path.exists(event.src_path):
                logging.warning(f"File does not exist: {event.src_path}")
                return

            # Skip if file existed before program start
            if not self._is_new_file(event.src_path):
                logging.debug(f"Skipping existing file: {event.src_path}")
                return

            # Check for duplicates
            if self.duplicate_handler.is_duplicate(event.src_path):
                logging.info(f"Duplicate file detected: {event.src_path}")
                return

            filename = os.path.basename(event.src_path)
            category = self.config.get_category(event.src_path)
            
            dest_path = self.file_handler.move_file(
                event.src_path,
                category,
                filename
            )

            if dest_path:
                self.processed_files.add(dest_path)
                self.stats_manager.update_stats({
                    'size': os.path.getsize(dest_path),
                    'category': category
                })
                logging.info(f"Moved {filename} to {category} folder")

        except Exception as e:
            logging.error(f"Error processing {event.src_path}: {str(e)}")

    def _get_category(self, filepath):
        """Determine file category based on extension"""
        # Handle special case for .tar.gz
        if filepath.endswith('.tar.gz'):
            return next((cat for cat, exts in self.file_types.items() 
                        if '.tar.gz' in exts), "Others")
        
        file_ext = os.path.splitext(filepath)[1].lower()
        return next((cat for cat, exts in self.file_types.items() 
                    if file_ext in exts), "Others")

    def _create_directories(self):
        """Create category directories if they don't exist"""
        for category in self.file_types.keys():
            folder_path = os.path.join(self.dest_dir, category)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                logging.info(f"Created directory: {folder_path}")

        # Create Others directory
        others_path = os.path.join(self.dest_dir, "Others")
        if not os.path.exists(others_path):
            os.makedirs(others_path)
            logging.info(f"Created directory: {others_path}")

    def on_modified(self, event):
        self.on_created(event)