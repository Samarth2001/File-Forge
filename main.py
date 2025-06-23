import os
import sys
import logging
import time
import winreg
from typing import List, Optional
from watchdog.observers import Observer
from core.FileOrganiser import FileOrganizer
from config.settings import Config

def setup_logging() -> None:
    """Setup comprehensive logging configuration"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "file_organizer.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

def remove_all_startup_entries() -> bool:
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
        
        removed_count = 0
        for entry in entries_to_remove:
            try:
                winreg.DeleteValue(key, entry)
                logging.info(f"Removed startup entry: {entry}")
                removed_count += 1
            except WindowsError:
                pass
                
        winreg.CloseKey(key)
        logging.info(f"Startup cleanup completed. Removed {removed_count} entries.")
        return True
    except Exception as e:
        logging.error(f"Error cleaning startup entries: {str(e)}")
        return False

def kill_existing_instances() -> None:
    """Kill any existing Python processes running the script"""
    try:
        # Try to kill pythonw.exe first
        os.system('taskkill /F /IM pythonw.exe 2>nul')
        # Then try python.exe
        os.system('taskkill /F /IM python.exe 2>nul')
        time.sleep(1)
        logging.info("Cleaned up existing instances")
    except Exception as e:
        logging.warning(f"Process cleanup warning (this is normal if not running): {e}")

def add_to_startup(file_path: str) -> bool:
    """Add the script to Windows startup"""
    try:
        abs_path = os.path.abspath(file_path)
        script_dir = os.path.dirname(abs_path)
        batch_path = os.path.join(script_dir, "start_file_organizer.bat")

        # Create batch file for background execution
        with open(batch_path, "w", encoding='utf-8') as f:
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

def remove_from_startup() -> bool:
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

def start_monitoring(config: Config) -> List[Observer]:
    """Start file monitoring for all configured directories"""
    organizer = FileOrganizer(
        source_dirs=config.monitored_dirs,
        dest_dir=config.destination_dir,
        file_types=config.file_types
    )
    
    observers = []
    for directory in config.monitored_dirs:
        if os.path.exists(directory):
            observer = Observer()
            observer.schedule(organizer, directory, recursive=False)
            observer.start()
            observers.append(observer)
            logging.info(f"Started monitoring: {directory}")
        else:
            logging.warning(f"Directory does not exist, skipping: {directory}")
    
    if not observers:
        logging.error("No valid directories to monitor!")
        return []
    
    return observers

def main():
    """Main application entry point"""
    setup_logging()
    
    logging.info("File Forge starting...")
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--add-startup":
            success = add_to_startup(__file__)
            if success:
                logging.info("Successfully added to startup")
            else:
                logging.error("Failed to add to startup")
            return
        elif sys.argv[1] == "--remove-startup":
            success = remove_all_startup_entries()
            if success:
                logging.info("Successfully removed from startup")
            else:
                logging.error("Failed to remove from startup")
            return
    
    # Initialize configuration
    try:
        config = Config()
        logging.info(f"Configuration loaded successfully")
        config_summary = config.get_config_summary()
        logging.info(f"Monitoring {len(config_summary['monitored_directories'])} directories")
        logging.info(f"Destination: {config_summary['destination_directory']}")
        logging.info(f"File categories: {len(config_summary['file_categories'])}")
    except Exception as e:
        logging.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Start monitoring
    observers = start_monitoring(config)
    if not observers:
        logging.error("Failed to start any file monitors. Exiting.")
        sys.exit(1)

    try:
        logging.info("File Forge is now running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received...")
        for observer in observers:
            observer.stop()
        logging.info("Stopping File Forge...")

    # Wait for all observers to finish
    for observer in observers:
        observer.join()
    
    logging.info("File Forge stopped successfully.")

if __name__ == "__main__":
    main()