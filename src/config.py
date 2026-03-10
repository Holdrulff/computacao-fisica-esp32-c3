"""
Application configuration file.

Loads configuration from .env file using micropython-dotenv.
This provides secure credential management without hardcoding secrets.

Create a .env file in the src/ directory with:
    WIFI_SSID=your_network
    WIFI_PASSWORD=your_password
    HOSTNAME=dv01
"""

import sys
sys.path.append('/lib')  # Ensure lib directory is in path

from dotenv_micro import load_dotenv, get_env
from core.logger import get_logger, LogLevel

# Load environment variables from .env file
try:
    load_dotenv('.env')
except Exception as e:
    logger = get_logger('Config')
    logger.error(f"Failed to load .env file: {e}")
    

# WiFi Configuration (loaded from .env)
WIFI_SSID = get_env('WIFI_SSID', 'default_network')
WIFI_PASSWORD = get_env('WIFI_PASSWORD', 'default_password')

# Device Configuration (loaded from .env)
HOSTNAME = get_env('HOSTNAME', 'esp32')
