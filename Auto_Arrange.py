import os
import time
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import logging
from pathlib import Path
import datetime
import sys
import winreg
import json

# Configure logging to write to both console and file
log_file = os.path.join(str(Path.home()), "file_organizer_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)


class FileOrganizer(FileSystemEventHandler):
    def __init__(self, monitored_dirs, destination_base_dir, start_time=None):
        self.monitored_dirs = monitored_dirs
        self.destination_base_dir = destination_base_dir
        self.start_time = start_time if start_time else datetime.datetime.now()
        self.file_types = self._load_file_types()
        self._create_directories()
        self.processed_files = set()
        self.pending_files = []
        self.last_batch_time = time.time()
        self.batch_interval = 5  # Process files every 5 seconds
        self.max_pending = 50  # Max files to queue

    def process_pending_files(self):
        """Process queued files in batches"""
        current_time = time.time()
        if (
            not self.pending_files
            or (current_time - self.last_batch_time) < self.batch_interval
        ):
            return

        files_to_process = self.pending_files[: self.max_pending]
        self.pending_files = self.pending_files[self.max_pending :]

        for event in files_to_process:
            self._process_file(event)

        self.last_batch_time = current_time

        # Memory optimization
        if len(self.processed_files) > 1000:
            self.processed_files.clear()

    def on_created(self, event):
        """Queue files instead of processing immediately"""
        if event.is_directory or self._is_temp_file(event.src_path):
            return

        logging.info(f"File created: {event.src_path}")
        self.pending_files.append(event)
        self.process_pending_files()

    def _is_temp_file(self, path):
        """Quick check for temporary files"""
        return path.endswith((".tmp", ".crdownload"))

    def _process_file(self, event):
        """Optimized file processing"""
        try:
            if not os.path.exists(event.src_path):
                logging.warning(f"File does not exist: {event.src_path}")
                return

            # Use stat once instead of multiple exists/getctime calls
            stat = os.stat(event.src_path)
            if stat.st_ctime < self.start_time.timestamp():
                logging.info(f"File created before start time: {event.src_path}")
                return

            # Quick size check without loops
            time.sleep(0.1)  # Minimal delay
            if os.path.exists(event.src_path):
                new_stat = os.stat(event.src_path)
                if new_stat.st_size != stat.st_size:
                    logging.info(f"File size changed: {event.src_path}")
                    return

            # Determine file category
            file_extension = os.path.splitext(event.src_path)[1].lower()
            category = "Others"
            for folder, extensions in self.file_types.items():
                if file_extension in extensions:
                    category = folder
                    break

            # Create destination path
            dest_dir = os.path.join(self.destination_base_dir, category)
            filename = os.path.basename(event.src_path)
            dest_path = os.path.join(dest_dir, filename)

            # Handle duplicate filenames with counter
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{base_name}_{counter}{ext}"
                dest_path = os.path.join(dest_dir, new_name)
                counter += 1

            # Ensure source file still exists and move it
            if os.path.exists(event.src_path):
                shutil.move(event.src_path, dest_path)
                self.processed_files.add(dest_path)
                logging.info(f"Moved {filename} to {category} folder")

        except Exception as e:
            logging.error(f"Error processing {event.src_path}: {str(e)}")

    def _load_file_types(self):
        """Load file types configuration from JSON"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "file_types.json")
            with open(config_path, "r") as f:
                config = json.load(f)

            # Flatten nested dictionaries (for Documents category)
            file_types = {}
            for category, extensions in config.items():
                if isinstance(extensions, dict):
                    # Flatten nested categories
                    all_extensions = []
                    for subcategory in extensions.values():
                        all_extensions.extend(subcategory)
                    file_types[category] = all_extensions
                else:
                    file_types[category] = extensions

            return file_types

        except Exception as e:
            logging.error(f"Error loading file types: {str(e)}")
            # Return default empty dict if config fails to load
            return {}

    def _create_directories(self):
        """Create organized folders if they don't exist"""
        for folder in self.file_types.keys():
            folder_path = os.path.join(self.destination_base_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                logging.info(f"Created directory: {folder_path}")

        others_path = os.path.join(self.destination_base_dir, "Others")
        if not os.path.exists(others_path):
            os.makedirs(others_path)
            logging.info(f"Created directory: {others_path}")

    def on_modified(self, event):
        """Handle file modification events"""
        self.on_created(event)  # Use same logic as creation


def add_to_startup(file_path):
    """Add the script to Windows startup"""
    try:
        # Create batch file in the script's directory
        script_dir = os.path.dirname(os.path.abspath(file_path))
        batch_path = os.path.join(script_dir, "start_file_organizer.bat")

        # Write the batch file with pythonw.exe (runs without console window)
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write(f'start /MIN pythonw "{file_path}"')

        # Add to registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )

        winreg.SetValueEx(key, "FileOrganizer", 0, winreg.REG_SZ, batch_path)

        winreg.CloseKey(key)
        logging.info("Successfully added to startup!")
        return True
    except Exception as e:
        logging.error(f"Failed to add to startup: {str(e)}")
        return False


def remove_from_startup():
    """Remove the script from Windows startup"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )

        winreg.DeleteValue(key, "FileOrganizer")
        winreg.CloseKey(key)
        logging.info("Successfully removed from startup!")
        return True
    except Exception as e:
        logging.error(f"Failed to remove from startup: {str(e)}")
        return False


# Modify main loop for efficiency
def main():
    # Get user's home directory
    home_dir = str(Path.home())

    # List of directories to monitor
    monitored_dirs = [
        os.path.join(str(Path.home()), "Downloads"),
        os.path.join(str(Path.home()), "Desktop"),
        "D:\\Downloads",  # Adjust if needed
    ]

    # Set destination directory to D drive
    organized_files_path = "D:\\OrganizedDownloads"  # Adjust if needed

    # Handle command line arguments for startup configuration
    if len(sys.argv) > 1:
        if sys.argv[1] == "--add-startup":
            add_to_startup(__file__)
            return
        elif sys.argv[1] == "--remove-startup":
            remove_from_startup()
            return

    # Create base directory in D drive if it doesn't exist
    if not os.path.exists(organized_files_path):
        os.makedirs(organized_files_path)
        logging.info(f"Created base directory in D drive: {organized_files_path}")

    # Initialize observers for each monitored directory
    observers = []
    event_handler = FileOrganizer(monitored_dirs, organized_files_path)

    for directory in monitored_dirs:
        if os.path.exists(directory):
            observer = Observer()
            observer.schedule(event_handler, directory, recursive=False)
            observer.start()
            observers.append(observer)
            logging.info(f"Started monitoring: {directory}")

    logging.info(f"Files will be organized in: {organized_files_path}")
    logging.info("Ready to organize new downloads. Existing files will be ignored.")

    try:
        while True:
            event_handler.process_pending_files()
            time.sleep(1)  # Reduced CPU usage

            # Optional: System resource check
            if psutil.cpu_percent() > 80 or psutil.virtual_memory().percent > 80:
                time.sleep(5)  # Back off if system is under load

    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        logging.info("Stopping file organizer...")

    for observer in observers:
        observer.join()


if __name__ == "__main__":
    main()
