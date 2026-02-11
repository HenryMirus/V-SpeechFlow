"""
Centralized Logging Configuration for V-SpeechFlow

Sets up rotating file logging and console output for all GUI modules.
All log messages are in English for consistency.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Module-level flag to prevent duplicate setup
_logging_initialized = False
_log_file_path = None


def setup_logging(log_level: int = logging.INFO) -> Path:
    """
    Initialize the logging system with rotating file handler and console output.

    Args:
        log_level: Initial log level (default: logging.INFO)

    Returns:
        Path to the current log file
    """
    global _logging_initialized, _log_file_path

    if _logging_initialized:
        return _log_file_path

    log_dir = Path.home() / "V-SpeechFlow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"gui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    _log_file_path = log_file

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers (prevent duplicates on restart)
    root_logger.handlers.clear()

    # File handler with rotation (5 MB per file, 10 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=10,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)  # File always captures everything
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler (respects the configured log level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    _logging_initialized = True

    # Startup banner
    logger = logging.getLogger('vspeechflow')
    logger.info("=" * 60)
    logger.info("V-SpeechFlow logging initialized")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("=" * 60)

    return log_file


def set_log_level(level: int):
    """
    Dynamically change the log level for the console handler.
    The file handler always captures DEBUG and above.

    Args:
        level: New log level (e.g. logging.DEBUG, logging.INFO)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
            handler.setLevel(level)

    logger = logging.getLogger('vspeechflow')
    logger.info(f"Log level changed to: {logging.getLevelName(level)}")


def get_log_level() -> int:
    """Returns the current effective log level."""
    return logging.getLogger().level


def get_log_file_path() -> Path:
    """Returns the path to the current log file."""
    return _log_file_path
