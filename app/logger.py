"""
Shared logger for the whole application.

Writes to logs/eth_terminal.log (with manual rotation) and to stdout.
Usage:

    from app.logger import get_logger
    log = get_logger(__name__)
    log.info("something happened")
"""

import logging
from app.config import LOG_FILE, LOG_LEVEL


def _setup_root_logger():
    """Configure the root logger. Runs only once when the module is imported."""
    root = logging.getLogger()

    # If already configured (e.g. by another library), don't add duplicate handlers
    if root.handlers:
        return

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    root.setLevel(level)

    # Format
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler: file (UTF-8 encoding so non-ASCII characters are preserved)
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(fmt)
        file_handler.setLevel(level)
        root.addHandler(file_handler)
    except Exception:
        # If the file cannot be written (permissions, full disk, etc.),
        # continue with stdout only
        pass

    # Handler: console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(level)
    root.addHandler(console_handler)


_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a logger named after the module that requests it."""
    return logging.getLogger(name)
