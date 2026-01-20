from dotenv import load_dotenv
import os
from logger import logger as log
# Load .env file if it exists
load_dotenv()

log.critical(os.getenv("USER_NAME"))

log.debug("This is a debug statement")