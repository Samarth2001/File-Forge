import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        self.load_config()
        self._setup_directories()
        
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "file_types.json")
        with open(config_path) as f:
            self.file_types = json.load(f)
            
        # Create case-insensitive mapping of extensions to categories
        self.flattened_types = {}
        for category, extensions in self.file_types.items():
            for ext in extensions:
                self.flattened_types[ext.lower()] = category
    
    def _setup_directories(self):
        self.monitored_dirs = [
            os.path.join(str(Path.home()), "Downloads"),
            os.path.join(str(Path.home()), "Desktop")
        ]
        self.destination_dir = "D:\\OrganizedFiles"  # Changed to D drive
                
    def get_category(self, filepath):
        if filepath.endswith(".tar.gz"):
            ext = ".tar.gz"
        else:
            ext = os.path.splitext(filepath)[1].lower()
        return self.flattened_types.get(ext, "Others")