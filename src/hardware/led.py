"""
LED hardware abstraction.
"""
from machine import Pin
from core.logger import get_logger

class LED:
    """Hardware abstraction for ESP32 LED control."""

    def __init__(self, pin: int, inverted: bool = False):
        """
        Initialize LED on specified pin.

        Args:
            pin: GPIO pin number for LED
            inverted: True if LED is active-low (common in ESP32 boards)
        """
        self.logger = get_logger('LED')
        self._pin = Pin(pin, Pin.OUT)
        self._state = False
        self._inverted = inverted

        # Log the configuration
        mode = "active-low (inverted)" if inverted else "active-high (normal)"
        self.logger.info(f"LED initialized on pin {pin} ({mode})")

    def on(self):
        """Turn LED on."""
        # If inverted, we need to set pin LOW to turn LED on
        if self._inverted:
            self._pin.off()
        else:
            self._pin.on()
        self._state = True
        self.logger.debug("LED turned ON")

    def off(self):
        """Turn LED off."""
        # If inverted, we need to set pin HIGH to turn LED off
        if self._inverted:
            self._pin.on()
        else:
            self._pin.off()
        self._state = False
        self.logger.debug("LED turned OFF")

    def toggle(self):
        """Toggle LED state."""
        if self._state:
            self.off()
        else:
            self.on()

    def value(self) -> int:
        """
        Get current LED state.

        Returns:
            1 if on, 0 if off
        """
        return 1 if self._state else 0

    @property
    def is_on(self) -> bool:
        """Check if LED is currently on."""
        return self._state
