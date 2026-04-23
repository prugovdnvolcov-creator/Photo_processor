"""
Logging setup for the Photo Agent.

Configures structured logging with both file and console handlers.
"""

import logging
import sys
from typing import Optional

from photo_agent.src.core.config import Config


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Creates a logger with both file and console handlers,
    using a standardized format with timestamps.
    
    Args:
        log_file: Optional custom log file path. Uses Config.LOG_FILE if not provided.
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("PhotoAgent")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    log_path = log_file or Config.PATHS.LOG_FILE
    try:
        fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except (IOError, OSError) as e:
        print(f"Warning: Could not create log file {log_path}: {e}")
    
    # Console handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    logger.info("=== PHOTO AGENT STARTED ===")
    
    return logger
