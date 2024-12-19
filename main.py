import os
import sys
import logging
import time
import winreg
from watchdog.observers import Observer
from core.FileOrganiser import FileOrganizer
from config.settings import Config

def add_to_startup(file_path):
    try:
        script_dir = os.path.dirname(os.path.abspath(file_path))
        batch_path = os.path.join(script_dir, "start_file_organizer.bat")
        
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write(f'start /MIN pythonw "{file_path}"')
            
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "FileOrganizer", 0, winreg.REG_SZ, batch_path)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error(f"Failed to add to startup: {str(e)}")
        return False

def remove_from_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "FileOrganizer")
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error(f"Failed to remove from startup: {str(e)}")
        return False

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--add-startup":
            add_to_startup(__file__)
            return
        elif sys.argv[1] == "--remove-startup":
            remove_from_startup()
            return
    
    config = Config()
    organizer = FileOrganizer(config)
    
    observers = []
    for directory in config.monitored_dirs:
        if os.path.exists(directory):
            observer = Observer()
            observer.schedule(organizer, directory, recursive=False)
            observer.start()
            observers.append(observer)
            logging.info(f"Started monitoring: {directory}")
    
    try:
        while True:
            organizer.process_pending_files()
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        logging.info("Stopping file organizer...")

    for observer in observers:
        observer.join()

if __name__ == "__main__":
    main()