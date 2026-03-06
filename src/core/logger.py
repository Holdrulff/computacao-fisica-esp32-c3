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

    def __init__(self, name: str, level: int = LogLevel.INFO):
        self.name = name
        self.level = level
        self._level_names = {
            LogLevel.DEBUG: "DEBUG",
            LogLevel.INFO: "INFO",
            LogLevel.WARNING: "WARN",
            LogLevel.ERROR: "ERROR",
            LogLevel.CRITICAL: "CRIT"
        }

    def _log(self, level: int, message: str):
        """Internal logging method."""
        if level >= self.level:
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

def get_logger(name: str, level: int = LogLevel.INFO) -> Logger:
    """Factory function to create logger instances."""
    return Logger(name, level)
