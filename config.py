import os
import logging
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Core Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
except ValueError:
    ADMIN_ID = 0
    logger.error("ADMIN_ID must be an integer!")

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN or not MONGO_URI or not ADMIN_ID:
    logger.error("CRITICAL ERROR: Missing BOT_TOKEN, MONGO_URI, or ADMIN_ID in .env file!")
    exit(1)
