"""
OLED Display hardware abstraction.
"""
from machine import Pin, I2C
from core.logger import get_logger
import constants

class Display:
    """Hardware abstraction for SSD1306 OLED display."""

    def __init__(self, scl_pin: int, sda_pin: int, i2c_addr: int = 0x3C):
        """
        Initialize OLED display.

        Args:
            scl_pin: I2C SCL pin number
            sda_pin: I2C SDA pin number
            i2c_addr: I2C address of display (default 0x3C)
        """
        self.logger = get_logger('Display')
        self._available = False
        self._driver = None

        try:
            # Initialize I2C
            i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))

            # Scan for devices
            devices = i2c.scan()
            self.logger.info(f"I2C devices found: {[hex(d) for d in devices]}")

            if i2c_addr not in devices:
                self.logger.warning(f"Display not found at address {hex(i2c_addr)}")
                return

            # Initialize display driver
            import ssd1306
            self._driver = ssd1306.SSD1306_I2C(
                constants.DISPLAY_WIDTH,
                constants.DISPLAY_HEIGHT,
                i2c
            )
            self._available = True
            self.logger.info("Display initialized successfully")
            self.clear()

        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")

    @property
    def is_available(self) -> bool:
        """Check if display is available and working."""
        return self._available

    def clear(self):
        """Clear display."""
        if not self._available:
            return
        try:
            self._driver.fill(0)
            self._driver.show()
        except Exception as e:
            self.logger.error(f"Failed to clear display: {e}")

    def show_text(self, text: str, x: int = 0, y: int = 0):
        """
        Show text at specified position.

        Args:
            text: Text to display
            x: X coordinate (default 0)
            y: Y coordinate (default 0)
        """
        if not self._available:
            self.logger.debug(f"Display unavailable, would show: {text}")
            return

        try:
            self._driver.text(text, x, y, 1)
            self._driver.show()
        except Exception as e:
            self.logger.error(f"Failed to show text: {e}")

    def _wrap_text(self, text):
        """
        Wrap text into chunks - OPTIMIZED with generator (O(1) memory).

        Yields chunks of text that fit within DISPLAY_CHARS_PER_LINE.
        """
        lines = text.split('\n')
        chars_per_line = constants.DISPLAY_CHARS_PER_LINE

        for line in lines:
            line_len = len(line)
            if line_len <= chars_per_line:
                yield line
            else:
                # Yield chunks without creating intermediate list
                for i in range(0, line_len, chars_per_line):
                    yield line[i:i + chars_per_line]

    def show_message(self, message: str):
        """
        Display multi-line message with automatic text wrapping.

        Args:
            message: Message to display (supports \\n for line breaks)
        """
        if not self._available:
            self.logger.debug(f"Display unavailable, would show message: {message}")
            return

        try:
            self.clear()
            line_num = 0
            max_lines = constants.DISPLAY_HEIGHT // constants.DISPLAY_LINE_HEIGHT

            # Use generator for memory-efficient text wrapping
            for chunk in self._wrap_text(message):
                if line_num >= max_lines:
                    break

                y_pos = constants.DISPLAY_START_Y + (line_num * constants.DISPLAY_LINE_HEIGHT)

                # Center text horizontally
                text_width = len(chunk) * 6  # Approximate char width
                x_pos = max(0, (constants.DISPLAY_WIDTH - text_width) // 2)

                self._driver.text(chunk, x_pos, y_pos, 1)
                line_num += 1

            self._driver.show()
            self.logger.debug(f"Displayed message: {message}")

        except Exception as e:
            self.logger.error(f"Failed to display message: {e}")

    def show_status(self, hostname: str, ip: str, port: int = 5000):
        """
        Display device status (hostname and IP).

        Args:
            hostname: Device hostname
            ip: IP address
            port: HTTP port number
        """
        status_msg = f"{hostname}:{port} {ip}"
        self.show_message(status_msg)
