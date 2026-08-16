"""
Centralized logging utilities for Chakma Historical OCR.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "chakma_ocr",
    level: str = "INFO",
    log_dir: Optional[str] = "logs",
    log_to_file: bool = False,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a structured logger instance.

    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory to save log files if log_to_file is True.
        log_to_file: Whether to write logs to a file in addition to stdout.
        log_format: Custom log format string.
        date_format: Custom date format string.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    default_fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    default_date_fmt = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(
        fmt=log_format or default_fmt,
        datefmt=date_format or default_date_fmt,
    )

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional File Handler
    if log_to_file and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path / f"{name}.log", encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
