import os
import shutil
import time
import logging
from typing import List, Dict, Set, Optional, Any
from watchdog.events import FileSystemEventHandler
import datetime
from core.file_handler import FileHandler
from features.stats import StatsManager
from features.duplicates import DuplicateHandler
from features.compression import CompressionHandler

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, source_dirs: List[str], dest_dir: str, file_types: Optional[Dict[str, List[str]]] = None):
        self.source_dirs = source_dirs
        self.dest_dir = dest_dir
        self.destination_base_dir = dest_dir
        self.file_types = file_types or {}
        
        # Initialize configuration
        self.config = {
            'enable_compression': False,
            'enable_stats': True,
            'enable_duplicates': True,
        }
        
        # Initialize handlers
        self.file_handler = FileHandler(self.dest_dir)
        self.stats_manager = StatsManager()
        self.duplicate_handler = DuplicateHandler()
        self.compression_handler = CompressionHandler()
        
        # Initialize processing variables
        self.processed_files: Set[str] = set()
        self.pending_files: List[Any] = []
        self.last_batch_time = time.time()
        self.batch_interval = 5
        self.max_pending = 50
        self.start_time = time.time()
        
        self._create_directories()

    def process_pending_files(self) -> None:
        """Process any files that might be waiting"""
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

    def on_created(self, event) -> None:
        """Handle file creation event"""
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_modified(self, event) -> None:
        """Handle file modification event"""
        if not event.is_directory:
            self.process_file(event.src_path)

    def process_file(self, file_path: str) -> Optional[str]:
        """Process a single file using the unified approach"""
        try:
            if not os.path.exists(file_path):
                return None

            # Skip if file existed before program start
            if not self._is_new_file(file_path):
                return None

            # Skip temporary files
            if self._is_temp_file(file_path):
                return None

            # Check for duplicates if enabled
            if self.config['enable_duplicates'] and self.duplicate_handler.is_duplicate(file_path):
                logging.info(f"Duplicate file detected: {file_path}")
                return None

            # Get category and filename
            category = self._get_category(file_path)
            filename = os.path.basename(file_path)
            
            # Use file_handler for consistent file movement
            dest_path = self.file_handler.move_file(file_path, category, filename)
            
            if dest_path:
                self.processed_files.add(dest_path)
                
                # Update stats if enabled
                if self.config['enable_stats']:
                    self.stats_manager.update_stats({
                        'size': os.path.getsize(dest_path),
                        'category': category
                    })
                
                logging.info(f"Moved {filename} to {category}")
                return dest_path

        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            return None

    def _is_temp_file(self, path: str) -> bool:
        """Check if file is a temporary file"""
        temp_extensions = (".tmp", ".crdownload", ".part")
        return path.lower().endswith(temp_extensions)

    def _is_new_file(self, filepath: str) -> bool:
        """Check if file was created after the program started"""
        try:
            creation_time = os.path.getctime(filepath)
            return creation_time > self.start_time
        except OSError:
            return False

    def _process_file(self, event) -> None:
        """Legacy method for batch processing - delegates to process_file"""
        self.process_file(event.src_path)

    def _get_category(self, filepath: str) -> str:
        """Determine file category based on extension"""
        try:
            # Handle special case for .tar.gz
            if filepath.lower().endswith('.tar.gz'):
                return next((cat for cat, exts in self.file_types.items() 
                          if '.tar.gz' in [ext.lower() for ext in exts]), "Others")
            
            # Get file extension and ensure it's lowercase
            file_ext = os.path.splitext(filepath)[1].lower()
            
            # Check all extensions in file_types
            for category, extensions in self.file_types.items():
                # Convert all extensions to lowercase for comparison
                if file_ext in [ext.lower() for ext in extensions]:
                    logging.debug(f"File {filepath} categorized as {category}")
                    return category
                    
            logging.debug(f"File {filepath} with extension {file_ext} categorized as Others")
            return "Others"
        except Exception as e:
            logging.error(f"Error categorizing {filepath}: {str(e)}")
            return "Others"

    def _create_directories(self) -> None:
        """Create main category directories"""
        try:
            # Create main category directories from file_types plus Others
            categories = set(self.file_types.keys())
            categories.add("Others")
            
            for category in categories:
                folder_path = os.path.join(self.dest_dir, category)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    logging.info(f"Created directory: {folder_path}")
        except Exception as e:
            logging.error(f"Error creating directories: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.stats_manager.get_stats() if self.config['enable_stats'] else {}