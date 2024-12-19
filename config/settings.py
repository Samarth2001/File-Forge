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
            
        # Flatten nested categories
        self.flattened_types = {}
        for category, extensions in self.file_types.items():
            if isinstance(extensions, dict):
                for subcategory in extensions.values():
                    self.flattened_types.update({ext: category for ext in subcategory})
            else:
                self.flattened_types.update({ext: category for ext in extensions})
    
    def _setup_directories(self):
        self.monitored_dirs = [
            os.path.join(str(Path.home()), "Downloads"),
            os.path.join(str(Path.home()), "Desktop"),
            "D:\\Downloads"
        ]
        self.destination_dir = "D:\\OrganizedDownloads"
                
    def get_category(self, filepath):
        if filepath.endswith(".tar.gz"):
            ext = ".tar.gz"
        else:
            ext = os.path.splitext(filepath)[1].lower()
        return self.flattened_types.get(ext, "Others")