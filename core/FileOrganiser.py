import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.events import FileSystemEventHandler
from core.file_handler import FileHandler
from features.duplicates import DuplicateHandler

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, source_dirs: List[str], dest_dir: str, file_types: Optional[Dict[str, List[str]]] = None):
        self.source_dirs = source_dirs
        self.dest_dir = dest_dir
        self.file_types = file_types or {}
        
        self.file_handler = FileHandler(self.dest_dir)
        self.duplicate_handler = DuplicateHandler()
        
        self.start_time = time.time()
        
        self._create_directories()

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def process_file(self, file_path: str) -> Optional[str]:
        try:
            if not os.path.exists(file_path) or not self._is_new_file(file_path) or self._is_temp_file(file_path):
                return None

            if self.duplicate_handler.is_duplicate(file_path):
                logging.info(f"Duplicate file detected and ignored: {file_path}")
                try:
                    os.remove(file_path)
                except OSError as e:
                    logging.warning(f"Could not remove duplicate file: {e}")
                return None

            category = self._get_category(file_path)
            filename = os.path.basename(file_path)
            
            dest_path = self.file_handler.move_file(file_path, category, filename)
            
            if dest_path:
                logging.info(f"Moved {filename} to {category}/{filename}")
                return dest_path

        except FileNotFoundError:
            logging.warning(f"File not found for processing: {file_path}")
        except PermissionError:
            logging.error(f"Permission denied while processing: {file_path}")
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
        
        return None

    def _is_temp_file(self, path: str) -> bool:
        return path.lower().endswith((".tmp", ".crdownload", ".part"))

    def _is_new_file(self, filepath: str) -> bool:
        try:
            return os.path.getctime(filepath) > self.start_time
        except OSError:
            return False

    def _get_category(self, filepath: str) -> str:
        suffixes = "".join(Path(filepath).suffixes).lower()
        if not suffixes:
            return "Others"
        
        for category, extensions in self.file_types.items():
            if any(suffixes.endswith(ext) for ext in extensions):
                return category
        return "Others"

    def _create_directories(self) -> None:
        try:
            for category in set(self.file_types.keys()) | {"Others"}:
                Path(self.dest_dir).joinpath(category).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating directories: {e}")
            raise
