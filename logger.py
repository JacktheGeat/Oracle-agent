# -*- coding: utf-8 -*-
#logger.py
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import os
# Load .env file if it exists
load_dotenv()

# ------------------------------------------------------------------
# 1. Resolve log file path
# ------------------------------------------------------------------
# Option A: Environment variable (highest priority)

LOG_FILE_NAME = "logger"
log_path_env = os.getenv("LOG_FILE_LOCATION")

if log_path_env:
    LOG_FILE = Path(log_path_env).expanduser().resolve() / f"{LOG_FILE_NAME}.log"
else:
    # Option B: Default = "logs" folder next to this logger.py file
    LOG_FILE = Path(__file__).with_name("logs") / f"{LOG_FILE_NAME}.log"

# Ensure the directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Print log file location to console so user knows where logs are
print(f" Logging to: {LOG_FILE}")
print(f" Log level: {os.getenv('LOG_LEVEL', 'LOG_TO_CONSOLE')}")
print("-" * 80)

# ------------------------------------------------------------------
# 2. Resolve log level from environment
# ------------------------------------------------------------------
LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOG_LEVEL = LEVEL_MAP.get(os.getenv("LOG_LEVEL", "DEBUG").upper(), logging.DEBUG)

# ------------------------------------------------------------------
# 3. Set up logging
# ------------------------------------------------------------------
logger = logging.getLogger(LOG_FILE_NAME)
logger.setLevel(LOG_LEVEL)        # change to DEBUG if needed

logger.propagate = False  # <--- KEY: Stop propagating to root (prevents inherited console output)

# Clear any existing handlers (defensive)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Customize format to show the filename (not full path)
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)-8s] [%(filename)s:%(funcName)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Optional: also log to console (disable with LOG_TO_CONSOLE=false)
log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() in ("true", "1", "yes")

if log_to_console:
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

# ------------------------------------------------------------------
# 4. Convenience functions
# ------------------------------------------------------------------
debug    = logger.debug
info     = logger.info
warning  = logger.warning
error    = logger.error
critical = logger.critical

# ------------------------------------------------------------------
# 5. Usage
# ------------------------------------------------------------------
"""
#Put this at the top of every Python file:
from logger import logger as log

#Then write logs like this everywhere:
log.debug("Parsing input data")
log.info("Connected to database")
log.warning("High memory usage detected")
log.error("Failed to send email")
log.critical("Cannot access configuration file")
"""

