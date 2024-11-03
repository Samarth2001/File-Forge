import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import logging
from pathlib import Path
import datetime
import sys
import winreg

# Configure logging to write to both console and file
log_file = os.path.join(str(Path.home()), "file_organizer_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)


class FileOrganizer(FileSystemEventHandler):
    def __init__(self, monitored_dirs, destination_base_dir):
        self.monitored_dirs = monitored_dirs
        self.destination_base_dir = destination_base_dir
        self.start_time = datetime.datetime.now()

        # Expanded file types dictionary with more categories and extensions
        self.file_types = {
            "Images": [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".webp",
                ".svg",
                ".tiff",
                ".ico",
                ".raw",
                ".psd",
                ".ai",
            ],
            "Documents": [
                # Microsoft Office
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                # PDFs and texts
                ".pdf",
                ".txt",
                ".rtf",
                ".odt",
                ".ods",
                ".odp",
                # Other documents
                ".csv",
                ".json",
                ".xml",
                ".html",
                ".htm",
            ],
            "Videos": [
                ".mp4",
                ".mkv",
                ".avi",
                ".mov",
                ".wmv",
                ".flv",
                ".webm",
                ".m4v",
                ".mpg",
                ".mpeg",
                ".3gp",
                ".3g2",
                ".gif",
            ],
            "Audio": [
                ".mp3",
                ".wav",
                ".flac",
                ".m4a",
                ".aac",
                ".ogg",
                ".wma",
                ".aiff",
                ".alac",
                ".midi",
                ".mid",
            ],
            "Archives": [
                ".zip",
                ".rar",
                ".7z",
                ".tar",
                ".gz",
                ".bz2",
                ".xz",
                ".iso",
                ".dmg",
            ],
            "Code": [
                ".py",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".js",
                ".css",
                ".php",
                ".html",
                ".sql",
                ".rb",
                ".go",
                ".rs",
                ".swift",
                ".kt",
                ".ipynb",
                ".r",
                ".sh",
                ".bat",
                ".ps1",
            ],
            "Executables": [".exe", ".msi", ".app", ".dmg", ".deb", ".rpm"],
            "Fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
            "eBooks": [".epub", ".mobi", ".azw", ".azw3", ".fb2", ".lit"],
        }

        self._create_directories()
        self.processed_files = set()

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

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        # Skip temporary files and partial downloads
        if event.src_path.endswith(".tmp") or event.src_path.endswith(".crdownload"):
            return

        # Skip if file doesn't exist
        if not os.path.exists(event.src_path):
            return

        try:
            # Ignore files created before script started
            creation_time = os.path.getctime(event.src_path)
            if creation_time < self.start_time.timestamp():
                return

            # Avoid processing same file multiple times
            if event.src_path in self.processed_files:
                return

            # Wait for file to be completely written
            initial_size = -1
            current_size = 0

            while initial_size != current_size:
                initial_size = os.path.getsize(event.src_path)
                time.sleep(1)  # Wait 1 second
                if os.path.exists(event.src_path):  # Check if file still exists
                    current_size = os.path.getsize(event.src_path)
                else:
                    return  # File was deleted, abort processing

            # Additional wait for very large files
            if current_size > 10_000_000:  # 10MB
                time.sleep(2)

            # Get file category
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
                self.processed_files.add(dest_path)  # Store the destination path
                logging.info(f"Moved {filename} to {category} folder")

        except Exception as e:
            logging.error(f"Error processing {event.src_path}: {str(e)}")

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


def main():
    # Get user's home directory
    home_dir = str(Path.home())

    # List of directories to monitor
    monitored_dirs = [
        os.path.join(home_dir, "Downloads"),
        os.path.join(home_dir, "Desktop"),
        "D:\\Downloads",
    ]

    # Set destination directory to D drive
    organized_files_path = r"D:\OrganizedDownloads"

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
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        logging.info("Stopping file organizer...")

    for observer in observers:
        observer.join()


if __name__ == "__main__":
    main()
