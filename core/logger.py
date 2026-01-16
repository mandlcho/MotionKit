"""
Logging system for MotionKit
"""

import logging
import os
from datetime import datetime


class Logger:
    """Centralized logging system for MotionKit"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """Initialize the logger"""
        self._logger = logging.getLogger('MotionKit')
        self._logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - MotionKit - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        self._logger.addHandler(console_handler)

    def debug(self, message):
        """Log debug message"""
        self._logger.debug(message)

    def info(self, message):
        """Log info message"""
        self._logger.info(message)

    def warning(self, message):
        """Log warning message"""
        self._logger.warning(message)

    def error(self, message):
        """Log error message"""
        self._logger.error(message)

    def critical(self, message):
        """Log critical message"""
        self._logger.critical(message)


# Singleton instance
logger = Logger()
