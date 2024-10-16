import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import yaml
import argparse


# create a class that will handle the download
class DownloadHandler(FileSystemEventHandler):

    def __init__(
        self,
        source_directory,
        destination_directory,
        move_unknown_files,
        unknown_files_directory=None,
        auto_create_dir=False,
    ):  # initialize the class
        self.source_directory = source_directory
        self.destination_directory = destination_directory
        self.move_unknown_files = move_unknown_files
        self.unknown_files_directory = unknown_files_directory
        self.auto_create_dir = auto_create_dir

    # create a new directory
    def on_creation(self, event):
        if event.is_directory:  # check if the event is a directory
            return

        file_path = event.src_path  # get the file path
        self.process_file(file_path)

        # process the file and move it to the destination directory

    def process_files(self, file_path):

        file_name = os.path.basename(file_path)  # get the file name
        _, extension = os.path.splitText(file_name)  # get the file extension
        extension = extension.lower()  # convert to lowercase

        moved = False
        for folder, extensions in self.destination_directory.items():
            if extension in extensions:
                destination = os.path.join(folder, file_name)
                self.move_file(file_path, destination)
                moved = True
                break

        if not moved:
            if self.auto_create_dir:

                new_folder = os.path.join(
                    self.destination_directory, extension.lsrip(".")
                )  # create a new folder
                os.makedirs(new_folder, exist_ok=True)
                self.destination_directory[new_folder] = [extension]
                destination = os.path.join(new_folder, file_name)
                self.move_file(file_path, destination)
                logging.info(
                    f"Created new folder for {extension} and moved {file_name} to {new_folder}"
                )
            elif self.move_unknown_files and self.unknown_files_directory:
                destination = os.path.join(self.unknown_files_directory, file_name)
                self.move_file(file_path, destination)
                logging.info(
                    f"Moved unknown file {file_name} to {self.unknown_files_directory}"
                )

    def move_file(self, source, destination):

        max_retries = 10
        attempts = 0
        while attempts < max_retries:
            try:
                shutil.move(source, destination)
                logging.info(f"Moved {source} to {destination}")
                break
            except PermissionError:
                attempts += 1
                time.sleep(1)
            except FileNotFoundError:
                logging.error(f"File {source} not found")
                break
        else:
            logging.error(f"Failed to move {source} to {destination}")


def load_config(config_path):
    with open(config_path, "r") as config_file:
        return yaml.safe_load(config_file)


def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
