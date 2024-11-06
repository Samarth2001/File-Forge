# Auto File Organizer

The **Auto File Organizer** is a Python script that monitors a specific directory and automatically sorts files into appropriate subdirectories based on their type. This script is useful for keeping your download folder organized by categorizing files as soon as they are downloaded or created.

---

## Features

- **Automatic File Sorting**: Detects file creation or modifications and moves files to designated folders (e.g., Images, Videos, Documents).
- **Customizable Directory**: Supports setting custom source folders for file monitoring.
- **Logging**: Creates a log file that records actions, such as file movements and any errors encountered.
- **Robust Detection**: Uses `watchdog` library to monitor directories in real time.

---

## Prerequisites

Before running this script, ensure you have Python 3.x and the required dependencies installed.

### Required Libraries

Install the required Python libraries by running:

```bash
pip install watchdog
```

## Usage

1. **Clone or Download** the script into your desired directory.

2. **Run the Script**:

   ```bash
   python Auto_Sort.py
   ```

By default, the script monitors the "Downloads" folder. You can modify the source directory as explained in the Configuration section.

3. **View Logs**:

The script generates a log file (file_organizer_log.txt) in your home directory. You can view this log to review file organization activities and troubleshoot issues.
