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

# Display I2C Configuration
DISPLAY_I2C_SCL_PIN = 6
DISPLAY_I2C_SDA_PIN = 5
DISPLAY_I2C_ADDR = 0x3C  # I2C address for SSD1306 OLED
DISPLAY_WIDTH = 72    # 0.42" OLED display
DISPLAY_HEIGHT = 40
Y_OFF_SET = 28
X_OFF_SET = 24

# Network
WIFI_CONNECT_TIMEOUT_SEC = 40
WIFI_CONNECT_RETRY_INTERVAL_SEC = 2
WIFI_MAX_RETRIES = 20

# Web server
HTTP_PORT = 5000
HTTP_HOST = '0.0.0.0'

# Display (72x40 - 0.42" OLED)
DISPLAY_CHARS_PER_LINE = 9    # 72px / 8px per char (with spacing)
DISPLAY_LINE_HEIGHT = 10      # Line spacing
DISPLAY_START_Y = 0           # Start from top

# Logging
LOG_LEVEL = 'INFO'  # Can be set to 'ERROR' in production to skip debug/info formatting

# Pre-intern common strings to reduce allocations
HTTP_STATUS_OK = "OK"
HTTP_STATUS_ERROR = "Error"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_HTML = "text/html"
