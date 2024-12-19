# File Forge

The **File Forge** is a Python script that monitors a specific directory and automatically Arranges files into appropriate subdirectories based on their type. This script is useful for keeping your download folder organized by categorizing files as soon as they are downloaded or created.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Monitored Directories](#monitored-directories)
  - [Destination Directory](#destination-directory)
  - [File Types Configuration](#file-types-configuration)
- [Usage](#usage)
  - [Running the Script](#running-the-script)
  - [Adding to Startup](#adding-to-startup)
  - [Removing from Startup](#removing-from-startup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Automatic Arranging**: Moves files to designated folders based on their extensions.
- **Customizable Monitoring**: Specify which directories to monitor.
- **Configurable Categories**: Easily update file type categories via a JSON file.
- **Runs on Startup**: Optionally configure the script to run automatically when your system starts.
- **Logging**: Generates a log file to track actions and errors.
- **Batch Processing**: Processes files efficiently to reduce system load.


## Prerequisites

- **Operating System**: Windows
- **Python Version**: Python 3.x

**Required Python Packages**

- `watchdog`
- `psutil` (if implementing performance enhancements)

Install the required packages using:

```bash
pip install watchdog psutil
```
---

## Installation

1. **Clone or Download the Repository:**
   ```bash
   git clone https://github.com/yourusername/File-Forge.git
   ```

2. **Navigate to the Directory:**
   ```bash
   cd file-forge
   ```

## Configuration

Before running the script, you may want to adjust the configuration to suit your needs.

### Monitored Directories

By default, the script monitors the following directories:

- `C:\Users\<YourUsername>\Downloads`
- `C:\Users\<YourUsername>\Desktop`
- `D:\Downloads`

To change the directories, edit the `monitored_dirs` list in `Auto_Arrange.py`:

```python
monitored_dirs = [
    r"C:\Users\<YourUsername>\Downloads",
    r"C:\Users\<YourUsername>\Desktop",
    r"D:\Downloads"
]
```
### Destination Directory

The default destination directory is D:\OrganizedDownloads. To change it, modify the organized_files_path variable in Auto_Arrange.py:
```python
organized_files_path = "D:\\OrganizedDownloads"  # Adjust as needed
```
Make sure the destination drive and path exist or can be created by the script.

### File Types Configuration

File type categories and their associated extensions are defined in `file_types.json`. This allows easy updates without modifying the script.

Example `file_types.json`:

```json
{
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "Documents": {
        "Office": [".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
        "Text": [".pdf", ".txt", ".rtf"],
        "Data": [".csv", ".json", ".xml"]
    },
    "Videos": [".mp4", ".mkv", ".avi"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Archives": [".zip", ".rar", ".7z"],
    "Code": [".py", ".java", ".cpp"],
    "Executables": [".exe", ".msi"],
    "Others": []
}
```

## Notes

- **Nested Categories**: The script flattens nested categories. For example, under "Documents", subcategories like "Office", "Text", and "Data" are merged into a single "Documents" folder.
- **Adding Extensions**: To add a new extension to an existing category, simply add it to the appropriate category in `file_types.json`.
- **Adding Categories**: To create a new category, add a new key to the JSON file with a list of associated extensions.

---

## Usage

### Running the Script

To run the script manually:

```bash
python Auto_Arrange.py
```
The script will start monitoring the specified directories and organizing files accordingly.

### Adding to Startup

To run the script automatically when you log in to Windows:

1. **Add to Startup**:
   - Create a batch file that runs the Python script.
   - Add a registry entry to run the batch file at startup.

2. **Verify**:
   - The script creates a log file at `%USERPROFILE%\file_organizer_log.txt`.
   - Check this log file to ensure the script is running without errors.

### Removing from Startup

To remove the script from the startup sequence:

```python
python Auto_Arrange.py --remove-startup
```
---

## Testing

To ensure the script works correctly:

1. **Place Test Files**: Add files of various types to the monitored directories.
2. **Observe**: Wait a few seconds for the script to process the files.
3. **Verify**: Check the destination directories to see if files have been moved appropriately.
4. **Check Logs**: Review the log file (`%USERPROFILE%\file_organizer_log.txt`) for any errors or warnings.

---

## Troubleshooting

### Files Not Being Moved
- Ensure the script is running.
- Check that the monitored directories and destination directory exist.
- Verify that you have the necessary permissions to access and modify files in the specified directories.

### Script Not Starting on Boot
- Run the script with `--add-startup` as an administrator.
- Check the startup folder or registry entries to ensure the script is set to run on boot.

### High CPU or Memory Usage
- The script includes optimizations to reduce system load. Make sure you have the latest version.
- Reduce the number of monitored directories if performance issues persist.

### Files with Unknown Extensions
- Update `file_types.json` to include the new extensions.
- Files with extensions not listed in `file_types.json` will be moved to the "Others" folder by default.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## Acknowledgments

- **Watchdog**: Used for monitoring file system events.
- **Python.org**: The Python programming language.

## Disclaimer

This script is provided "as is" without any warranty. Use at your own risk. Always back up important data before running scripts that modify file systems.

 
