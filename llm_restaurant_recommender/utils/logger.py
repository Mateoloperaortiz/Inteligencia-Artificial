"""Centralized logging configuration for the application."""
import logging
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Name of the logger (usually __name__)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / "app.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # File gets all debug info
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger
