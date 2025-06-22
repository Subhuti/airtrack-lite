# utils/logger.py

import logging
import sys

logger = logging.getLogger("AirTrack")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers if reloaded
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

