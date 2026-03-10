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
            # Log I2C configuration
            self.logger.info(f"Initializing display with SCL={scl_pin}, SDA={sda_pin}, addr={hex(i2c_addr)}")

            # Initialize I2C
            i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))

            # Scan for devices
            devices = i2c.scan()
            if devices:
                self.logger.info(f"I2C scan found {len(devices)} device(s) at addresses: {[hex(d) for d in devices]}")
            else:
                self.logger.error(f"I2C scan found no devices - check wiring to pins SCL={scl_pin}, SDA={sda_pin}")
                return

            if i2c_addr not in devices:
                self.logger.error(f"Display not detected at address {hex(i2c_addr)} - check wiring to pins SCL={scl_pin}, SDA={sda_pin}")
                self.logger.info(f"Available devices: {[hex(d) for d in devices]}")
                return

            # Initialize display driver
            self.logger.info(f"Display detected at {hex(i2c_addr)}, initializing driver...")
            
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
            self.logger.error(f"Check display wiring to pins SCL={scl_pin}, SDA={sda_pin}")

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

    def get_framebuffer_as_bmp(self):
        """
        Export current framebuffer as BMP image.

        Returns:
            bytes: BMP file data (monochrome bitmap) or None if unavailable

        SSD1306 framebuffer layout:
        - 72 width x 40 height = 2,880 pixels
        - 1 bit per pixel (monochrome)
        - Stored in vertical pages (8 pixels per byte)
        - 72 bytes per page x 5 pages = 360 bytes total

        BMP format (monochrome):
        - 62 byte header (14 BMP + 40 DIB + 8 palette)
        - Pixel data (padded to 4-byte alignment)
        """
        if not self._available or not self._driver:
            return None

        try:
            import struct

            # BMP dimensions
            width = constants.DISPLAY_WIDTH   # 72
            height = constants.DISPLAY_HEIGHT # 40

            # Calculate row size (must be multiple of 4 bytes)
            # Monochrome: 1 bit per pixel, so 72 pixels = 9 bytes
            # Padded to 12 bytes (next multiple of 4)
            bits_per_pixel = 1
            bytes_per_row = (width * bits_per_pixel + 7) // 8  # 9 bytes
            row_padding = (4 - (bytes_per_row % 4)) % 4        # 3 bytes padding
            padded_row_size = bytes_per_row + row_padding      # 12 bytes

            pixel_data_size = padded_row_size * height          # 480 bytes
            palette_size = 8  # 2 colors x 4 bytes each
            header_size = 54
            file_size = header_size + palette_size + pixel_data_size

            # Build BMP header (14 bytes)
            bmp_header = struct.pack('<2sIHHI',
                b'BM',              # Signature
                file_size,          # File size
                0,                  # Reserved
                0,                  # Reserved
                header_size + palette_size  # Pixel data offset (62)
            )

            # Build DIB header (40 bytes - BITMAPINFOHEADER)
            dib_header = struct.pack('<IiiHHIIiiII',
                40,                 # DIB header size
                width,              # Width
                height,             # Height (positive = bottom-up)
                1,                  # Planes
                bits_per_pixel,     # Bits per pixel
                0,                  # Compression (BI_RGB)
                pixel_data_size,    # Image size
                2835,               # X pixels per meter (72 DPI)
                2835,               # Y pixels per meter
                2,                  # Colors in palette
                2                   # Important colors
            )

            # Build color palette (2 colors: black=0, white=1)
            # BMP uses BGRA format (4 bytes per color)
            palette = struct.pack('<BBBBBBBB',
                0, 0, 0, 0,        # Black (B, G, R, A)
                255, 255, 255, 0   # White (B, G, R, A)
            )

            # Get framebuffer from SSD1306 driver
            # The framebuffer is stored as a bytearray in vertical strips
            framebuffer = self._driver.buffer

            # Convert framebuffer to BMP pixel data
            # SSD1306: vertical strips (8 pixels per byte, column-major)
            # BMP: horizontal rows (bottom-up, row-major)
            pixel_data = bytearray()

            # Iterate rows from bottom to top (BMP is bottom-up)
            for y in range(height - 1, -1, -1):
                row_bits = bytearray()

                # Build one row of pixels
                for x in range(width):
                    # Calculate position in framebuffer
                    # SSD1306 layout: page = y // 8, bit = y % 8
                    page = y // 8
                    bit_position = y % 8
                    fb_index = x + (page * width)

                    # Extract pixel value (1 = white, 0 = black)
                    if fb_index < len(framebuffer):
                        pixel = (framebuffer[fb_index] >> bit_position) & 1
                    else:
                        pixel = 0

                    # Pack into BMP format (LSB first within each byte)
                    byte_index = x // 8
                    bit_index = 7 - (x % 8)  # BMP is MSB first

                    if x % 8 == 0:
                        row_bits.append(0)

                    if pixel:
                        row_bits[byte_index] |= (1 << bit_index)

                # Add row to pixel data
                pixel_data.extend(row_bits)

                # Add padding to reach 4-byte alignment
                pixel_data.extend(b'\x00' * row_padding)

            # Combine all parts
            bmp_data = bmp_header + dib_header + palette + pixel_data

            return bytes(bmp_data)

        except Exception as e:
            self.logger.error(f"Failed to export framebuffer: {e}")
            return None

    def get_framebuffer_as_base64(self):
        """
        Export framebuffer as base64-encoded BMP data URI.

        Returns:
            str: Data URI (data:image/bmp;base64,...) or None if unavailable
        """
        if not self._available:
            return None

        try:
            bmp_data = self.get_framebuffer_as_bmp()
            if not bmp_data:
                return None

            # Use ubinascii for base64 encoding (MicroPython standard)
            import ubinascii
            b64_data = ubinascii.b2a_base64(bmp_data).decode('ascii').strip()

            return f"data:image/bmp;base64,{b64_data}"

        except Exception as e:
            self.logger.error(f"Failed to encode framebuffer: {e}")
            return None
