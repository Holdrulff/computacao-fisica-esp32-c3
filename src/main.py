"""
Main application entry point.

This file is executed after boot.py and contains the main application logic.
The 2-second delay allows IDEs like Thonny to interrupt execution.

Development tip:
- Press RESET button on ESP32
- Immediately press STOP in Thonny
- This should give you a REPL prompt (>>>)
"""
import time
import sys

# Ensure root directory is in path (MicroPython compatibility)
if '' not in sys.path:
    sys.path.insert(0, '')
if '/' not in sys.path:
    sys.path.insert(0, '/')

# Allow time for IDE to interrupt (Thonny race condition workaround)
time.sleep(2)

# Start the application
from core.app import Application
import config

if __name__ == '__main__':
    # Create and start application with config
    app = Application(
        wifi_ssid=config.WIFI_SSID,
        wifi_password=config.WIFI_PASSWORD,
        hostname=config.HOSTNAME
    )

    # Run the application (this blocks until shutdown)
    app.start()
