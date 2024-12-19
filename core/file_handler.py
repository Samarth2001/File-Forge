import os
import shutil
import logging
from pathlib import Path

class FileHandler:
    def __init__(self, destination_base_dir):
        self.destination_base_dir = destination_base_dir
        
    def move_file(self, source, destination_category, filename):
        try:
            dest_dir = os.path.join(self.destination_base_dir, destination_category)
            dest_path = os.path.join(dest_dir, filename)
            
            # Skip if file already exists at destination
            if os.path.exists(dest_path):
                return None
                
            # Handle duplicates
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{base_name}_{counter}{ext}"
                dest_path = os.path.join(dest_dir, new_name)
                counter += 1
                
            shutil.move(source, dest_path)
            return dest_path
            
        except Exception as e:
            logging.error(f"Error moving file {source}: {str(e)}")
            return None