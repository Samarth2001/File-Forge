import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from watchdog.events import FileSystemEventHandler
from core.file_handler import FileHandler
from features.duplicates import DuplicateHandler
from threading import Timer

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, source_dirs: List[str], dest_dir: str, file_types: Dict[str, List[str]], 
                 feature_flags: Dict[str, bool], temp_extensions: List[str], default_category: str,
                 debounce_delay: float):
        self.source_dirs = source_dirs
        self.dest_dir = dest_dir
        self.file_types = file_types
        self.feature_flags = feature_flags
        self.temp_extensions = temp_extensions
        self.default_category = default_category
        self.debounce_delay = debounce_delay
        
        self.file_handler = FileHandler(self.dest_dir)
        self.duplicate_handler = DuplicateHandler() if self.feature_flags.get("duplicates") else None
        
        self.start_time = time.time()
        self._extension_map = self._create_extension_map()
        self._create_directories()
        self._event_timers: Dict[str, Timer] = {}

    def _create_extension_map(self) -> Dict[str, str]:
        return {ext: cat for cat, exts in self.file_types.items() for ext in exts}

    def on_any_event(self, event):
        if event.is_directory or event.event_type not in ('created', 'modified'):
            return

        if event.src_path in self._event_timers:
            self._event_timers[event.src_path].cancel()

        self._event_timers[event.src_path] = Timer(
            self.debounce_delay, self._process_event, args=[event.src_path]
        )
        self._event_timers[event.src_path].start()

    def _process_event(self, file_path: str):
        if file_path in self._event_timers:
            del self._event_timers[file_path]
        self.process_file(file_path)

    def process_file(self, file_path: str) -> Optional[str]:
        try:
            if not os.path.exists(file_path) or not self._is_new_file(file_path) or self._is_temp_file(file_path):
                return None

            if self.duplicate_handler and self.duplicate_handler.is_duplicate(file_path):
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
        return path.lower().endswith(tuple(self.temp_extensions))

    def _is_new_file(self, filepath: str) -> bool:
        try:
            return os.path.getctime(filepath) > self.start_time
        except OSError:
            return False

    def _get_category(self, filepath: str) -> str:
        suffixes = "".join(Path(filepath).suffixes).lower()
        return self._extension_map.get(suffixes, self.default_category) if suffixes else self.default_category

    def _create_directories(self) -> None:
        try:
            for category in set(self.file_types.keys()) | {self.default_category}:
                Path(self.dest_dir).joinpath(category).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logging.error(f"Error creating directories: {e}")
            raise
