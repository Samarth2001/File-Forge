import os
import sys
import time
import logging
import psutil
from watchdog.observers import Observer
from core.FileOrganiser import FileOrganizer
from config.settings import Config

PID_FILE = "file_forge.pid"

def setup_logging():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "file_organizer.log")),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_pid_from_file():
    if not os.path.exists(PID_FILE):
        return None
    with open(PID_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except (ValueError, TypeError):
            return None

def is_running():
    pid = get_pid_from_file()
    if pid is None:
        return False
    try:
        process = psutil.Process(pid)
        return process.is_running() and any("main.py" in cmd.lower() for cmd in process.cmdline())
    except psutil.NoSuchProcess:
        return False

def start_monitoring_service():
    if is_running():
        logging.warning("File Forge is already running.")
        sys.exit(1)

    setup_logging()
    logging.info("File Forge starting...")

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    observers = []
    try:
        config = Config()
        organizer = FileOrganizer(
            source_dirs=config.monitored_dirs,
            dest_dir=config.destination_dir,
            file_types=config.file_types,
            feature_flags=config.feature_flags,
            temp_extensions=config.temp_extensions,
            default_category=config.default_category,
            debounce_delay=config.debounce_delay
        )
        
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
            logging.error("No valid directories to monitor. Exiting.")
            sys.exit(1)

        logging.info("File Forge is now running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutdown signal received.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        for observer in observers:
            observer.stop()
            observer.join()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        logging.info("File Forge stopped successfully.")

def stop_monitoring_service():
    pid = get_pid_from_file()
    if not pid or not is_running():
        logging.warning("File Forge is not running.")
        sys.exit(1)

    try:
        process = psutil.Process(pid)
        process.terminate()
        process.wait(timeout=5)
        logging.info("File Forge stopped successfully.")
    except psutil.NoSuchProcess:
        logging.warning("PID file found, but process is not running.")
    except psutil.TimeoutExpired:
        logging.error("Failed to stop the process gracefully. It might need to be killed manually.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error stopping File Forge: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def get_status():
    pid = get_pid_from_file()
    if pid and is_running():
        print(f"File Forge is running with PID: {pid}")
    else:
        print("File Forge is not running.")

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ["start", "stop", "status"]:
        print("Usage: python main.py [start|stop|status]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        start_monitoring_service()
    elif command == "stop":
        stop_monitoring_service()
    elif command == "status":
        get_status()

if __name__ == "__main__":
    main()
