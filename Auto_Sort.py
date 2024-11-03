import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import logging
from pathlib import Path
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


class FileOrganizer(FileSystemEventHandler):
    def __init__(self, monitored_dirs, destination_base_dir):
        self.monitored_dirs = monitored_dirs
        self.destination_base_dir = destination_base_dir
        # Store the script start time
        self.start_time = datetime.datetime.now()

        self.file_types = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".pptx"],
            "Videos": [".mp4", ".mkv", ".avi", ".mov"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
        }

        # Create destination directories if they don't exist
        self._create_directories()

        # Keep track of processed files to avoid duplicates
        self.processed_files = set()

    def _create_directories(self):
        """Create organized folders if they don't exist"""
        for folder in self.file_types.keys():
            folder_path = os.path.join(self.destination_base_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                logging.info(f"Created directory: {folder_path}")

        # Create Others folder
        others_path = os.path.join(self.destination_base_dir, "Others")
        if not os.path.exists(others_path):
            os.makedirs(others_path)

    def _get_destination_folder(self, file_extension):
        """Determine the appropriate folder based on file extension"""
        for folder, extensions in self.file_types.items():
            if file_extension.lower() in extensions:
                return folder
        return "Others"

    def on_created(self, event):
        self._process_file(event)

    def _process_file(self, event):
        if event.is_directory:
            return

        file_path = event.src_path

        # Skip if file has already been processed
        if file_path in self.processed_files:
            return

        # Skip temporary files
        if file_path.endswith(".crdownload") or file_path.endswith(".tmp"):
            return

        try:
            # Wait briefly to ensure the file is completely downloaded
            time.sleep(1)

            # Skip if file no longer exists (already moved)
            if not os.path.exists(file_path):
                return

            # Check if file was created after script started
            file_creation_time = datetime.datetime.fromtimestamp(
                os.path.getctime(file_path)
            )

            if file_creation_time < self.start_time:
                return  # Skip files that existed before script started

            # Get file extension and determine destination folder
            file_extension = os.path.splitext(file_path)[1]
            folder_name = self._get_destination_folder(file_extension)

            destination_dir = os.path.join(self.destination_base_dir, folder_name)

            # Get filename and create destination path
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(destination_dir, file_name)

            # Handle duplicate files
            if os.path.exists(destination_path):
                base_name, extension = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(destination_path):
                    new_name = f"{base_name}_{counter}{extension}"
                    destination_path = os.path.join(destination_dir, new_name)
                    counter += 1

            # Move the file to the destination folder and add to processed_files set  
            shutil.move(file_path, destination_path)
            self.processed_files.add(destination_path)
            logging.info(f"Moved {file_name} to {folder_name} folder")

        except Exception as e:
            logging.error(f"Error processing {event.src_path}: {str(e)}")


def main():
    # Get user's home directory to monitor common download locations 
    home_dir = str(Path.home())

    # List of directories to monitor (add your common download locations here)
    monitored_dirs = [
        os.path.join(home_dir, "Downloads"),
        os.path.join(home_dir, "Desktop"),
        "D:\\Downloads",  # Add more paths as needed
    ]

    # Set destination directory to D drive
    organized_files_path = r"D:\OrganizedDownloads"

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
