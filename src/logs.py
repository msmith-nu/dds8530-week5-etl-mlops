"""Logs module performance."""
import logging
from src import config

def get_logger(name):
    """Create a logging that writes into our log folder."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(config.LOG_FILE), logging.StreamHandler()],
    )

    return logging.getLogger(name)


