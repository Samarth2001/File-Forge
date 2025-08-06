import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Any

# Get the absolute path to the project's root directory
ROOT_DIR = Path(__file__).parent.parent

class Config:
    def __init__(self, config_file: str = "file_types.json"):
        self.config_file = ROOT_DIR / "config" / config_file
        try:
            self.file_types = self._load_file_types()
            self.monitored_dirs = self._setup_monitored_dirs()
            self.destination_dir = self._setup_destination_dir()
            self.feature_flags = self._load_feature_flags()
            self.temp_extensions = self._load_temp_extensions()
            self.default_category = self._load_default_category()
        except (ValueError, OSError) as e:
            logging.error(f"Configuration error: {e}")
            raise

    def _load_file_types(self) -> Dict[str, List[str]]:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load or parse config file '{self.config_file}': {e}")

    def _setup_monitored_dirs(self) -> List[str]:
        home = Path.home()
        return [str(home / "Downloads"), str(home / "Desktop")]

    def _setup_destination_dir(self) -> str:
        home = Path.home()
        # Define possible destination directories, from most to least preferred
        possible_destinations = [
            Path("D:/OrganizedFiles"),
            Path("C:/OrganizedFiles"),
            home / "OrganizedFiles",
            Path.cwd() / "OrganizedFiles"
        ]
        
        for dest in possible_destinations:
            try:
                dest.mkdir(parents=True, exist_ok=True)
                return str(dest)
            except (PermissionError, OSError):
                continue
        
        # This will only be reached if all attempts to create a directory fail
        raise OSError("Could not create any destination directory. Please check permissions.")

    def _load_feature_flags(self) -> Dict[str, bool]:
        # Configuration for features like compression, stats, and duplicates
        return {
            "duplicates": True,
            "compression": False,
            "stats": True
        }

    def _load_temp_extensions(self) -> List[str]:
        return [".tmp", ".crdownload", ".part"]

    def _load_default_category(self) -> str:
        return "Others"

    def get_config_summary(self) -> Dict[str, Any]:
        return {
            'monitored_directories': self.monitored_dirs,
            'destination_directory': self.destination_dir,
            'file_categories': list(self.file_types.keys()),
            'total_extensions': sum(len(exts) for exts in self.file_types.values()),
            'features': self.feature_flags
        }
