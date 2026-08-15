# ============================================
# ===       PRIME LEVEL BOT (PART 1)       ===
# ===       IMPORTS & FONT ENGINE          ===
# ============================================
import os
import logging
import re
import asyncio
import threading
import httpx
import uuid
import html
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, User, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters, Defaults
)
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from flask import Flask, request
from waitress import serve

# --- Font Manager ---
FONT_MAPS = {
    'default': {},
    'small_caps': {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ',
        'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'Q', 'r': 'ʀ',
        's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H', 'I': 'I',
        'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P', 'Q': 'Q', 'R': 'R',
        'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X', 'Y': 'Y', 'Z': 'Z',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    },
    'sans_serif': {
        'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪',
        'j': '𝘫', 'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳',
        's': '𝘴', 't': '𝘵', 'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻',
        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐',
        'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙',
        'S': '𝘚', 'T': '𝘛', 'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡',
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦', '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫'
    },
    'sans_serif_bold': {
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    },
    'sans_serif_regular': {
        'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾', 'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 'i': '𝗂',
        'j': '𝗃', 'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈', 'p': '𝗉', 'q': '𝗊', 'r': '𝗋',
        's': '𝗌', 't': '𝗍', 'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 'y': '𝗒', 'z': '𝗓',
        'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤', 'F': '𝖥', 'G': '𝖦', 'H': '𝖧', 'I': '𝖨',
        'J': '𝖩', 'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮', 'P': '𝖯', 'Q': '𝖰', 'R': '𝖱',
        'S': '𝖲', 'T': '𝖳', 'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷', 'Y': '𝖸', 'Z': '𝖹',
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦', '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫'
    },
    'sans_serif_regular_bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    },
    'script': {
        'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': '𝑒', 'f': '𝒻', 'g': '𝑔', 'h': '𝒽', 'i': '𝒾',
        'j': '𝒿', 'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃', 'o': '𝑜', 'p': '𝓅', 'q': '𝓆', 'r': '𝓇',
        's': '𝓈', 't': '𝓉', 'u': '𝓊', 'v': '𝓋', 'w': '𝓌', 'x': '𝓍', 'y': '𝓎', 'z': '𝓏',
        'A': '𝒜', 'B': '𝐵', 'C': '𝒞', 'D': '𝒟', 'E': '𝐸', 'F': '𝐹', 'G': '𝒢', 'H': '𝐻', 'I': '𝐼',
        'J': '𝒥', 'K': '𝒦', 'L': '𝐿', 'M': '𝑀', 'N': '𝒩', 'O': '𝒪', 'P': '𝒫', 'Q': '𝒬', 'R': '𝑅',
        'S': '𝒮', 'T': '𝒯', 'U': '𝒰', 'V': '𝒱', 'W': '𝒲', 'X': '𝒳', 'Y': '𝒴', 'Z': '𝒵',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    },
    'script_bold': {
        'a': '𝓪', 'b': '𝓫', 'c': '𝓬', 'd': '𝓭', 'e': '𝓮', 'f': '𝓯', 'g': '𝓰', 'h': '𝓱', 'i': '𝓲',
        'j': '𝓳', 'k': '𝓴', 'l': '𝓵', 'm': '𝓶', 'n': '𝓷', 'o': '𝓸', 'p': '𝓹', 'q': '𝓺', 'r': '𝓻',
        's': '𝓼', 't': '𝓽', 'u': '𝓾', 'v': '𝓿', 'w': '𝔀', 'x': '𝔁', 'y': '𝔂', 'z': '𝔃',
        'A': '𝓐', 'B': '𝓑', 'C': '𝓒', 'D': '𝓓', 'E': '𝓔', 'F': '𝓕', 'G': '𝓖', 'H': '𝓗', 'I': '𝓘',
        'J': '𝓙', 'K': '𝓚', 'L': '𝓛', 'M': '𝓜', 'N': '𝓝', 'O': '𝓞', 'P': '𝓟', 'Q': '𝓠', 'R': '𝓡',
        'S': '𝓢', 'T': '𝓣', 'U': '𝓤', 'V': '𝓥', 'W': '𝓦', 'X': '𝓧', 'Y': '𝓨', 'Z': '𝓩',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    },
    'monospace': {
        'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐', 'h': '𝚑', 'i': '𝚒',
        'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗', 'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛',
        's': '𝚜', 't': '𝚝', 'u': '𝚞', 'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
        'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶', 'H': '𝙷', 'I': '𝙸',
        'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽', 'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁',
        'S': '𝚂', 'T': '𝚃', 'U': '𝚄', 'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
        '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿'
    },
    'serif': {
        'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪',
        'j': '𝘫', 'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳',
        's': '𝘴', 't': '𝘵', 'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻',
        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐',
        'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙',
        'S': '𝘚', 'T': '𝘛', 'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    },
    'serif_bold': {
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'
    }
}
FONT_MAPS['small_caps_bold'] = FONT_MAPS['small_caps']
FONT_MAPS['monospace_bold'] = FONT_MAPS['monospace']
FONT_MAPS['default_bold'] = {
    'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
    'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
    's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
    'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
    'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
    'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
    '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
}

# ============================================
# ===       BOT SETUP & DB CONFIG          ===
# ============================================
load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

if not BOT_TOKEN or not MONGO_URI or not ADMIN_ID:
    logger.error("Error: Secrets missing. Check BOT_TOKEN, MONGO_URI, and ADMIN_ID.")
    exit()

try:
    logger.info("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client['PrimeLevelBotDB']
    users_collection = db['users']
    contents_collection = db['contents'] # For both Movies and Series
    config_collection = db['config']
    post_log_collection = db['post_log']
    
    contents_collection.create_index([("content_type", ASCENDING), ("title_key", ASCENDING)], unique=True)
    contents_collection.create_index([("content_type", ASCENDING), ("updated_at", DESCENDING)])
    users_collection.create_index([("interaction_count", DESCENDING)])
    
    client.admin.command('ping')
    logger.info("MongoDB connected successfully!")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit()

ITEMS_PER_PAGE = 10
QUALITY_OPTIONS = ("480p", "720p", "1080p", "4K")
DESCRIPTION_PREVIEW_LIMIT = 850
TELEGRAM_CAPTION_LIMIT = 1024

def compact_id() -> str:
    """Unique ID generator for seasons and episodes"""
    return uuid.uuid4().hex[:8]

def normalized_title(value: str) -> str:
    return " ".join(value.casefold().split())

# ============================================
# ===       ADMIN & CO-ADMIN CHECKER       ===
# ============================================
async def is_main_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def is_co_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    config = await get_config()
    return user_id in config.get("co_admins", [])

async def increment_user_interaction(user_id: int):
    try:
        users_collection.update_one(
            {"_id": user_id},
            {"$inc": {"interaction_count": 1}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Interaction count update error: {e}")

# ============================================
# ===       CONFIG & MESSAGE FORMATTER     ===
# ============================================
async def get_default_messages():
    return {
        "welcome": "Welcome, {name}! Use the buttons below.",
        "user_welcome_admin": "Salaam, Admin! Admin panel ke liye /menu use karein.",
        "user_welcome_basic": "Salaam, {full_name}! Apna user menu dekhne ke liye /user use karein.",
        "user_not_admin": "Aap admin nahi hain.",
        "user_dl_dm_alert": "✅ <f>Check your DM (private chat) with me!</f>",
        "user_dl_movie_not_found": "❌ <f>Error: Content nahi mila.</f>",
        "user_dl_file_error": "❌ <f>Error! {quality} file nahi bhej paya. Please try again.</f>",
        "user_dl_fetching": "⏳ <f>Fetching files...</f>",
        "user_dl_sending_file": "✅ <b>{movie_name}</b> | <b>{quality}</b>\n\n<f>Aapki file bhej raha hoon...</f>",
        "user_dl_select_quality": "<b>{title}</b>\n\n<f>Quality select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {minutes} minute(s) mein automatically delete ho jaayegi.</f></b>",
        "user_donate_qr_text": "❤️ <b><f>Support Us!</f></b>\n\n<f>Agar aapko hamara kaam pasand aata hai, toh aap humein support kar sakte hain.</f>",
        "admin_cancel": "<f>Operation cancel kar diya gaya hai.</f>",
        "post_gen_caption": "🎬 <b>{title}</b>\n\n{description}\n\n<f>Neeche button se download karein!</f>"
    }

async def get_config():
    config = config_collection.find_one({"_id": "bot_config"})
    default_messages = await get_default_messages()

    if not config:
        config = {
            "_id": "bot_config",
            "language": "en",
            "donate_qr_id": None,
            "links": {"backup": "https://t.me/", "download": None, "help": "https://t.me/"},
            "user_menu_photo_id": None,
            "default_destination": None,
            "delete_seconds": 300,
            "messages": default_messages,
            "co_admins": [],
            "appearance": {"font": "default", "style": "normal"},
            "quotes_enabled": True
        }
        config_collection.insert_one(config)
        return config
    
    # Auto-update missing keys
    needs_update = False
    for key in ["delete_seconds", "default_destination", "quotes_enabled", "co_admins", "appearance", "links", "messages"]:
        if key not in config:
            needs_update = True
    
    if needs_update:
        config.setdefault("quotes_enabled", True)
        config.setdefault("default_destination", None)
        config.setdefault("delete_seconds", 300)
        config.setdefault("co_admins", [])
        config.setdefault("appearance", {"font": "default", "style": "normal"})
        config.setdefault("links", {"backup": "https://t.me/", "download": None, "help": "https://t.me/"})
        config.setdefault("messages", default_messages)
        config_collection.update_one({"_id": "bot_config"}, {"$set": config})

    return config

async def apply_font_formatting(raw_text: str, font_settings: dict) -> str:
    font = font_settings.get('font', 'default')
    style = font_settings.get('style', 'normal')
    
    if font == 'default' and style == 'normal':
        return raw_text.replace('<f>', '').replace('</f>', '')

    map_key = f"{font}_{style}" if style == 'bold' else font
    font_map = FONT_MAPS.get(map_key, {})
    
    if not font_map:
        map_key = 'default_bold' if style == 'bold' else 'default'
        font_map = FONT_MAPS.get(map_key, {})
        if not font_map:
            return raw_text.replace('<f>', '').replace('</f>', '')

    def replace_chars_html_safe(text_chunk):
        return "".join([font_map.get(char, char) for char in text_chunk])

    def process_tags(match):
        content = match.group(1)
        parts = re.split(r'(<[^>]+>)', content)
        
        processed_parts = []
        for part in parts:
            if re.match(r'<[^>]+>', part):
                processed_parts.append(part)
            else:
                processed_parts.append(replace_chars_html_safe(part))
        return "".join(processed_parts)

    try:
        formatted_text = re.sub(r'<f>(.*?)</f>', process_tags, raw_text, flags=re.DOTALL)
        return formatted_text
    except Exception as e:
        logger.error(f"Font formatting error: {e}")
        return raw_text.replace('<f>', '').replace('</f>', '')

async def format_message(context: ContextTypes.DEFAULT_TYPE, key: str, variables: dict = None) -> str:
    config = await get_config()
    default_messages = await get_default_messages()
    raw_text = config.get("messages", {}).get(key, default_messages.get(key, f"MISSING_KEY: {key}"))
    
    if variables:
        safe_variables = {}
        for k, v in variables.items():
            if isinstance(v, str):
                safe_variables[k] = v.replace('<', '&lt;').replace('>', '&gt;')
            else:
                safe_variables[k] = v
        try:
            text_with_vars = raw_text.format(**safe_variables)
        except Exception as e:
            logger.error(f"Message format error: {e}")
            text_with_vars = raw_text
    else:
        text_with_vars = raw_text

    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    return await apply_font_formatting(text_with_vars, font_settings)

def quote_text(description: str, enable_quotes: bool) -> str:
    description = html.escape(description.strip(), quote=False)
    if not description:
        return ""
    if enable_quotes:
        tag = "blockquote expandable" if len(description) > 180 else "blockquote"
        return f"<{tag}>{description}</blockquote>"
    return description

# ============================================
# ===       PAGINATION HELPER              ===
# ============================================
def build_grid_keyboard(buttons, items_per_row=2):
    keyboard = []
    row = []
    for button in buttons:
        row.append(button)
        if len(row) == items_per_row:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard

async def build_paginated_keyboard(
    collection,
    page: int,
    page_callback_prefix: str,
    item_callback_prefix: str,
    back_callback: str,
    filter_query: dict = None,
):
    if filter_query is None:
        filter_query = {}
        
    skip = page * ITEMS_PER_PAGE
    total_items = collection.count_documents(filter_query)
    
    items = list(collection.find(filter_query).sort("updated_at", DESCENDING).skip(skip).limit(ITEMS_PER_PAGE))
    
    if not items and page == 0:
        return None, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]])
        
    buttons = []
    for item in items:
        if "title" in item:
            buttons.append(InlineKeyboardButton(item['title'], callback_data=f"{item_callback_prefix}{str(item['_id'])}"))

    keyboard = build_grid_keyboard(buttons, items_per_row=2)
    
    page_buttons = []
    if page > 0:
        page_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{page_callback_prefix}{page - 1}"))
    if (page + 1) * ITEMS_PER_PAGE < total_items:
        page_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"{page_callback_prefix}{page + 1}"))
        
    if page_buttons:
        keyboard.append(page_buttons)
        
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_callback)])
    
    return items, InlineKeyboardMarkup(keyboard)
