from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
import uuid
from config import MONGO_URI, logger

# Initialize Connection
try:
    client = MongoClient(MONGO_URI)
    db = client['PrimeBotDB']
    
    users_col = db['users']
    content_col = db['contents']
    config_col = db['bot_config']
    
    # Indexes for fast search
    content_col.create_index([("content_type", ASCENDING), ("title_key", ASCENDING)], unique=True)
    content_col.create_index([("updated_at", DESCENDING)])
    users_col.create_index([("interaction_count", DESCENDING)])
    
    client.admin.command('ping')
    logger.info("MongoDB Connected Successfully!")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit(1)

# Unique ID generator
def compact_id() -> str:
    return uuid.uuid4().hex[:8]

def normalized_title(value: str) -> str:
    return " ".join(value.casefold().split())

# Core Database Functions
async def get_bot_config():
    config = config_col.find_one({"_id": "main_config"})
    if not config:
        config = {
            "_id": "main_config",
            "language": "hinglish",
            "delete_seconds": 300,
            "donate_qr_id": None,
            "user_menu_photo_id": None,
            "default_destination": None,
            "quotes_enabled": True,
            "co_admins": [],
            "appearance": {"font": "default", "style": "normal"},
            "links": {"backup": "", "download": "", "help": ""},
            "messages": {}
        }
        config_col.insert_one(config)
    return config

async def update_bot_config(update_data: dict):
    config_col.update_one({"_id": "main_config"}, {"$set": update_data}, upsert=True)

async def is_main_admin(user_id: int, main_admin_id: int) -> bool:
    return user_id == main_admin_id

async def is_co_admin(user_id: int, main_admin_id: int) -> bool:
    if user_id == main_admin_id:
        return True
    config = await get_bot_config()
    return user_id in config.get("co_admins", [])

async def track_user(user_id: int, first_name: str, full_name: str, username: str):
    users_col.update_one(
        {"_id": user_id},
        {
            "$set": {"first_name": first_name, "full_name": full_name, "username": username},
            "$inc": {"interaction_count": 1}
        },
        upsert=True
    )
