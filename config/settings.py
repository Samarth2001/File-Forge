import json
import os
from pathlib import Path
from typing import Dict, List, Any

class Config:
    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.load_config()
        self._setup_directories()
        
    def load_config(self) -> None:
        """Load file type configuration from JSON file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "file_types.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                self.file_types = json.load(f)
                
            # Create case-insensitive mapping of extensions to categories
            self.flattened_types: Dict[str, str] = {}
            for category, extensions in self.file_types.items():
                for ext in extensions:
                    self.flattened_types[ext.lower()] = category
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    def _setup_directories(self) -> None:
        """Setup source and destination directories with fallback options"""
        # Default monitored directories
        self.monitored_dirs: List[str] = [
            os.path.join(str(Path.home()), "Downloads"),
            os.path.join(str(Path.home()), "Desktop")
        ]
        
        # Try to set destination directory with fallbacks
        possible_destinations = [
            "D:\\OrganizedFiles",  # Primary choice
            "C:\\OrganizedFiles",  # Fallback to C drive
            os.path.join(str(Path.home()), "OrganizedFiles")  # User directory fallback
        ]
        
        self.destination_dir = self._find_valid_destination(possible_destinations)
        
        # Ensure destination directory exists
        try:
            os.makedirs(self.destination_dir, exist_ok=True)
        except PermissionError:
            raise PermissionError(f"Cannot create destination directory: {self.destination_dir}")
    
    def _find_valid_destination(self, paths: List[str]) -> str:
        """Find the first valid destination path from the list"""
        for path in paths:
            try:
                # Try to create the directory to test permissions
                os.makedirs(path, exist_ok=True)
                return path
            except (PermissionError, OSError):
                continue
        
        # If all fails, use current directory as last resort
        fallback = os.path.join(os.getcwd(), "OrganizedFiles")
        os.makedirs(fallback, exist_ok=True)
        return fallback
                
    def get_category(self, filepath: str) -> str:
        """Get category for a file based on its extension"""
        try:
            if filepath.lower().endswith(".tar.gz"):
                ext = ".tar.gz"
            else:
                ext = os.path.splitext(filepath)[1].lower()
            return self.flattened_types.get(ext, "Others")
        except Exception:
            return "Others"
    
    def add_monitored_directory(self, directory: str) -> bool:
        """Add a new directory to monitor"""
        if os.path.exists(directory) and directory not in self.monitored_dirs:
            self.monitored_dirs.append(directory)
            return True
        return False
    
    def remove_monitored_directory(self, directory: str) -> bool:
        """Remove a directory from monitoring"""
        if directory in self.monitored_dirs:
            self.monitored_dirs.remove(directory)
            return True
        return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'monitored_directories': self.monitored_dirs,
            'destination_directory': self.destination_dir,
            'file_categories': list(self.file_types.keys()),
            'total_extensions': len(self.flattened_types)
        }