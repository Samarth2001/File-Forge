import os
import sys
import logging
import time
import winreg
from watchdog.observers import Observer
from core.FileOrganiser import FileOrganizer
from config.settings import Config

def remove_all_startup_entries():
    """Remove all related startup entries"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_ALL_ACCESS
        )
        
        # List of possible registry names we might have used
        entries_to_remove = ["FileForge", "FileOrganizer", "AutoFileOrganizer"]
        
        for entry in entries_to_remove:
            try:
                winreg.DeleteValue(key, entry)
                logging.info(f"Removed startup entry: {entry}")
            except WindowsError:
                pass
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error(f"Error cleaning startup entries: {str(e)}")
        return False

def kill_existing_instances():
    """Kill any existing Python processes running the script"""
    try:
        # Try to kill pythonw.exe first
        os.system('taskkill /F /IM pythonw.exe 2>nul')
        # Then try python.exe
        os.system('taskkill /F /IM python.exe 2>nul')
        time.sleep(1)
    except Exception as e:
        logging.warning(f"Process not found (this is normal if not running): {e}")

def add_to_startup(file_path):
    """Add the script to Windows startup"""
    try:
        abs_path = os.path.abspath(file_path)
        script_dir = os.path.dirname(abs_path)
        batch_path = os.path.join(script_dir, "start_file_organizer.bat")

        # Create batch file for background execution
        with open(batch_path, "w") as f:
            f.write("@echo off\n")
            f.write(f'cd /d "{script_dir}"\n')
            python_path = os.path.join(sys.prefix, "pythonw.exe")
            f.write(f'start /B /MIN "" "{python_path}" "{abs_path}"\n')

        # Add to registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "FileForge", 0, winreg.REG_SZ, batch_path)
        winreg.CloseKey(key)

        # Start the program now
        os.system(f'start /B /MIN "" "{python_path}" "{abs_path}"')
        
        logging.info(f"Added to startup and launched in background")
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
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "FileForge")
        winreg.CloseKey(key)
        logging.info("Successfully removed from startup!")
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
    
    # Handle command line arguments but continue execution
    if len(sys.argv) > 1:
        if sys.argv[1] == "--add-startup":
            add_to_startup(__file__)
        elif sys.argv[1] == "--remove-startup":
            remove_all_startup_entries()
            return
    
    # Continue with normal execution
    config = Config()
    organizer = FileOrganizer(
        source_dirs=config.monitored_dirs,
        dest_dir=config.destination_dir,
        file_types=config.file_types
    )
    
    # Start monitoring
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
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        logging.info("Stopping File Forge...")

    for observer in observers:
        observer.join()

if __name__ == "__main__":
    main()