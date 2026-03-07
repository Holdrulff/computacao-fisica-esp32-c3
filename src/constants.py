"""
Application constants and configuration values.
"""

# Performance / Debug
DEBUG = False  # Enable development features (IDE interrupt delay, verbose logging)
ENABLE_AIOREPL = False  # Enable async REPL (can be disabled for faster boot)
ENABLE_WEBREPL = False  # Enable WebREPL (conflicts with HTTP server event loop)

# Hardware pins
LED_PIN = 8
LED_INVERTED = True  # True for active-low LEDs (common in ESP32 boards)
DISPLAY_I2C_SCL_PIN = 6
DISPLAY_I2C_SDA_PIN = 5
DISPLAY_I2C_ADDR = 0x3C
DISPLAY_WIDTH = 128   # Landscape mode (standard)
DISPLAY_HEIGHT = 64

# Network
WIFI_CONNECT_TIMEOUT_SEC = 40
WIFI_CONNECT_RETRY_INTERVAL_SEC = 2
WIFI_MAX_RETRIES = 20

# Web server
HTTP_PORT = 5000
HTTP_HOST = '0.0.0.0'

# Display (landscape mode: 128x64)
DISPLAY_CHARS_PER_LINE = 21   # ~128px / 6px per char
DISPLAY_LINE_HEIGHT = 10      # Extra spacing between lines
DISPLAY_START_Y = 0           # Start from top
