"""
Lightweight logging utility for MicroPython.
"""
import time

class LogLevel:
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class Logger:
    """Simple logger for MicroPython with timestamp and log levels."""

    # Map string level names to integers
    LEVEL_MAP = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}

    def __init__(self, name: str, level: int = LogLevel.INFO):
        self.name = name
        # Support string-based level from constants
        if isinstance(level, str):
            level = self.LEVEL_MAP.get(level, LogLevel.INFO)
        self.level = level
        self._level_names = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.WARNING: "WARN",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRIT"
        }

    def _log(self, level: int, message: str):
        """Internal logging method - OPTIMIZED to skip formatting if not logged."""
        # Early return before any string formatting
        if level < self.level:
            return

        level_name = self._level_names.get(level, "UNKNOWN")
        timestamp = time.time()
        print(f"[{timestamp:.3f}] {level_name:5s} [{self.name}] {message}")

    def debug(self, message: str):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """Log info message."""
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        """Log warning message."""
        self._log(LogLevel.WARNING, message)

    def error(self, message: str):
        """Log error message."""
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message)

def get_logger(name: str, level = None) -> Logger:
    """
    Factory function to create logger instances.

    Args:
        name: Logger name
        level: Log level (int or string from constants.LOG_LEVEL), defaults to INFO
    """
    if level is None:
        # Try to import LOG_LEVEL from constants, fallback to INFO
        try:
            import constants
            level = constants.LOG_LEVEL
        except (ImportError, AttributeError):
            level = LogLevel.INFO

    return Logger(name, level)
