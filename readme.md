# File Forge

**File Forge** is a powerful, cross-platform tool that automatically organizes files in specified directories based on their type. Keep your digital space tidy with this efficient and easy-to-use command-line utility.

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
- [Running as a Service](#running-as-a-service)
  - [Linux (systemd)](#linux-systemd)
  - [macOS (launchd)](#macos-launchd)
  - [Windows (Task Scheduler)](#windows-task-scheduler)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Automatic Organization**: Moves files to designated folders based on their extensions.
- **Cross-Platform**: Works on Linux, macOS, and Windows.
- **Command-Line Interface**: Easy-to-use commands to `start`, `stop`, and check the `status` of the service.
- **Customizable**: Configure monitored directories and file categories through a simple JSON file.
- **Efficient**: Uses a PID file to ensure only one instance is running at a time.
- **Logging**: Keeps a detailed log of all operations for easy monitoring and troubleshooting.

## Prerequisites

- **Operating System**: Linux, macOS, or Windows
- **Python Version**: Python 3.7+

**Required Python Packages**

- `watchdog`: For monitoring file system events.
- `psutil`: For process management.

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

---

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/file-forge.git
    cd file-forge
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## Configuration

Customize File Forge to fit your needs by editing the configuration files.

### Monitored Directories

By default, File Forge monitors your `Downloads` and `Desktop` folders. You can change this by editing `config/settings.py`.

### Destination Directory

The default destination for organized files is `D:\OrganizedFiles` on Windows and `~/OrganizedFiles` on other systems. This can also be configured in `config/settings.py`.

### File Types Configuration

File categories are defined in `config/file_types.json`. You can add new file types or change existing ones without modifying the source code.

**Example `file_types.json`**:
```json
{
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt"],
    "Archives": [".zip", ".rar", ".tar.gz"]
}
```

---

## Usage

File Forge is controlled via the command line:

- **Start the service**:
  ```bash
  python main.py start
  ```

- **Stop the service**:
  ```bash
  python main.py stop
  ```

- **Check the status**:
  ```bash
  python main.py status
  ```

---

## Running as a Service

For continuous, automatic file organization, you can set up File Forge to run as a background service on your operating system.

### Linux (systemd)

1.  **Create a Service File**:
    Create a file named `file-forge.service` in `/etc/systemd/system/`:
    ```ini
    [Unit]
    Description=File Forge Service
    After=network.target

    [Service]
    User=your-username
    Group=your-group
    WorkingDirectory=/path/to/file-forge
    ExecStart=/usr/bin/python /path/to/file-forge/main.py start
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    Replace `your-username`, `your-group`, and `/path/to/file-forge` with your actual user, group, and project path.

2.  **Enable and Start the Service**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable file-forge.service
    sudo systemctl start file-forge.service
    ```

### macOS (launchd)

1.  **Create a Launch Agent**:
    Create a file named `com.fileforge.plist` in `~/Library/LaunchAgents/`:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.fileforge</string>
        <key>ProgramArguments</key>
        <array>
            <string>/usr/bin/python</string>
            <string>/path/to/file-forge/main.py</string>
            <string>start</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
    </dict>
    </plist>
    ```
    Replace `/path/to/file-forge` with the actual path to the project.

2.  **Load the Agent**:
    ```bash
    launchctl load ~/Library/LaunchAgents/com.fileforge.plist
    ```

### Windows (Task Scheduler)

1.  **Create a Batch File**:
    Create a file named `start-file-forge.bat` with the following content:
    ```bat
    @echo off
    cd /d "C:\path\to\file-forge"
    python main.py start
    ```
    Replace `C:\path\to\file-forge` with the actual path to the project.

2.  **Schedule a Task**:
    - Open Task Scheduler.
    - Click "Create Basic Task...".
    - Name the task "File Forge" and click "Next".
    - Set the trigger to "When I log on" and click "Next".
    - Choose "Start a program" and click "Next".
    - Browse to and select your `start-file-forge.bat` file.
    - Click "Finish".

---

## Testing

To verify that File Forge is working correctly:
1.  Add files of various types to your monitored directories.
2.  Check the destination folder to confirm they have been moved to the correct subdirectories.
3.  Review the `logs/file_organizer.log` file for any errors.

---

## Troubleshooting

- **Files Not Moving**: Ensure the service is running (`python main.py status`) and check the log file for errors.
- **Permissions**: Verify that you have the necessary permissions to read from the monitored directories and write to the destination directory.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
