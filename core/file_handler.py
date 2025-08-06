import os
import shutil
import logging
from pathlib import Path

class FileHandler:
    def __init__(self, destination_base_dir: str):
        self.destination_base_dir = Path(destination_base_dir)

    def move_file(self, source_path: str, category: str, filename: str) -> str:
        try:
            dest_dir = self.destination_base_dir / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = dest_dir / filename
            
            # Handle potential duplicates by renaming the file
            if dest_path.exists():
                counter = 1
                base, ext = dest_path.stem, dest_path.suffix
                while dest_path.exists():
                    dest_path = dest_dir / f"{base}_{counter}{ext}"
                    counter += 1
            
            shutil.move(source_path, dest_path)
            return str(dest_path)
            
        except (OSError, shutil.Error) as e:
            logging.error(f"Error moving file {source_path}: {e}")
            raise
