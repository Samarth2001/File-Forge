import os
import sys
import pytest
import shutil
import time
import logging
import subprocess

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import is_running, PID_FILE

# Set working directory to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

def cleanup_pid_file():
    """Ensure PID file is removed."""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Fixture to clean up before and after each test."""
    cleanup_pid_file()
    yield
    cleanup_pid_file()

def wait_for_process(command, timeout=10):
    """Wait for the process to start or stop."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if command == "start" and is_running():
            return True
        if command == "stop" and not is_running():
            return True
        time.sleep(0.5)
    return False

class TestCLI:
    def test_start_stop_status(self):
        # 1. Test 'start' command
        main_py_path = os.path.join(PROJECT_ROOT, "main.py")
        process = subprocess.Popen([sys.executable, main_py_path, "start"])
        assert wait_for_process("start"), "Process did not start within timeout."
        
        # 2. Test 'status' command
        result = subprocess.run([sys.executable, main_py_path, "status"], capture_output=True, text=True)
        assert "is running" in result.stdout
        
        # 3. Test 'stop' command
        subprocess.run([sys.executable, main_py_path, "stop"])
        assert wait_for_process("stop"), "Process did not stop within timeout."
        
        # 4. Verify status after stopping
        result = subprocess.run([sys.executable, main_py_path, "status"], capture_output=True, text=True)
        assert "is not running" in result.stdout

    def test_multiple_starts(self):
        # Start the process once
        main_py_path = os.path.join(PROJECT_ROOT, "main.py")
        subprocess.Popen([sys.executable, main_py_path, "start"])
        assert wait_for_process("start")

        # Try to start it again and check the output
        result = subprocess.run([sys.executable, main_py_path, "start"], capture_output=True, text=True)
        assert "already running" in result.stderr.lower()
        
        # Stop the process
        subprocess.run([sys.executable, main_py_path, "stop"])
        wait_for_process("stop")

    def test_stop_without_start(self):
        # Ensure the process is not running
        main_py_path = os.path.join(PROJECT_ROOT, "main.py")
        assert not is_running()
        
        # Try to stop it and check the output
        result = subprocess.run([sys.executable, main_py_path, "stop"], capture_output=True, text=True)
        assert "not running" in result.stderr.lower()

if __name__ == "__main__":
    pytest.main()