# ============================================
# ===       PRIME LEVEL BOT (PART 2)       ===
# ===       CONVERSATION STATES & ADMIN    ===
# ============================================

# Conversation States
(
    M_GET_TITLE, M_GET_POSTER, M_GET_DESC, M_GET_QUAL,
    S_GET_TITLE, S_GET_POSTER, S_GET_DESC, S_GET_SEASON, S_GET_EPISODE, S_GET_QUAL,
    POST_GET_ITEM, POST_GET_LINK, POST_GET_DEST, POST_PREVIEW, POST_EDIT_TITLE, POST_EDIT_DESC,
    MSG_GET_INPUT, CUSTOM_POST_POSTER, CUSTOM_POST_CAPTION, CUSTOM_POST_BTN_TEXT, CUSTOM_POST_BTN_URL,
    SET_DEST_INPUT, DEL_TIME_INPUT, COADMIN_ADD, COADMIN_REM, BRD_INPUT, GET_QR_INPUT, LINK_INPUT
) = range(28)

async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels any ongoing conversation and returns to Admin Menu"""
    context.user_data.clear()
    text = await format_message(context, "admin_cancel")
    if update.callback_query:
        await update.callback_query.answer("Cancelled!")
        await admin_command(update, context, from_callback=True)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

# ============================================
# ===       MAIN ADMIN DASHBOARD           ===
# ============================================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    if not await is_co_admin(user_id):
        if not from_callback:
            text = await format_message(context, "user_not_admin")
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Content", callback_data="menu_add_content"),
         InlineKeyboardButton("🗑️ Manage Content", callback_data="menu_manage_content")],
        [InlineKeyboardButton("✍️ Post Generator", callback_data="menu_post_gen"),
         InlineKeyboardButton("🔗 Gen Link", callback_data="menu_gen_link")],
        [InlineKeyboardButton("📝 Message Settings", callback_data="menu_msg_settings"),
         InlineKeyboardButton("⚙️ Bot Settings", callback_data="menu_bot_settings")]
    ]
    
    if await is_main_admin(user_id):
        keyboard.append([InlineKeyboardButton("📢 Broadcast & Stats", callback_data="menu_broadcast_stats")])
        admin_text = "👑 <b>Prime Admin Dashboard</b> 👑\n\nMain Admin Panel. Select an option below to manage your bot:"
    else:
        admin_text = "👑 <b>Co-Admin Dashboard</b> 👑\n\nSelect an option below to manage content:"

    reply_markup = InlineKeyboardMarkup(keyboard)

    if from_callback:
        query = update.callback_query
        try:
            if query.message.photo:
                await query.message.delete()
                await context.bot.send_message(query.from_user.id, admin_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except BadRequest:
            await query.answer()
    else:
        await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===       ADD CONTENT MENU (SPLIT)       ===
# ============================================
async def menu_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Add Movie", callback_data="start_add_movie")],
        [InlineKeyboardButton("📺 Add Web Series", callback_data="start_add_series")],
        [InlineKeyboardButton("📺 Add Season/Ep to Series", callback_data="start_append_series")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("➕ <b>Add Content</b>\n\nAap kya add karna chahte hain?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# ============================================
# ===       ADD MOVIE FLOW                 ===
# ============================================
async def start_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    context.user_data['content_type'] = 'movie'
    context.user_data['files'] = {}
    await query.edit_message_text("🎬 <b>Send Movie Title:</b>\n\n/cancel - To stop.", parse_mode=ParseMode.HTML)
    return M_GET_TITLE

async def get_movie_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("🖼️ <b>Send Poster Photo (or /skip):</b>\n\n/cancel - To stop.", parse_mode=ParseMode.HTML)
    return M_GET_POSTER

async def get_movie_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['poster_id'] = update.message.photo[-1].file_id
    elif update.message.text != '/skip':
        await update.message.reply_text("Please send a valid photo or /skip.")
        return M_GET_POSTER
    await update.message.reply_text("📝 <b>Send Description/Synopsis (or /skip):</b>\n\n/cancel - To stop.", parse_mode=ParseMode.HTML)
    return M_GET_DESC

async def get_movie_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != '/skip':
        context.user_data['description'] = update.message.text
    else:
        context.user_data['description'] = ""
    await show_quality_menu(update.message, context, is_series=False)
    return M_GET_QUAL

async def show_quality_menu(message, context, is_series=False):
    files = context.user_data.get('files', {})
    cb_prefix = "squal_" if is_series else "mqual_"
    keyboard = [[InlineKeyboardButton(f"{q} {'✅' if q in files else ''}", callback_data=f"{cb_prefix}{q}")] for q in QUALITY_OPTIONS]
    
    save_cb = "save_series_ep" if is_series else "save_movie"
    keyboard.append([InlineKeyboardButton("💾 Save Content", callback_data=save_cb)])
    
    item_name = context.user_data.get('curr_ep_title', context.user_data.get('title', 'Content'))
    await message.reply_text(f"🎥 <b>Select Quality to Upload for: {item_name}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def movie_quality_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "save_movie":
        if not context.user_data.get('files'):
            await query.answer("Upload at least 1 file!", show_alert=True)
            return M_GET_QUAL
        
        # Save to DB
        doc = {
            "title": context.user_data['title'],
            "title_key": normalized_title(context.user_data['title']),
            "content_type": "movie",
            "description": context.user_data.get('description', ''),
            "poster_id": context.user_data.get('poster_id'),
            "files": context.user_data['files'],
            "updated_at": datetime.now()
        }
        try:
            contents_collection.insert_one(doc)
            await query.edit_message_text(f"✅ <b>{doc['title']}</b> saved successfully!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.edit_message_text(f"❌ Error saving movie: Title might already exist.\n{e}", parse_mode=ParseMode.HTML)
            
        await asyncio.sleep(2)
        await admin_command(update, context, from_callback=True)
        return ConversationHandler.END

    # Wait for file
    quality = query.data.replace("mqual_", "")
    context.user_data['current_quality'] = quality
    await query.edit_message_text(f"Send the video/file for <b>{quality}</b>:", parse_mode=ParseMode.HTML)
    return M_GET_QUAL

async def movie_quality_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fid = None
    if update.message.video:
        fid = update.message.video.file_id
    elif update.message.document:
        fid = update.message.document.file_id
        
    if not fid:
        await update.message.reply_text("Please send a valid video or document file.")
        return M_GET_QUAL
        
    quality = context.user_data['current_quality']
    context.user_data['files'][quality] = fid
    await update.message.reply_text(f"✅ {quality} file saved!")
    await show_quality_menu(update.message, context, is_series=False)
    return M_GET_QUAL

# ============================================
# ===       ADD SERIES FLOW                ===
# ============================================
async def start_add_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    context.user_data['content_type'] = 'series'
    context.user_data['seasons'] = []
    await query.edit_message_text("📺 <b>Send Web Series Title:</b>\n\n/cancel - To stop.", parse_mode=ParseMode.HTML)
    return S_GET_TITLE

async def get_series_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("🖼️ <b>Send Series Poster Photo (or /skip):</b>", parse_mode=ParseMode.HTML)
    return S_GET_POSTER

async def get_series_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['poster_id'] = update.message.photo[-1].file_id
    elif update.message.text != '/skip':
        await update.message.reply_text("Please send a valid photo or /skip.")
        return S_GET_POSTER
    await update.message.reply_text("📝 <b>Send Series Description (or /skip):</b>", parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def get_series_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != '/skip':
        context.user_data['description'] = update.message.text
    else:
        context.user_data['description'] = ""
        
    # Save base series doc
    doc = {
        "title": context.user_data['title'],
        "title_key": normalized_title(context.user_data['title']),
        "content_type": "series",
        "description": context.user_data.get('description', ''),
        "poster_id": context.user_data.get('poster_id'),
        "seasons": [],
        "updated_at": datetime.now()
    }
    try:
        inserted = contents_collection.insert_one(doc)
        context.user_data['series_id'] = str(inserted.inserted_id)
        await update.message.reply_text(f"✅ Series '{doc['title']}' created!\n\nNow send the <b>Season Title</b> (e.g., Season 1):", parse_mode=ParseMode.HTML)
        return S_GET_SEASON
    except Exception as e:
        await update.message.reply_text(f"❌ Error: Title might already exist.\n{e}")
        return ConversationHandler.END

async def get_series_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = compact_id()
    context.user_data['curr_sid'] = sid
    season_title = update.message.text
    season = {"sid": sid, "title": season_title, "episodes": []}
    
    contents_collection.update_one(
        {"_id": ObjectId(context.user_data['series_id'])},
        {"$push": {"seasons": season}, "$set": {"updated_at": datetime.now()}}
    )
    
    await update.message.reply_text(f"✅ '{season_title}' added!\n\nNow send <b>Episode Title</b> (e.g., Episode 1):", parse_mode=ParseMode.HTML)
    context.user_data['files'] = {}
    return S_GET_EPISODE

async def get_series_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['curr_ep_title'] = update.message.text
    await show_quality_menu(update.message, context, is_series=True)
    return S_GET_QUAL

async def series_quality_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "save_series_ep":
        if not context.user_data.get('files'):
            await query.answer("Upload at least 1 file!", show_alert=True)
            return S_GET_QUAL
        
        episode = {
            "eid": compact_id(),
            "title": context.user_data['curr_ep_title'],
            "files": context.user_data['files']
        }
        
        contents_collection.update_one(
            {"_id": ObjectId(context.user_data['series_id']), "seasons.sid": context.user_data['curr_sid']},
            {"$push": {"seasons.$.episodes": episode}, "$set": {"updated_at": datetime.now()}}
        )
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Another Episode", callback_data="app_new_ep")],
            [InlineKeyboardButton("➕ Add New Season", callback_data="app_new_season")],
            [InlineKeyboardButton("✅ Done (Back to Admin)", callback_data="admin_menu")]
        ]
        await query.edit_message_text(f"✅ Episode saved! What do you want to do next?", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
        
    quality = query.data.replace("squal_", "")
    context.user_data['current_quality'] = quality
    await query.edit_message_text(f"Send the video/file for <b>{quality}</b>:", parse_mode=ParseMode.HTML)
    return S_GET_QUAL

async def series_quality_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fid = None
    if update.message.video:
        fid = update.message.video.file_id
    elif update.message.document:
        fid = update.message.document.file_id
        
    if not fid:
        await update.message.reply_text("Please send a valid video or document file.")
        return S_GET_QUAL
        
    quality = context.user_data['current_quality']
    context.user_data['files'][quality] = fid
    await update.message.reply_text(f"✅ {quality} file saved!")
    await show_quality_menu(update.message, context, is_series=True)
    return S_GET_QUAL
# ============================================
# ===       PRIME LEVEL BOT (PART 3)       ===
# ===       MANAGE CONTENT & POST GEN      ===
# ============================================

# ============================================
# ===       MANAGE CONTENT FLOW            ===
# ============================================
async def menu_manage_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Movie", callback_data="manage_del_movie"),
         InlineKeyboardButton("🗑️ Delete Series", callback_data="manage_del_series")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("🗑️ <b>Manage Content</b>\n\nSelect content type to delete:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def manage_del_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    if query.data.startswith("del_m_page_"):
        page = int(query.data.split("_")[-1])
    await query.answer()
    
    items, kb = await build_paginated_keyboard(contents_collection, page, "del_m_page_", "del_item_", "menu_manage_content", {"content_type": "movie"})
    if not items and page == 0:
        await query.edit_message_text("❌ No movies found.", reply_markup=kb)
    else:
        await query.edit_message_text(f"🗑️ Select Movie to Delete (Page {page+1}):", reply_markup=kb)

async def manage_del_series_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    if query.data.startswith("del_s_page_"):
        page = int(query.data.split("_")[-1])
    await query.answer()
    
    items, kb = await build_paginated_keyboard(contents_collection, page, "del_s_page_", "del_item_", "menu_manage_content", {"content_type": "series"})
    if not items and page == 0:
        await query.edit_message_text("❌ No web series found.", reply_markup=kb)
    else:
        await query.edit_message_text(f"🗑️ Select Web Series to Delete (Page {page+1}):", reply_markup=kb)

async def delete_item_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("del_item_", "")
    contents_collection.delete_one({"_id": ObjectId(item_id)})
    await query.edit_message_text("✅ Content successfully deleted!")
    await asyncio.sleep(2)
    await admin_command(update, context, from_callback=True)

# ============================================
# ===       POST GENERATOR FLOW            ===
# ============================================
async def menu_post_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    dest = config.get("default_destination", "Not Set")
    
    keyboard = [
        [InlineKeyboardButton(f"🎯 Set Default ID ({dest})", callback_data="post_set_dest")],
        [InlineKeyboardButton("🎬 Movie Post", callback_data="post_sel_movie_0"),
         InlineKeyboardButton("📺 Series Post", callback_data="post_sel_series_0")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("✍️ <b>Post Generator</b>\n\nGenerate beautiful posts with shortlinks seamlessly.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def post_set_dest_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Send Default Channel/Group ID (e.g. -10012345 or @MyChannel):")
    return SET_DEST_INPUT

async def post_save_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"default_destination": update.message.text}})
    await update.message.reply_text("✅ Default Destination Saved!")
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

async def post_select_list(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str, page: int = 0):
    query = update.callback_query
    if query.data.startswith("post_sel_"):
        parts = query.data.split("_")
        content_type = parts[2]
        page = int(parts[3])
    await query.answer()
    
    prefix = f"post_sel_{content_type}_"
    items, kb = await build_paginated_keyboard(contents_collection, page, prefix, "post_pick_", "menu_post_gen", {"content_type": content_type})
    
    if not items and page == 0:
        await query.edit_message_text(f"❌ No {content_type} found.", reply_markup=kb)
    else:
        await query.edit_message_text(f"Select {content_type.capitalize()} to Post (Page {page+1}):", reply_markup=kb)
    return POST_GET_ITEM

async def post_pick_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("post_pick_", "")
    doc = contents_collection.find_one({"_id": ObjectId(item_id)})
    if not doc:
        return ConversationHandler.END
        
    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=dl_{item_id}"
    context.user_data['post_doc'] = doc
    context.user_data['deep_link'] = deep_link
    context.user_data['temp_title'] = doc['title']
    context.user_data['temp_desc'] = doc.get('description', '')
    
    await query.edit_message_text(f"✅ <b>{doc['title']}</b> selected.\n\nOriginal Deep Link:\n<code>{deep_link}</code>\n\nSend the <b>Shortened Link</b> (or send the same link if no shortener is used):", parse_mode=ParseMode.HTML)
    return POST_GET_LINK

async def post_get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['short_link'] = update.message.text
    await show_post_preview(update.message, context)
    return POST_PREVIEW

async def show_post_preview(message, context):
    config = await get_config()
    doc = context.user_data['post_doc']
    title = context.user_data['temp_title']
    
    # Formatter applies font settings to caption template
    caption_template = config.get("messages", {}).get("post_gen_caption", "🎬 <b>{title}</b>\n\n{description}\n\n<f>Neeche button se download karein!</f>")
    raw_desc = context.user_data['temp_desc']
    formatted_desc = quote_text(raw_desc, config.get("quotes_enabled", True))
    
    # Apply vars
    caption_raw = caption_template.format(title=title, description=formatted_desc)
    
    # Apply fonts
    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    final_caption = await apply_font_formatting(caption_raw, font_settings)
    
    # Build Buttons
    kb = []
    links = config.get("links", {})
    if links.get("backup"): 
        kb.append(InlineKeyboardButton("🔄 Backup", url=links["backup"]))
    if config.get("donate_qr_id") or links.get("help"): 
        kb.append(InlineKeyboardButton("🆘 Support", url=links.get("help", "https://t.me/")))
    
    btn_row = [InlineKeyboardButton("📥 Download", url=context.user_data['short_link'])]
    reply_markup = InlineKeyboardMarkup([kb, btn_row] if kb else [btn_row])
    
    context.user_data['final_kb'] = reply_markup
    context.user_data['final_cap'] = final_caption

    control_kb = [
        [InlineKeyboardButton("✅ Publish to Default ID", callback_data="post_pub_def"),
         InlineKeyboardButton("🚀 Publish to Custom ID", callback_data="post_pub_cust")],
        [InlineKeyboardButton("✏️ Edit Temp Title", callback_data="post_edit_t"),
         InlineKeyboardButton("✏️ Edit Temp Desc", callback_data="post_edit_d")],
        [InlineKeyboardButton("⬅️ Cancel", callback_data="admin_menu")]
    ]
    
    if doc.get('poster_id'):
        await message.reply_photo(photo=doc['poster_id'], caption=final_caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(control_kb))
    else:
        await message.reply_text(text=final_caption, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(control_kb))

async def post_handle_controls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "post_edit_t":
        await query.message.reply_text("Send temporary Title for this post:")
        return POST_EDIT_TITLE
    elif query.data == "post_edit_d":
        await query.message.reply_text("Send temporary Description for this post:")
        return POST_EDIT_DESC
    elif query.data == "post_pub_def":
        config = await get_config()
        dest = config.get("default_destination")
        if not dest:
            await query.answer("No Default Destination Set!", show_alert=True)
            return POST_PREVIEW
        await execute_publish(context, query.message, dest)
        return ConversationHandler.END
    elif query.data == "post_pub_cust":
        await query.message.reply_text("Send Target Channel/Group ID:")
        return POST_GET_DEST
    elif query.data == "admin_menu":
        await admin_command(update, context, from_callback=True)
        return ConversationHandler.END

async def post_edit_t(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_title'] = update.message.text
    await show_post_preview(update.message, context)
    return POST_PREVIEW

async def post_edit_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_desc'] = update.message.text
    await show_post_preview(update.message, context)
    return POST_PREVIEW

async def post_get_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await execute_publish(context, update.message, update.message.text)
    return ConversationHandler.END

async def execute_publish(context, message, chat_id):
    try:
        if context.user_data['post_doc'].get('poster_id'):
            await context.bot.send_photo(chat_id=chat_id, photo=context.user_data['post_doc']['poster_id'], caption=context.user_data['final_cap'], reply_markup=context.user_data['final_kb'], parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text=context.user_data['final_cap'], reply_markup=context.user_data['final_kb'], parse_mode=ParseMode.HTML)
        
        await message.reply_text(f"✅ Post Published successfully to {chat_id}!")
    except Exception as e:
        await message.reply_text(f"❌ Error publishing: {e}")
        
    context.user_data.clear()

# ============================================
# ===       SETTINGS & MESSAGES            ===
# ============================================
async def menu_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌍 Language", callback_data="set_language"),
         InlineKeyboardButton("🎨 Font Style", callback_data="set_font_style")],
        [InlineKeyboardButton("❤️ Donation QR", callback_data="set_donate_qr"),
         InlineKeyboardButton("🔗 Other Links", callback_data="set_links")],
        [InlineKeyboardButton("⏱️ Auto-Delete Time", callback_data="set_autodel")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("⚙️ <b>Bot Settings</b>\n\nConfigure core parameters:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def menu_msg_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    quote_status = "✅ Enabled" if config.get("quotes_enabled", True) else "❌ Disabled"
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit Welcome Msg", callback_data="msg_edit_welcome")],
        [InlineKeyboardButton("📝 Edit Post Caption Format", callback_data="msg_edit_post_gen_caption")],
        [InlineKeyboardButton(f"💬 Blockquotes: {quote_status}", callback_data="toggle_quotes")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("⚙️ <b>Message Settings</b>\n\nEdit texts or toggle quote formatting.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def toggle_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = await get_config()
    new_stat = not config.get("quotes_enabled", True)
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"quotes_enabled": new_stat}})
    await menu_msg_settings(update, context)

async def msg_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("msg_edit_", "")
    context.user_data['msg_key'] = key
    config = await get_config()
    curr = config.get("messages", {}).get(key, "Not set")
    await query.edit_message_text(f"Editing <b>{key}</b>\n\nCurrent:\n<code>{curr}</code>\n\nSend new message (HTML & <f> tags allowed):", parse_mode=ParseMode.HTML)
    return MSG_GET_INPUT

async def msg_edit_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"messages.{context.user_data['msg_key']}": update.message.text}})
    await update.message.reply_text("✅ Message Updated!")
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END
# ============================================
# ===       PRIME LEVEL BOT (PART 4)       ===
# ===       GEN LINK, BROADCAST & MAIN     ===
# ============================================

# ============================================
# ===       GENERATE LINK FLOW             ===
# ============================================
async def menu_gen_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Link", callback_data="gen_sel_movie_0"),
         InlineKeyboardButton("📺 Series Link", callback_data="gen_sel_series_0")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text("🔗 <b>Generate Link</b>\n\nSelect content type:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def gen_select_list(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str = "movie", page: int = 0):
    query = update.callback_query
    if query.data.startswith("gen_sel_"):
        parts = query.data.split("_")
        content_type = parts[2]
        page = int(parts[3])
    await query.answer()
    
    prefix = f"gen_sel_{content_type}_"
    items, kb = await build_paginated_keyboard(contents_collection, page, prefix, "gen_pick_", "menu_gen_link", {"content_type": content_type})
    
    if not items and page == 0:
        await query.edit_message_text(f"❌ No {content_type} found.", reply_markup=kb)
    else:
        await query.edit_message_text(f"Select {content_type.capitalize()} to Generate Link (Page {page+1}):", reply_markup=kb)

async def gen_pick_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = query.data.replace("gen_pick_", "")
    doc = contents_collection.find_one({"_id": ObjectId(item_id)})
    if not doc:
        return
        
    bot_username = (await context.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=dl_{item_id}"
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_gen_link")]]
    await query.edit_message_text(f"✅ <b>Link Generated for: {doc['title']}</b>\n\n<code>{deep_link}</code>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================
# ===       BROADCAST & STATS              ===
# ============================================
async def menu_broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    total_users = users_collection.count_documents({})
    total_movies = contents_collection.count_documents({"content_type": "movie"})
    total_series = contents_collection.count_documents({"content_type": "series"})
    
    text = f"📊 <b>Bot Statistics</b>\n\n👥 Total Users: <b>{total_users}</b>\n🎬 Total Movies: <b>{total_movies}</b>\n📺 Total Series: <b>{total_series}</b>"
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="start_broadcast")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("📢 Send the message/photo/video you want to broadcast:\n\n/cancel to stop.")
    return BRD_INPUT

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    total_users = users_collection.count_documents({})
    await msg.reply_text(f"⏳ Starting broadcast to {total_users} users... This might take a while.")
    
    sent = 0
    failed = 0
    users = users_collection.find({}, {"_id": 1})
    
    for user in users:
        try:
            await msg.copy(chat_id=user["_id"])
            sent += 1
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            await msg.copy(chat_id=user["_id"])
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05) # Prevent flood waits
        
    await msg.reply_text(f"✅ Broadcast Complete!\n\n📤 Sent: {sent}\n❌ Failed/Blocked: {failed}")
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

# ============================================
# ===       USER DOWNLOAD FLOW             ===
# ============================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await increment_user_interaction(user.id)
    
    args = context.args
    if args and args[0].startswith("dl_"):
        await handle_deep_link(update, context, args[0].replace("dl_", ""))
        return

    text = await format_message(context, "user_welcome_basic", {"full_name": user.full_name})
    if await is_co_admin(user.id):
        text = await format_message(context, "user_welcome_admin")
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE, item_id: str):
    doc = contents_collection.find_one({"_id": ObjectId(item_id)})
    user_id = update.effective_user.id
    
    if not doc:
        msg = await format_message(context, "user_dl_movie_not_found")
        await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML)
        return

    if doc['content_type'] == 'movie':
        qualities = doc.get('files', {})
        kb = [[InlineKeyboardButton(q, callback_data=f"send_m_{item_id}_{q}")] for q in qualities]
        msg = await format_message(context, "user_dl_select_quality", {"title": doc['title']})
        
        if doc.get('poster_id'):
            await context.bot.send_photo(chat_id=user_id, photo=doc['poster_id'], caption=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
            
    elif doc['content_type'] == 'series':
        seasons = doc.get('seasons', [])
        kb = [[InlineKeyboardButton(s['title'], callback_data=f"sel_s_{item_id}_{s['sid']}")] for s in seasons]
        msg = f"📺 <b>{doc['title']}</b>\n\nSelect a Season:"
        
        if doc.get('poster_id'):
            await context.bot.send_photo(chat_id=user_id, photo=doc['poster_id'], caption=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))

async def user_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    await query.answer()
    
    # 1. SEND MOVIE FILE
    if data.startswith("send_m_"):
        parts = data.split("_")
        item_id = parts[2]
        quality = parts[3]
        
        doc = contents_collection.find_one({"_id": ObjectId(item_id)})
        file_id = doc['files'].get(quality)
        
        if file_id:
            msg = await format_message(context, "user_dl_sending_file", {"movie_name": doc['title'], "quality": quality})
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML)
            sent_msg = await context.bot.send_document(chat_id=user_id, document=file_id, caption=f"🎬 <b>{doc['title']}</b> ({quality})", parse_mode=ParseMode.HTML)
            
            # Auto Delete Logic
            config = await get_config()
            del_time = config.get("delete_seconds", 300)
            asyncio.create_task(delete_message_later(context.bot, user_id, sent_msg.message_id, del_time))
        else:
            err = await format_message(context, "user_dl_file_error", {"quality": quality})
            await context.bot.send_message(chat_id=user_id, text=err, parse_mode=ParseMode.HTML)

    # 2. SELECT SERIES SEASON -> SHOW EPISODES
    elif data.startswith("sel_s_"):
        parts = data.split("_")
        item_id = parts[2]
        sid = parts[3]
        
        doc = contents_collection.find_one({"_id": ObjectId(item_id)})
        season = next((s for s in doc['seasons'] if s['sid'] == sid), None)
        
        if season:
            kb = [[InlineKeyboardButton(e['title'], callback_data=f"sel_e_{item_id}_{sid}_{e['eid']}")] for e in season.get('episodes', [])]
            kb.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_ser_{item_id}")])
            await query.edit_message_caption(caption=f"📺 <b>{doc['title']} - {season['title']}</b>\n\nSelect an Episode:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # 3. SELECT SERIES EPISODE -> SHOW QUALITIES
    elif data.startswith("sel_e_"):
        parts = data.split("_")
        item_id = parts[2]
        sid = parts[3]
        eid = parts[4]
        
        doc = contents_collection.find_one({"_id": ObjectId(item_id)})
        season = next((s for s in doc['seasons'] if s['sid'] == sid), None)
        ep = next((e for e in season['episodes'] if e['eid'] == eid), None)
        
        if ep:
            kb = [[InlineKeyboardButton(q, callback_data=f"send_s_{item_id}_{sid}_{eid}_{q}")] for q in ep.get('files', {})]
            kb.append([InlineKeyboardButton("⬅️ Back", callback_data=f"sel_s_{item_id}_{sid}")])
            await query.edit_message_caption(caption=f"📺 <b>{doc['title']} - {ep['title']}</b>\n\nSelect Quality:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # 4. SEND SERIES FILE
    elif data.startswith("send_s_"):
        parts = data.split("_")
        item_id = parts[2]
        sid = parts[3]
        eid = parts[4]
        quality = parts[5]
        
        doc = contents_collection.find_one({"_id": ObjectId(item_id)})
        season = next((s for s in doc['seasons'] if s['sid'] == sid), None)
        ep = next((e for e in season['episodes'] if e['eid'] == eid), None)
        file_id = ep['files'].get(quality)
        
        if file_id:
            msg = await format_message(context, "user_dl_sending_file", {"movie_name": ep['title'], "quality": quality})
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML)
            sent_msg = await context.bot.send_document(chat_id=user_id, document=file_id, caption=f"📺 <b>{doc['title']} - {ep['title']}</b> ({quality})", parse_mode=ParseMode.HTML)
            
            # Auto Delete
            config = await get_config()
            del_time = config.get("delete_seconds", 300)
            asyncio.create_task(delete_message_later(context.bot, user_id, sent_msg.message_id, del_time))

    # 5. BACK BUTTON TO SERIES SEASONS
    elif data.startswith("back_ser_"):
        item_id = data.replace("back_ser_", "")
        doc = contents_collection.find_one({"_id": ObjectId(item_id)})
        seasons = doc.get('seasons', [])
        kb = [[InlineKeyboardButton(s['title'], callback_data=f"sel_s_{item_id}_{s['sid']}")] for s in seasons]
        await query.edit_message_caption(caption=f"📺 <b>{doc['title']}</b>\n\nSelect a Season:", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)


async def delete_message_later(bot, chat_id: int, message_id: int, seconds: int):
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Auto-delete error: {e}")

# ============================================
# ===       WEBHOOK SERVER (FLASK)         ===
# ============================================
app = Flask(__name__)
bot_app = None
bot_loop = None

@app.route('/')
def home():
    return "Prime Level Bot is Running!", 200

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.is_json:
        update = Update.de_json(request.get_json(), bot_app.bot)
        asyncio.run_coroutine_threadsafe(bot_app.process_update(update), bot_loop)
        return "OK", 200
    return "Bad Request", 400

def run_async(loop, application):
    global bot_loop
    bot_loop = loop
    asyncio.set_event_loop(loop)
    
    if WEBHOOK_URL:
        url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        try:
            httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
            logger.info(f"Webhook set to {url}")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_forever()

# ============================================
# ===       MAIN FUNCTION & HANDLERS       ===
# ============================================
def main():
    global bot_app
    defaults = Defaults(parse_mode=ParseMode.HTML)
    bot_app = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

    cancel_handler = CommandHandler("cancel", cancel_flow)

    # CONVERSATION: ADD MOVIE
    add_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_movie, pattern="^start_add_movie$")],
        states={
            M_GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_title)],
            M_GET_POSTER: [MessageHandler(filters.PHOTO | filters.TEXT, get_movie_poster)],
            M_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_desc)],
            M_GET_QUAL: [
                CallbackQueryHandler(movie_quality_select, pattern="^(mqual_|save_)"),
                MessageHandler(filters.VIDEO | filters.Document.ALL, movie_quality_receive)
            ]
        },
        fallbacks=[cancel_handler, CallbackQueryHandler(cancel_flow, pattern="^admin_menu$")]
    )

    # CONVERSATION: ADD SERIES
    add_series_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_series, pattern="^start_add_series$")],
        states={
            S_GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_series_title)],
            S_GET_POSTER: [MessageHandler(filters.PHOTO | filters.TEXT, get_series_poster)],
            S_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_series_desc)],
            S_GET_SEASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_series_season)],
            S_GET_EPISODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_series_episode)],
            S_GET_QUAL: [
                CallbackQueryHandler(series_quality_select, pattern="^(squal_|save_)"),
                MessageHandler(filters.VIDEO | filters.Document.ALL, series_quality_receive)
            ]
        },
        fallbacks=[cancel_handler, CallbackQueryHandler(cancel_flow, pattern="^admin_menu$")]
    )

    # CONVERSATION: POST GENERATOR
    post_gen_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(post_select_list, pattern="^post_sel_"),
            CallbackQueryHandler(post_set_dest_prompt, pattern="^post_set_dest$")
        ],
        states={
            POST_GET_ITEM: [
                CallbackQueryHandler(post_pick_item, pattern="^post_pick_"),
                CallbackQueryHandler(post_select_list, pattern="^post_sel_")
            ],
            POST_GET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_get_link)],
            POST_PREVIEW: [CallbackQueryHandler(post_handle_controls, pattern="^(post_|admin_menu)")],
            POST_EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_t)],
            POST_EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_d)],
            POST_GET_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_get_dest)],
            SET_DEST_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_save_dest)]
        },
        fallbacks=[cancel_handler, CallbackQueryHandler(cancel_flow, pattern="^admin_menu$")]
    )

    # CONVERSATION: MESSAGE EDITOR
    msg_edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(msg_edit_start, pattern="^msg_edit_")],
        states={MSG_GET_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, msg_edit_save)]},
        fallbacks=[cancel_handler, CallbackQueryHandler(cancel_flow, pattern="^admin_menu$")]
    )

    # CONVERSATION: BROADCAST
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^start_broadcast$")],
        states={BRD_INPUT: [MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast)]},
        fallbacks=[cancel_handler, CallbackQueryHandler(cancel_flow, pattern="^admin_menu$")]
    )

    # BASE COMMANDS
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler(["admin", "menu"], admin_command))
    
    # ADD CONVERSATION HANDLERS
    bot_app.add_handler(add_movie_conv)
    bot_app.add_handler(add_series_conv)
    bot_app.add_handler(post_gen_conv)
    bot_app.add_handler(msg_edit_conv)
    bot_app.add_handler(broadcast_conv)

    # GENERAL CALLBACK HANDLERS
    bot_app.add_handler(CallbackQueryHandler(admin_command, pattern="^admin_menu$"))
    bot_app.add_handler(CallbackQueryHandler(menu_add_content, pattern="^menu_add_content$"))
    bot_app.add_handler(CallbackQueryHandler(menu_manage_content, pattern="^menu_manage_content$"))
    bot_app.add_handler(CallbackQueryHandler(menu_post_gen, pattern="^menu_post_gen$"))
    bot_app.add_handler(CallbackQueryHandler(menu_msg_settings, pattern="^menu_msg_settings$"))
    bot_app.add_handler(CallbackQueryHandler(menu_bot_settings, pattern="^menu_bot_settings$"))
    bot_app.add_handler(CallbackQueryHandler(menu_broadcast_stats, pattern="^menu_broadcast_stats$"))
    bot_app.add_handler(CallbackQueryHandler(menu_gen_link, pattern="^menu_gen_link$"))
    
    # Gen Link pagination & selection
    bot_app.add_handler(CallbackQueryHandler(gen_select_list, pattern="^gen_sel_"))
    bot_app.add_handler(CallbackQueryHandler(gen_pick_item, pattern="^gen_pick_"))
    
    # Manage Content pagination & delete
    bot_app.add_handler(CallbackQueryHandler(manage_del_movie_list, pattern="^manage_del_movie$|^del_m_page_"))
    bot_app.add_handler(CallbackQueryHandler(manage_del_series_list, pattern="^manage_del_series$|^del_s_page_"))
    bot_app.add_handler(CallbackQueryHandler(delete_item_confirm, pattern="^del_item_"))
    
    # Toggle Quotes
    bot_app.add_handler(CallbackQueryHandler(toggle_quotes, pattern="^toggle_quotes$"))
    
    # User Callback Handlers (Files & Series nav)
    bot_app.add_handler(CallbackQueryHandler(user_callback_handler, pattern="^(send_m_|sel_s_|sel_e_|send_s_|back_ser_)"))

    # SERVER THREAD
    loop = asyncio.new_event_loop()
    threading.Thread(target=run_async, args=(loop, bot_app)).start()
    
    port = int(os.environ.get("PORT", 8080))
    serve(app, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
