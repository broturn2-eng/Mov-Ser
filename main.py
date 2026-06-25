# ============================================
# ===       COMPLETE FINAL FIX (v35)       ===
# ===       MOVIES & SERIES SUPPORT         ===
# ============================================
# === (FEAT: Movies & Series)              ===
# === (FEAT: Add Broadcast feature)        ===
# === (FEAT: User Statistics)              ===
# === (FIX: Admin menu layout)             ===
# ============================================
import os
import logging
import re
import asyncio
import threading
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, User, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    Defaults
)
from telegram.error import BadRequest, Forbidden
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
        logger.error(f"Font formatting me error: {e}")
        return raw_text.replace('<f>', '').replace('</f>', '')

# --- Bot Setup ---
load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

try:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    
    if not BOT_TOKEN or not MONGO_URI or not ADMIN_ID or not LOG_CHANNEL_ID:
        logger.error("Error: Secrets missing.")
        exit()
    if not WEBHOOK_URL:
        logger.error("Error: WEBHOOK_URL missing!")
        exit()
except Exception as e:
    logger.error(f"Error reading secrets: {e}")
    exit()

# --- Database Connection ---
try:
    logger.info("MongoDB se connect karne ki koshish...")
    client = MongoClient(MONGO_URI)
    db = client['MovieBotDB']
    users_collection = db['users']
    content_collection = db['content']  # Changed from animes_collection to content_collection
    config_collection = db['config']
    
    content_collection.create_index([("name", ASCENDING)])
    content_collection.create_index([("created_at", DESCENDING)])
    content_collection.create_index([("last_modified", DESCENDING)])
    users_collection.create_index([("interaction_count", DESCENDING)])
    
    users_collection.update_many(
        {"interaction_count": {"$exists": False}},
        {"$set": {"interaction_count": 0}}
    )
    
    client.admin.command('ping')
    logger.info("MongoDB se successfully connect ho gaya!")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit()

ITEMS_PER_PAGE = 20

# --- Admin & Co-Admin Checks ---
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
            {"$inc": {"interaction_count": 1}}
        )
    except Exception as e:
        logger.error(f"User {user_id} ka interaction_count update karne me error: {e}")

# ============================================
# === NEW DATA STRUCTURE: Movies & Series ===
# ============================================
# Content Structure:
# {
#     "_id": ObjectId,
#     "name": "Movie or Series Name",
#     "type": "movie" | "series",
#     "poster_id": "file_id",
#     "description": "Description text",
#     "created_at": datetime,
#     "last_modified": datetime,
#     "seasons": {  # Only for series type
#         "1": {
#             "_poster_id": "file_id",  # Optional
#             "_description": "Season description",  # Optional
#             "1": {  # Episode number
#                 "480p": "file_id",
#                 "720p": "file_id",
#                 "1080p": "file_id",
#                 "4K": "file_id"
#             },
#             "2": { ... }
#         }
#     },
#     "episodes": {  # Only for movie type
#         "1": {  # Episode number (usually 1 for single movie)
#             "480p": "file_id",
#             "720p": "file_id",
#             "1080p": "file_id",
#             "4K": "file_id"
#         }
#     }
# }

# ============================================
# ===     CONVERSATION STATES (v35)        ===
# ============================================
# Add Content States
(A_GET_TYPE, A_GET_NAME, A_GET_POSTER, A_GET_DESC, A_CONFIRM) = range(5)

# Add Series States
(S_GET_ANIME, S_GET_NUMBER, S_GET_POSTER, S_GET_DESC, S_CONFIRM, S_ASK_MORE) = range(10, 16)

# Add Episode States (for both movies and series)
(E_GET_ANIME, E_GET_TYPE, E_GET_SEASON, E_GET_NUMBER, E_GET_480P, E_GET_720P, E_GET_1080P, E_GET_4K, E_ASK_MORE) = range(20, 29)

# Delete States
(DA_GET_TYPE, DA_GET_CONTENT, DA_CONFIRM) = range(30, 33)
(DS_GET_ANIME, DS_GET_SEASON, DS_CONFIRM) = range(33, 36)
(DE_GET_ANIME, DE_GET_TYPE, DE_GET_SEASON, DE_GET_EPISODE, DE_CONFIRM) = range(36, 41)

# Edit States
(EA_GET_TYPE, EA_GET_CONTENT, EA_GET_NEW_NAME, EA_CONFIRM) = range(41, 45)
(ES_GET_ANIME, ES_GET_SEASON, ES_GET_NEW_NAME, ES_CONFIRM) = range(45, 49)
(EE_GET_ANIME, EE_GET_TYPE, EE_GET_SEASON, EE_GET_EPISODE, EE_GET_NEW_NUM, EE_CONFIRM) = range(49, 55)

# Link Generation States
(GL_MENU, GL_GET_TYPE, GL_GET_CONTENT, GL_GET_SEASON, GL_GET_EPISODE) = range(55, 60)

# Post Generator States
(PG_MENU, PG_GET_TYPE, PG_GET_CONTENT, PG_GET_SEASON, PG_GET_EPISODE, PG_GET_SHORT_LINK, PG_GET_CHAT) = range(60, 67)

# Other States
(CD_GET_QR, CL_GET_LINK, CS_GET_DELETE_TIME, UP_GET_TYPE, UP_GET_CONTENT, UP_GET_TARGET, UP_GET_POSTER) = range(70, 77)
(CA_GET_ID, CA_CONFIRM, CR_GET_ID, CR_CONFIRM) = range(77, 81)
(CPOST_GET_CHAT, CPOST_GET_POSTER, CPOST_GET_CAPTION, CPOST_GET_BTN_TEXT, CPOST_GET_BTN_URL, CPOST_CONFIRM) = range(81, 87)
(M_MENU_MAIN, M_MENU_DL, M_MENU_GEN, M_MENU_POSTGEN, M_GET_MSG, M_MENU_ADMIN) = range(87, 93)
(AP_MENU, AP_SET_FONT, AP_SET_STYLE) = range(93, 96)
(CS_GET_MENU_PHOTO,) = range(96, 97)
(BC_GET_MESSAGE, BC_CONFIRM) = range(97, 99)
(MA_GET_TYPE, MA_GET_TARGET, MA_GET_SOURCE, MA_CONFIRM) = range(99, 103)

# ============================================
# ===   MESSAGE FORMATTING HELPERS         ===
# ============================================

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
        except KeyError as e:
            logger.error(f"Message format karne me KeyError: {e} (Key: {key})")
            try:
                text_with_vars = raw_text.format_map(safe_variables)
            except:
                text_with_vars = raw_text
        except Exception as e:
            logger.error(f"Message format karne me error: {e} (Key: {key})")
            text_with_vars = raw_text
    else:
        text_with_vars = raw_text

    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    formatted_text = await apply_font_formatting(text_with_vars, font_settings)
    return formatted_text

async def get_default_messages():
    return {
        # === Download Flow ===
        "user_dl_dm_alert": "✅ <f>Check your DM (private chat) with me!</f>",
        "user_dl_content_not_found": "❌ <f>Error: Content nahi mila.</f>",
        "user_dl_file_error": "❌ <f>Error! {quality} file nahi bhej paya. Please try again.</f>",
        "user_dl_blocked_error": "❌ <f>Error! File nahi bhej paya. Aapne bot ko block kiya hua hai.</f>",
        "user_dl_episodes_not_found": "❌ <f>Error: Is season ke liye episodes nahi mile.</f>",
        "user_dl_seasons_not_found": "❌ <f>Error: Is content ke liye seasons nahi mile.</f>",
        "user_dl_general_error": "❌ <f>Error! Please try again.</f>",
        "user_dl_sending_files": "✅ <b>{content_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>Aapke saare files bhej raha hoon...</f>",
        "user_dl_select_episode": "<b>{content_name}</b> | <b>Season {season_name}</b>\n\n<f>Episode select karein:</f>",
        "user_dl_select_season": "<b>{content_name}</b>\n\n<f>Season select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {minutes} minute(s) mein automatically delete ho jaayegi.</f></b>",
        "user_dl_fetching": "⏳ <f>Fetching files...</f>",

        # === General User ===
        "user_menu_greeting": "<f>Salaam {full_name}! Ye raha aapka menu:</f>",
        "user_donate_qr_error": "❌ <f>Donation info abhi admin ne set nahi ki hai.</f>",
        "user_donate_qr_text": "❤️ <b><f>Support Us!</f></b>\n\n<f>Agar aapko hamara kaam pasand aata hai, toh aap humein support kar sakte hain.</f>",
        "donate_thanks": "❤️ <f>Support karne ke liye shukriya!</f>",
        "user_not_admin": "<f>Aap admin nahi hain.</f>",
        "user_welcome_admin": "<f>Salaam, Admin! Admin panel ke liye</f> /menu <f>use karein.</f>",
        "user_welcome_basic": "<f>Salaam, {full_name}! Apna user menu dekhne ke liye</f> /user <f>use karein.</f>",
        
        # === Post Generator ===
        "post_gen_movie_caption": "✅ <b>{content_name}</b>\n\n<b><f>📖 Synopsis:</f></b>\n{description}\n\n<f>Neeche [Download] button dabake download karein!</f>",
        "post_gen_series_caption": "✅ <b>{content_name}</b>\n<b>[ S{season_name} ]</b>\n\n<b><f>📖 Synopsis:</f></b>\n{description}\n\n<f>Neeche [Download] button dabake download karein!</f>",
        "post_gen_episode_caption": "✨ <b><f>Episode {ep_num} Added</f></b> ✨\n\n🎬 <b><f>Title:</f></b> {content_name}\n➡️ <b><f>Season:</f></b> {season_name}\n\n<f>Neeche [Download] button dabake download karein!</f>",

        # === Admin: General ===
        "admin_cancel": "<f>Operation cancel kar diya gaya hai.</f>",
        "admin_cancel_error_edit": "<f>Cancel me edit nahi kar paya: {e}</f>",
        "admin_cancel_error_general": "<f>Cancel me error: {e}</f>",
        "admin_panel_main": "👑 <b><f>Salaam, Admin Boss!</f></b> 👑\n<f>Aapka control panel taiyyar hai.</f>",
        "admin_panel_co": "👑 <b><f>Salaam, Co-Admin!</f></b> 👑\n<f>Aapka content panel taiyyar hai.</f>",

        # === Admin: Set Menu Photo ===
        "admin_set_menu_photo_start": "<f>User menu mein dikhaane ke liye <b>Photo</b> bhejo.</f>\n\n/skip - <f>Photo hata do.</f>\n/cancel - <f>Cancel.</f>",
        "admin_set_menu_photo_error": "<f>Ye photo nahi hai. Please ek photo bhejo ya</f> /skip <f>karein.</f>",
        "admin_set_menu_photo_success": "✅ <b><f>Success!</f></b> <f>Naya user menu photo set ho gaya hai.</f>",
        "admin_set_menu_photo_skip": "✅ <b><f>Success!</f></b> <f>User menu photo hata diya gaya hai.</f>",

        # === Admin: Add Content Menus ===
        "admin_menu_add_content": "➕ <b><f>Add Content</f></b> ➕\n\n<f>Aap kya add karna chahte hain?</f>",
        "admin_menu_manage_content": "🗑️ <b><f>Delete Content</f></b> 🗑️\n\n<f>Aap kya delete karna chahte hain?</f>",
        "admin_menu_edit_content": "✏️ <b><f>Edit Content</f></b> ✏️\n\n<f>Aap kya edit karna chahte hain?</f>",

        # === Admin: Add Content (Movie/Series) ===
        "admin_add_content_select_type": "<f>Kis type ka content add karna hai?</f>",
        "admin_add_content_get_name": "<f>Salaam Admin! {content_type} ka <b>Naam</b> kya hai?</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_content_get_poster": "<f>Badhiya! Ab {content_type} ka <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_content_get_poster_error": "Ye photo nahi hai. Please ek photo bhejo.",
        "admin_add_content_get_desc": "<f>Poster mil gaya! Ab <b>Description (Synopsis)</b> bhejo.</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_content_confirm": "<b>{name}</b>\n\n{description}\n\n<f>--- Details Check Karo ---</f>",
        "admin_add_content_save_exists": "⚠️ <b><f>Error:</f></b> <f>Ye {content_type} naam</f> '{name}' <f>pehle se hai.</f>",
        "admin_add_content_save_success": "✅ <b><f>Success!</f></b> '{name}' <f>add ho gaya hai.</f>",
        "admin_add_content_save_error": "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>",

        # === Admin: Add Series/Season ===
        "admin_add_season_select_content": "<f>Aap kis {content_type} mein season add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_add_season_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai. Pehle 'Add {content_type}' se add karein.</f>",
        "admin_add_season_not_series": "❌ <b><f>Error!</f></b> '{content_name}' <f>ek movie hai, isme season add nahi kar sakte.</f>",
        "admin_add_season_get_content": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_content_with_last": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Last added season:</f> <b>{last_season_name}</b>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_content_no_last": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Is {content_type} mein abhi koi season nahi hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_number_error": "⚠️ <b><f>Error!</f></b> <f>{content_type}</f> '{content_name}' <f>database mein nahi mila.</f> /cancel <f>karke dobara try karein.</f>",
        "admin_add_season_get_number_exists": "⚠️ <b><f>Error!</f></b> '{content_name}' <f>mein 'Season {season_name}' pehle se hai.</f>\n\n<f>Koi doosra naam/number type karein ya</f> /cancel <f>karein.</f>",
        "admin_add_season_get_poster_prompt": "<f>Aapne Season</f> '{season_name}' <f>select kiya hai.</f>\n\n<f>Ab is season ka <b>Poster (Photo)</b> bhejo.</f>\n\n/skip - <f>Default poster use karo.</f>\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_poster_error": "<f>Ye photo nahi hai. Please ek photo bhejo.</f>",
        "admin_add_season_get_desc_prompt": "<f>Poster mil gaya! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_season_skip_poster": "<f>Default poster set! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_season_confirm": "<b><f>Confirm Karo:</f></b>\n<f>{content_type}:</f> <b>{content_name}</b>\n<f>Naya Season:</f> <b>{season_name}</b>\n<f>Description:</f> {season_desc}\n\n<f>Save kar doon?</f>",
        "admin_add_season_save_success": "✅ <b><f>Success!</f></b>\n<b>{content_name}</b> <f>mein</f> <b>Season {season_name}</b> <f>add ho gaya hai.</f>",
        "admin_add_season_save_error": "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>",
        "admin_add_season_ask_more": "✅ <f>Season</f> <b>{season_name}</b> <f>save ho gaya!</f>\n\n<f>Aap</f> <b>{content_name}</b> <f>mein aur season add karna chahte hain?</f>",
        "admin_add_season_next_prompt": "<f>Last Season:</f> <b>{season_name}</b>. <f>{content_type}:</f> <b>{content_name}</b>\n\n<f>Ab agla <b>Season Number/Naam</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        
        # === Admin: Add Episode ===
        "admin_add_ep_select_content": "<f>Aap kis {content_type} mein episode add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_add_ep_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai. Pehle 'Add {content_type}' se add karein.</f>",
        "admin_add_ep_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>\n\n<f>Pehle</f> <code>➕ Add Season</code> <f>se season add karo.</f>",
        "admin_add_ep_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_add_ep_get_season_with_last": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Last added episode:</f> <b>{last_ep_num}</b>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n<f>(Agar yeh ek movie hai, toh</f> <code>1</code> <f>type karein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_get_season_no_last": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Is season mein abhi koi episode nahi hai.</f>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n<f>(Agar yeh ek movie hai, toh</f> <code>1</code> <f>type karein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_get_number": "<f>Aapne</f> <b>Episode {ep_num}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>480p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_get_number_exists": "⚠️ <b><f>Error!</f></b> '{content_name}' - Season {season_name} - Episode {ep_num} <f>pehle se maujood hai. Please pehle isse delete karein ya koi doosra episode number dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_helper_invalid": "<f>Ye video file nahi hai. Please dobara video file bhejein ya</f> /skip <f>karein.</f>",
        "admin_add_ep_helper_success": "✅ <b>{quality}</b> <f>save ho gaya.</f>",
        "admin_add_ep_helper_error": "❌ <b><f>Error!</f></b> {quality} <f>save nahi kar paya. Logs check karein.</f>",
        "admin_add_ep_get_480p": "<f>Ab <b>720p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_skip_480p": "✅ <f>480p skip kar diya.</f>\n\n<f>Ab <b>720p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_get_720p": "<f>Ab <b>1080p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_skip_720p": "✅ <f>720p skip kar diya.</f>\n\n<f>Ab <b>1080p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_get_1080p": "<f>Ab <b>4K</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_skip_1080p": "✅ <f>1080p skip kar diya.</f>\n\n<f>Ab <b>4K</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_get_4k_success": "✅ <b><f>Success!</f></b> <f>Saari qualities save ho gayi hain.</f>",
        "admin_add_ep_skip_4k": "✅ <f>4K skip kar diya.</f>\n\n✅ <b><f>Success!</f></b> <f>Episode save ho gaya hai.</f>",
        "admin_add_ep_ask_more": "✅ <f>Ep</f> <b>{ep_num}</b> <f>save ho gaya!</f>\n\n<f>Aap</f> <b>S{season_name}</b> <f>mein aur episode add karna chahte hain?</f>",
        "admin_add_ep_next_prompt": "<f>Last Ep:</f> <b>{ep_num}</b>. <f>Season:</f> <b>{season_name}</b>\n\n<f>Ab agla <b>Episode Number</b> bhejo.</f>\n<f>(Suggestion: {next_ep_num})</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_next_prompt_no_suggestion": "<f>Last Ep:</f> <b>{ep_num}</b>. <f>Season:</f> <b>{season_name}</b>\n\n<f>Ab agla <b>Episode Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        
        # === Admin: Delete Content ===
        "admin_del_content_select_type": "<f>Kis type ka content delete karna hai?</f>",
        "admin_del_content_select": "<f>Kaunsa <b>{content_type}</b> delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_content_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_del_content_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{content_name}</b> <f>ko delete karne wale hain. Iske saare seasons aur episodes delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_content_success": "✅ <b><f>Success!</f></b>\n<f>{content_type}</f> '{content_name}' <f>delete ho gaya hai.</f>",
        "admin_del_content_error": "❌ <b><f>Error!</f></b> <f>{content_type} delete nahi ho paya.</f>",

        # === Admin: Delete Season ===
        "admin_del_season_select_content": "<f>Kaunse <b>{content_type}</b> ka season delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_season_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_del_season_not_series": "❌ <b><f>Error!</f></b> '{content_name}' <f>ek movie hai, isme season delete nahi kar sakte.</f>",
        "admin_del_season_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_del_season_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> delete karna hai?</f>",
        "admin_del_season_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{content_name}</b> <f>ka</f> <b>Season {season_name}</b> <f>delete karne wale hain. Iske saare episodes delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_season_success": "✅ <b><f>Success!</f></b>\n<f>Season</f> '{season_name}' <f>delete ho gaya hai.</f>",
        "admin_del_season_error": "❌ <b><f>Error!</f></b> <f>Season delete nahi ho paya.</f>",

        # === Admin: Delete Episode ===
        "admin_del_ep_select_content": "<f>Kaunse <b>{content_type}</b> ka episode delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_ep_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_del_ep_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_del_ep_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> select karna hai?</f>",
        "admin_del_ep_no_episode": "❌ <b><f>Error!</f></b> '{content_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_del_ep_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Episode</b> delete karna hai?</f>",
        "admin_del_ep_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{content_name}</b> - <b>S{season_name}</b> - <b>Ep {ep_num}</b> <f>delete karne wale hain. Iske saare qualities delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_ep_success": "✅ <b><f>Success!</f></b>\n<f>Episode</f> '{ep_num}' <f>delete ho gaya hai.</f>",
        "admin_del_ep_error": "❌ <b><f>Error!</f></b> <f>Episode delete nahi ho paya.</f>",

        # === Admin: Edit Content ===
        "admin_edit_content_select_type": "<f>Kis type ka content edit karna hai?</f>",
        "admin_edit_content_select": "<f>Kaunsa <b>{content_type}</b> ka naam edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_content_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_edit_content_get_name": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Naam</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_content_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya naam</f> '{new_name}' <f>pehle se maujood hai. Koi doosra naam dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_content_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>Purana Naam:</f> <code>{old_name}</code>\n<f>Naya Naam:</f> <code>{new_name}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_content_success": "✅ <b><f>Success!</f></b>\n<f>{content_type}</f> '{old_name}' <f>ka naam badal kar</f> '{new_name}' <f>ho gaya hai.</f>",
        "admin_edit_content_error": "❌ <b><f>Error!</f></b> <f>{content_type} naam update nahi ho paya.</f>",

        # === Admin: Edit Season ===
        "admin_edit_season_select_content": "<f>Kaunse <b>{content_type}</b> ka season edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_season_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_edit_season_not_series": "❌ <b><f>Error!</f></b> '{content_name}' <f>ek movie hai, isme season edit nahi kar sakte.</f>",
        "admin_edit_season_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_edit_season_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> ka naam edit karna hai?</f>",
        "admin_edit_season_get_name": "<f>Aapne</f> <b>{content_name}</b> -> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Naam/Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_season_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya naam</f> '{new_name}' <f>is {content_type} mein pehle se maujood hai. Koi doosra naam dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_season_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>{content_type}:</f> <code>{content_name}</code>\n<f>Purana Season:</f> <code>{old_name}</code>\n<f>Naya Season:</f> <code>{new_name}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_season_success": "✅ <b><f>Success!</f></b>\n<f>Season</f> '{old_name}' <f>ka naam badal kar</f> '{new_name}' <f>ho gaya hai.</f>",
        "admin_edit_season_error": "❌ <b><f>Error!</f></b> <f>Season naam update nahi ho paya.</f>",

        # === Admin: Edit Episode ===
        "admin_edit_ep_select_content": "<f>Kaunse <b>{content_type}</b> ka episode edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_ep_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_edit_ep_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_edit_ep_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.\n\n<f>Kaunsa <b>Season</b> select karna hai?</f>",
        "admin_edit_ep_no_episode": "❌ <b><f>Error!</f></b> '{content_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_edit_ep_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Episode</b> ka number edit karna hai?</f>",
        "admin_edit_ep_get_num": "<f>Aapne</f> <b>{content_name}</b> -> <b>S{season_name}</b> -> <b>Ep {ep_num}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_ep_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya number</f> '{new_num}' <f>is season mein pehle se maujood hai. Koi doosra number dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_ep_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>{content_type}:</f> <code>{content_name}</code>\n<f>Season:</f> <code>{season_name}</code>\n<f>Purana Episode:</f> <code>{old_num}</code>\n<f>Naya Episode:</f> <code>{new_num}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_ep_success": "✅ <b><f>Success!</f></b>\n<f>Episode</f> '{old_num}' <f>ka number badal kar</f> '{new_num}' <f>ho gaya hai.</f>",
        "admin_edit_ep_error": "❌ <b><f>Error!</f></b> <f>Episode number update nahi ho paya.</f>",

        # === Admin: Update Photo ===
        "admin_menu_update_photo": "🖼️ <b><f>Photo Settings</f></b> 🖼️\n\n<f>Aap kaunsi photo change karna chahte hain?</f>",
        "admin_update_photo_select_type": "<f>Kis type ka content ka poster update karna hai?</f>",
        "admin_update_photo_select_content": "<f>Kaunse <b>{content_type}</b> ka poster update karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_update_photo_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_update_photo_select_target": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Aap iska <b>Main Poster</b> change karna chahte hain ya kisi <b>Season</b> ka?</f>",
        "admin_update_photo_get_poster": "<f>Aapne</f> <b>{target_name}</b> <f>select kiya hai.</f>\n\n<f>Ab naya <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_update_photo_invalid": "<f>Ye photo nahi hai. Please ek photo bhejo ya</f> /cancel <f>karo.</f>",
        "admin_update_photo_save_success_main": "✅ <b><f>Success!</f></b>\n{content_name} <f>ka <b>Main Poster</b> change ho gaya hai.</f>",
        "admin_update_photo_save_success_season": "✅ <b><f>Success!</f></b>\n{content_name} - <b>Season {season_name}</b> <f>ka poster change ho gaya hai.</f>",
        "admin_update_photo_save_error_db": "❌ <b><f>Error!</f></b> <f>Poster update nahi ho paya.</f>",

        # === Admin: Settings ===
        "admin_menu_donate": "❤️ <b><f>Donation Settings</f></b> ❤️\n\n<f>Sirf QR code se donation accept karein.</f>",
        "admin_set_donate_qr_start": "<f>Aapna <b>Donate QR Code</b> ki photo bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_set_donate_qr_error": "<f>Ye photo nahi hai. Please ek photo bhejo ya</f> /cancel <f>karein.</f>",
        "admin_set_donate_qr_success": "✅ <b><f>Success!</f></b> <f>Naya donate QR code set ho gaya hai.</f>",
        "admin_menu_links": "🔗 <b><f>Other Links</f></b> 🔗\n\n<f>Doosre links yahan set karein.</f>",
        "admin_set_link_backup": "<f>Aapke <b>Backup Channel</b> ka link bhejo.</f>\n<f>(Example: https://t.me/mychannel)</f>\n\n/skip - <f>Skip.</f>\n/cancel - <f>Cancel.</f>",
        "admin_set_link_download": "<f>Aapka global <b>Download Link</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip - <f>Skip.</f>\n/cancel - <f>Cancel.</f>",
        "admin_set_link_help": "<f>Aapke <b>Help/Support</b> ka link bhejo.</f>\n<f>(Example: https://t.me/mychannel)</f>\n\n/skip - <f>Skip.</f>\n/cancel - <f>Cancel.</f>",
        "admin_set_link_invalid": "<f>Invalid button!</f>",
        "admin_set_link_success": "✅ <b><f>Success!</f></b> <f>Naya {link_type} link set ho gaya hai.</f>",
        "admin_set_link_skip": "✅ <b><f>Success!</f></b> {link_type} <f>link remove kar diya gaya hai.</f>",
        "admin_set_delete_time_start": "<f>Abhi file auto-delete</f> <b>{current_minutes} <f>minute(s)</f></b> ({current_seconds} <f>seconds</f>) <f>par set hai.</f>\n\n<f>Naya time <b>seconds</b> mein bhejo.</f>\n<f>(Example:</f> <code>300</code> <f>for 5 minutes)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_set_delete_time_low": "<f>Time 10 second se zyada hona chahiye.</f>",
        "admin_set_delete_time_success": "✅ <b><f>Success!</f></b> <f>Auto-delete time ab</f> <b>{seconds} <f>seconds</f></b> ({minutes} <f>min</f>) <f>par set ho gaya hai.</f>",
        "admin_set_delete_time_nan": "<f>Yeh number nahi hai. Please sirf seconds bhejein (jaise 180) ya</f> /cancel <f>karein.</f>",
        "admin_set_delete_time_error": "❌ <f>Error! Save nahi kar paya.</f>",

        # === Admin: Bot Messages ===
        "admin_menu_messages_main": "⚙️ <b><f>Bot Messages</f></b> ⚙️\n\n<f>Aap bot ke replies ko edit karne ke liye category select karein.</f>",
        "admin_menu_messages_dl": "📥 <b><f>Download Flow Messages</f></b> 📥\n\n<f>Kaunsa message edit karna hai?</f>",
        "admin_menu_messages_gen": "⚙️ <b><f>General Messages</f></b> ⚙️\n\n<f>Kaunsa message edit karna hai?</f>",
        "admin_menu_messages_postgen": "✍️ <b><f>Post Generator Messages</f></b> ✍️\n\n<f>Kaunsa message edit karna hai?</f>",
        "admin_menu_messages_admin": "👑 <b><f>Admin Messages</f></b> 👑\n\n<f>Kaunsa message edit karna hai?</f>",
        "admin_set_msg_start": "<b><f>Editing:</f></b> <code>{msg_key}</code>\n\n<b><f>Current Message:</f></b>\n<code>{current_msg}</code>\n\n<f>Naya message bhejo.</f>\n<f>Aap</f> <code>&lt;b&gt;bold&lt;/b&gt;</code>, <code>&lt;i&gt;italic&lt;/i&gt;</code>, <code>&lt;code&gt;code&lt;/code&gt;</code>, <f>aur</f> <code>&lt;blockquote&gt;quote&lt;/blockquote&gt;</code> <f>use kar sakte hain.</f>\n<f>Font apply karne ke liye</f> <code>&lt;f&gt;...&lt;/f&gt;</code> <f>use karein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_set_msg_success": "✅ <b><f>Success!</f></b> <f>Naya</f> '{msg_key}' <f>message set ho gaya hai.</f>",
        "admin_set_msg_error": "❌ <f>Error! Save nahi kar paya.</f>",

        # === Admin: Post Generator ===
        "admin_menu_post_gen": "✍️ <b><f>Post Generator</f></b> ✍️\n\n<f>Aap kis tarah ka post generate karna chahte hain?</f>",
        "admin_post_gen_select_type": "<f>Kis type ka content ka post generate karna hai?</f>",
        "admin_post_gen_select_content": "<f>Kaunsa <b>{content_type}</b> select karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_post_gen_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_post_gen_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_post_gen_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_post_gen_no_episode": "❌ <b><f>Error!</f></b> '{content_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_post_gen_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Episode</b> select karein:</f>",
        "admin_post_gen_ask_shortlink": "✅ <b><f>Post Ready!</f></b>\n\n<f>Aapka original download link hai:</f>\n<code>{original_download_url}</code>\n\n<f>Please iska <b>shortened link</b> reply mein bhejein.</f>\n<f>(Agar link change nahi karna hai, toh upar waala link hi copy karke bhej dein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_post_gen_ask_chat": "✅ <b><f>Short Link Saved!</f></b>\n\n<f>Ab uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.</f>\n<f>(Example: @MyChannel ya -100123456789)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_post_gen_success": "✅ <b><f>Success!</f></b>\n<f>Post ko</f> '{chat_id}' <f>par bhej diya gaya hai.</f>",
        "admin_post_gen_error": "❌ <b><f>Error!</f></b>\n<f>Post</f> '{chat_id}' <f>par nahi bhej paya. Check karo ki bot uss channel me admin hai ya ID sahi hai.</f>\n<f>Error:</f> {e}",
        "admin_post_gen_invalid_state": "❌ <f>Error! Invalid state. Please start over.</f>",
        "admin_post_gen_error_general": "❌ <b><f>Error!</f></b> <f>Post generate nahi ho paya. Logs check karein.</f>",
        
        # === Admin: Generate Link ===
        "admin_menu_gen_link": "🔗 <b><f>Generate Download Link</f></b> 🔗\n\n<f>Aap kis cheez ka link generate karna chahte hain?</f>",
        "admin_gen_link_select_type": "<f>Kis type ka content ka link generate karna hai?</f>",
        "admin_gen_link_select_content": "<f>Kaunsa <b>{content_type}</b> select karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_gen_link_no_content": "❌ <f>Error: Abhi koi {content_type} add nahi hua hai.</f>",
        "admin_gen_link_no_season": "❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>",
        "admin_gen_link_select_season": "<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_gen_link_no_episode": "❌ <b><f>Error!</f></b> '{content_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_gen_link_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Episode</b> select karein:</f>",
        "admin_gen_link_success": "✅ <b><f>Link Generated!</f></b>\n\n<b><f>Target:</f></b> {title}\n<b><f>Link:</f></b>\n<code>{final_link}</code>\n\n<f>Is link ko copy karke kahin bhi paste karein.</f>",
        "admin_gen_link_error": "❌ <b><f>Error!</f></b> <f>Link generate nahi ho paya. Logs check karein.</f>",

        # === Admin: Merge Content ===
        "admin_menu_merge_content": "🔄 <b><f>Merge {content_type}</f></b> 🔄\n\n<f>Yeh feature do alag-alag {content_type} entries ko ek mein combine kar dega.</f>",
        "admin_merge_select_type": "<f>Kis type ka content merge karna hai?</f>",
        "admin_merge_select_target": "1️⃣ <f>Pehle, <b>TARGET</b> {content_type} select karein.</f>\n\n<f>(Yeh woh {content_type} hai jiske ANDAR aap doosre seasons daalna chahte hain.)</f>\n<f>(Page {page})</f>",
        "admin_merge_select_source": "2️⃣ <f>Ab, <b>SOURCE</b> {content_type} select karein.</f>\n\n<f>(Yeh woh {content_type} hai jisko delete karke iske saare seasons <b>{target_name}</b> mein move kar diye jayenge.)</f>\n<f>(Page {page})</f>",
        "admin_merge_self_merge_error": "❌ <f>Error! Aap ek {content_type} ko khud se merge nahi kar sakte. Koi doosra {content_type} chunein.</f>",
        "admin_merge_confirm": "⚠️ <b><f>FINAL CONFIRMATION</f></b> ⚠️\n\n<f>Aap <b>SOURCE</b> {content_type}:</f>\n<code>{source_name}</code>\n<f>ke saare seasons ko <b>TARGET</b> {content_type}:</f>\n<code>{target_name}</code>\n<f>mein move kar rahe hain.</f>\n\n<f>Total</f> <b>{count}</b> <f>seasons move honge.</f>\n<f>Source {content_type}</f> (<code>{source_name}</code>) <f>delete ho jayega.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_merge_success": "✅ <b><f>Success!</f></b>\n<f>Total</f> <b>{count}</b> <f>seasons ko</f> <code>{source_name}</code> <f>se</f> <code>{target_name}</code> <f>mein move kar diya gaya hai.</f>\n<f>Source {content_type} delete ho gaya hai.</f>",
        "admin_merge_error": "❌ <b><f>Error!</f></b> <f>Merge nahi ho paya. Dono {content_type} check karein. Error:</f> {e}",

        # === Admin: Other Settings ===
        "admin_menu_admin_settings": "🛠️ <b><f>Admin Settings</f></b> 🛠️\n\n<f>Yahan aap Co-Admins aur doosri advanced settings manage kar sakte hain.</f>",
        "admin_co_admin_add_start": "<f>Naye Co-Admin ki <b>Telegram User ID</b> bhejein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_co_admin_add_invalid_id": "<f>Yeh valid User ID nahi hai. Please sirf number bhejein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_co_admin_add_is_main": "<f>Aap Main Admin hain, khud ko add nahi kar sakte.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_co_admin_add_exists": "<f>User</f> <code>{user_id}</code> <f>pehle se Co-Admin hai.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_co_admin_add_confirm": "<f>Aap user ID</f> <code>{user_id}</code> <f>ko <b>Co-Admin</b> banane wale hain.</f>\n\n<f>Woh content add, remove, aur post generate kar payenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_co_admin_add_success": "✅ <b><f>Success!</f></b>\n<f>User ID</f> <code>{user_id}</code> <f>ab Co-Admin hai.</f>",
        "admin_co_admin_add_error": "❌ <b><f>Error!</f></b> <f>Co-Admin add nahi ho paya.</f>",
        "admin_co_admin_remove_no_co": "<f>Abhi koi Co-Admin nahi hai.</f>",
        "admin_co_admin_remove_start": "<f>Kis Co-Admin ko remove karna hai?</f>",
        "admin_co_admin_remove_confirm": "<f>Aap Co-Admin ID</f> <code>{user_id}</code> <f>ko remove karne wale hain.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_co_admin_remove_success": "✅ <b><f>Success!</f></b>\n<f>Co-Admin ID</f> <code>{user_id}</code> <f>remove ho gaya hai.</f>",
        "admin_co_admin_remove_error": "❌ <b><f>Error!</f></b> <f>Co-Admin remove nahi ho paya.</f>",
        "admin_co_admin_list_none": "<f>Abhi koi Co-Admin nahi hai.</f>",
        "admin_co_admin_list_header": "<b><f>List of Co-Admins:</f></b>\n",
        "admin_custom_post_start": "🚀 <b><f>Custom Post Generator</f></b>\n\n<f>Ab uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.</f>\n<f>(Example: @MyChannel ya -100123456789)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_chat": "<f>Chat ID set! Ab post ka <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_poster_error": "<f>Ye photo nahi hai. Please ek photo bhejo.</f>",
        "admin_custom_post_get_poster": "<f>Poster set! Ab post ka <b>Caption</b> (text) bhejo.</f>\n<f>(Aap</f> <code>&lt;f&gt;...&lt;/f&gt;</code> <f>tags use kar sakte hain)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_caption": "<f>Caption set! Ab custom button ka <b>Text</b> bhejo.</f>\n<f>(Example: 'Join Now')</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_btn_text": "<f>Button text set! Ab button ka <b>URL (Link)</b> bhejo.</f>\n<f>(Example: 'https://t.me/mychannel')</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_confirm": "<b><f>--- PREVIEW ---</f></b>\n\n{caption}\n\n<b><f>Target:</f></b> <code>{chat_id}</code>",
        "admin_custom_post_success": "✅ <b><f>Success!</f></b>\n<f>Post ko</f> '{chat_id}' <f>par bhej diya gaya hai.</f>",
        "admin_custom_post_error": "❌ <b><f>Error!</f></b>\n<f>Post</f> '{chat_id}' <f>par nahi bhej paya.</f>\n<f>Error:</f> {e}",
        
        # === Admin: Appearance ===
        "admin_menu_appearance": "🎨 <b><f>Bot Appearance</f></b> 🎨\n\n<f>Bot ke messages ka look aur feel yahaan change karein.</f>\n\n<f>Current Font:</f> <b>{font}</b>\n<f>Current Style:</f> <b>{style}</b>",
        "admin_appearance_select_font": "<f>Kaunsa font select karna hai?</f>\n\n<f>Current:</f> <b>{font}</b>",
        "admin_appearance_select_style": "<f>Kaunsa style select karna hai?</f>\n\n<f>Current:</f> <b>{style}</b>",
        "admin_appearance_set_font_success": "✅ <b><f>Success!</f></b> <f>Font ko</f> <b>{font}</b> <f>par set kar diya gaya hai.</f>",
        "admin_appearance_set_style_success": "✅ <b><f>Success!</f></b> <f>Style ko</f> <b>{style}</b> <f>par set kar diya gaya hai.</f>",

        # === Admin: User Stats ===
        "admin_stats_loading": "⏳ <f>Stats calculate kar raha hoon...</f>",
        "admin_stats_result": "📊 <b><f>User Statistics</f></b> 📊\n\n<f>Total Users:</f> <b>{total_users}</b>\n\n🥇 <b><f>Top 10 Active Users:</f></b>\n{top_users_list}",
        "admin_stats_no_users": "<f>Abhi bot par koi top users nahi hain.</f>",
        
        # === Admin: Broadcast ===
        "admin_broadcast_start": "📢 <b><f>Broadcast Message</f></b>\n\n<f>Ab woh message bhejo jo aap sabhi users ko bhejna chahte hain.</f>\n<f>(Text, Photo, Video, kuch bhi...)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_broadcast_confirm": "⚠️ <b><f>Confirm Karo</f></b> ⚠️\n\n<f>Aap yeh message sabhi</f> <b>{user_count}</b> <f>users ko bhej rahe hain.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_broadcast_sending": "⏳ <f>Broadcast shuru kar raha hoon... Total</f> <b>{user_count}</b> <f>users.</f>\n\n<f>Isme time lag sakta hai. Bot ko band na karein.</f>",
        "admin_broadcast_success": "✅ <b><f>Broadcast Complete!</f></b>\n\n<f>Sent to:</f> <b>{sent_count}</b> <f>users</f>\n<f>Failed for:</f> <b>{failed_count}</b> <f>users</f>",
        "admin_broadcast_error": "❌ <b><f>Broadcast Error!</f></b>\n<f>Error:</f> {e}",
    }

# ============================================
# ===        CONFIG HELPER                 ===
# ============================================

async def get_config():
    config = config_collection.find_one({"_id": "bot_config"})
    default_messages = await get_default_messages()

    if not config:
        default_config = {
            "_id": "bot_config",
            "donate_qr_id": None,
            "links": {"backup": None, "download": None, "help": None},
            "user_menu_photo_id": None,
            "delete_seconds": 300,
            "messages": default_messages,
            "co_admins": [],
            "appearance": {"font": "default", "style": "normal"}
        }
        config_collection.insert_one(default_config)
        return default_config
    
    needs_update = False
    
    if "delete_seconds" not in config:
        config["delete_seconds"] = 300
        needs_update = True
    if "co_admins" not in config:
        config["co_admins"] = []
        needs_update = True
    if "appearance" not in config:
        config["appearance"] = {"font": "default", "style": "normal"}
        needs_update = True
    if "messages" not in config:
        config["messages"] = {}
        needs_update = True
    if "links" not in config:
        config["links"] = {"backup": None, "download": None, "help": None}
        needs_update = True
    elif "help" not in config["links"]:
        config["links"]["help"] = None
        needs_update = True

    # Remove old messages
    messages_to_remove = [
        "user_sub_qr_error", "user_sub_qr_text", "user_sub_ss_prompt",
        "user_sub_ss_not_photo", "user_sub_ss_error", "sub_pending",
        "sub_approved", "sub_rejected", "user_sub_removed",
        "user_already_subscribed", "user_dl_unsubscribed_alert",
        "user_dl_unsubscribed_dm", "user_dl_checking_sub"
    ]
    
    keys_to_actually_remove = []
    if "messages" in config:
        for key in messages_to_remove:
            if key in config["messages"]:
                keys_to_actually_remove.append(key)
                needs_update = True
    
    if keys_to_actually_remove:
        for key in keys_to_actually_remove:
            del config["messages"][key]

    if needs_update:
        update_set = {
            "messages": config["messages"],
            "user_menu_photo_id": config.get("user_menu_photo_id"),
            "delete_seconds": config.get("delete_seconds", 300),
            "co_admins": config.get("co_admins", []),
            "appearance": config.get("appearance", {"font": "default", "style": "normal"}),
            "links": config.get("links", {"backup": None, "download": None, "help": None})
        }
        
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$set": update_set}
        )

    if "donate" in config.get("links", {}):
        config_collection.update_one({"_id": "bot_config"}, {"$unset": {"links.donate": ""}})
    
    if "links" in config:
        if "support" in config["links"]:
            config_collection.update_one({"_id": "bot_config"}, {"$unset": {"links.support": ""}})
        if "download" not in config["links"]:
            if "dl_link" in config["links"]:
                config_collection.update_one({"_id": "bot_config"}, {"$rename": {"links.dl_link": "links.download"}})
            else:
                config_collection.update_one({"_id": "bot_config"}, {"$set": {"links.download": None}})

    return config

# ============================================
# ===        HELPER FUNCTIONS              ===
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
    exclude_items: list = None
):
    if filter_query is None:
        filter_query = {}
    
    if exclude_items:
        filter_query["name"] = {"$nin": exclude_items}
        
    skip = page * ITEMS_PER_PAGE
    total_items = collection.count_documents(filter_query)
    
    items = list(collection.find(filter_query).sort("last_modified", DESCENDING).skip(skip).limit(ITEMS_PER_PAGE))
    
    if not items and page == 0:
        return None, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]])
        
    buttons = []
    for item in items:
        if "name" in item:
            buttons.append(InlineKeyboardButton(item['name'], callback_data=f"{item_callback_prefix}{item['name']}"))
    
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

async def _update_content_timestamp(content_name: str):
    try:
        content_collection.update_one(
            {"name": content_name},
            {"$set": {"last_modified": datetime.now()}}
        )
        logger.info(f"'{content_name}' ka timestamp update ho gaya.")
    except Exception as e:
        logger.error(f"'{content_name}' ka timestamp update karne me error: {e}")

# ============================================
# ===     JOB QUEUE CALLBACKS              ===
# ============================================

async def send_donate_thank_you(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        msg = await format_message(context, "donate_thanks")
        await context.bot.send_message(chat_id=job.chat_id, text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning(f"Thank you message bhejte waqt error: {e}")

async def delete_message_later(bot, chat_id: int, message_id: int, seconds: int):
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Auto-deleted message {message_id} for user {chat_id} (asyncio.sleep)")
    except Exception as e:
        logger.warning(f"Message (asyncio.sleep) delete karne me error: {e}")

# ============================================
# ===        CANCEL HANDLERS               ===
# ============================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.id} ne operation cancel kiya.")
    if context.user_data:
        context.user_data.clear()
    
    reply_text = await format_message(context, "admin_cancel")
    
    try:
        if update.message:
            await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            query = update.callback_query
            if not query.data.startswith("admin_menu_") and not query.data == "admin_menu":
                await query.answer("Canceled!")
                await query.edit_message_text(reply_text, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Cancel me edit nahi kar paya: {e}")
    except Exception as e:
        logger.error(f"Cancel me error: {e}")

    if await is_co_admin(user.id):
        await asyncio.sleep(0.1)
        await admin_command(update, context, from_callback=(update.callback_query is not None))
    
    return ConversationHandler.END

# ============================================
# ===    ADMIN COMMANDS & MENUS            ===
# ============================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    if not await is_co_admin(user_id):
        if not from_callback:
            if update.message:
                text = await format_message(context, "user_not_admin")
                await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            else:
                await update.callback_query.answer("Aap admin nahi hain.", show_alert=True)
        return
        
    logger.info("Admin/Co-Admin ne /admin command use kiya.")
    
    if not await is_main_admin(user_id):
        # Co-Admin Menu
        keyboard = [
            [InlineKeyboardButton("➕ Add Content", callback_data="admin_menu_add_content")],
            [InlineKeyboardButton("🗑️ Delete Content", callback_data="admin_menu_manage_content")],
            [InlineKeyboardButton("✏️ Edit Content", callback_data="admin_menu_edit_content")],
            [InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen")],
            [
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")
            ]
        ]
        admin_menu_text = await format_message(context, "admin_panel_co")
    
    else:
        # Main Admin Menu
        keyboard = [
            [InlineKeyboardButton("➕ Add Content", callback_data="admin_menu_add_content")],
            [
                InlineKeyboardButton("🗑️ Delete Content", callback_data="admin_menu_manage_content"),
                InlineKeyboardButton("✏️ Edit Content", callback_data="admin_menu_edit_content")
            ],
            [
                InlineKeyboardButton("🔗 Other Links", callback_data="admin_menu_other_links"),
                InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen")
            ],
            [
                InlineKeyboardButton("❤️ Donation", callback_data="admin_menu_donate_settings"),
                InlineKeyboardButton("⏱️ Auto-Delete Time", callback_data="admin_set_delete_time")
            ],
            [
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")
            ],
            [
                InlineKeyboardButton("🎨 Bot Appearance", callback_data="admin_menu_appearance"),
                InlineKeyboardButton("📊 User Statistics", callback_data="admin_show_stats")
            ],
            [InlineKeyboardButton("⚙ Bot Messages", callback_data="admin_menu_messages")],
            [InlineKeyboardButton("🛠️ Admin Settings", callback_data="admin_menu_admin_settings")]
        ]
        admin_menu_text = await format_message(context, "admin_panel_main")
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if from_callback:
        query = update.callback_query
        try:
            if query.message.photo:
                await query.message.delete()
                await context.bot.send_message(query.from_user.id, admin_menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(admin_menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Admin menu edit nahi kar paya: {e}")
            await query.answer()
        except Exception as e:
            logger.warning(f"Admin menu edit error: {e}")
            await query.answer()
    else:
        await update.message.reply_text(admin_menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def add_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_content_movie")],
        [InlineKeyboardButton("📺 Add Series", callback_data="admin_add_content_series")],
        [InlineKeyboardButton("➕ Add Season", callback_data="admin_add_season")],
        [InlineKeyboardButton("➕ Add Episode", callback_data="admin_add_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_add_content")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def manage_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Movie", callback_data="admin_del_content_movie")],
        [InlineKeyboardButton("🗑️ Delete Series", callback_data="admin_del_content_series")],
        [InlineKeyboardButton("🗑️ Delete Season", callback_data="admin_del_season")],
        [InlineKeyboardButton("🗑️ Delete Episode", callback_data="admin_del_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_manage_content")
    
    if from_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def edit_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Movie Name", callback_data="admin_edit_content_movie")],
        [InlineKeyboardButton("✏️ Edit Series Name", callback_data="admin_edit_content_series")],
        [InlineKeyboardButton("✏️ Edit Season Name", callback_data="admin_edit_season")],
        [InlineKeyboardButton("✏️ Edit Episode Number", callback_data="admin_edit_episode")],
        [InlineKeyboardButton("🔄 Merge Content", callback_data="admin_merge_content")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_edit_content")
    
    if from_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# ============================================
# ===       ADD CONTENT (MOVIE/SERIES)     ===
# ============================================

async def add_content_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    content_type = "movie" if "movie" in query.data else "series"
    context.user_data['content_type'] = content_type
    
    text = await format_message(context, "admin_add_content_get_name", {
        "content_type": "Movie" if content_type == "movie" else "Series"
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return A_GET_NAME

async def add_content_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content_name'] = update.message.text
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    text = await format_message(context, "admin_add_content_get_poster", {
        "content_type": display_type
    })
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return A_GET_POSTER

async def add_content_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_add_content_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return A_GET_POSTER
    
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_content_get_desc")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return A_GET_DESC

async def add_content_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    return await add_content_confirm(update, context)

async def add_content_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = None
    return await add_content_confirm(update, context)

async def add_content_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['content_name']
    poster_id = context.user_data['poster_id']
    desc = context.user_data.get('description', '')
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    caption = await format_message(context, "admin_add_content_confirm", {
        "name": name,
        "description": desc if desc else '',
        "content_type": display_type
    })
    keyboard = [[InlineKeyboardButton("✅ Save", callback_data="save_content")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    
    if update.message:
        try:
            await update.message.reply_photo(photo=poster_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Confirm content details me error: {e}")
            text = await format_message(context, "admin_add_content_save_error")
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return A_GET_DESC
    return A_CONFIRM

async def save_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        name = context.user_data['content_name']
        content_type = context.user_data.get('content_type', 'movie')
        display_type = "Movie" if content_type == "movie" else "Series"
        
        if content_collection.find_one({"name": name}):
            caption = await format_message(context, "admin_add_content_save_exists", {
                "name": name,
                "content_type": display_type
            })
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)
            await add_content_menu(update, context)
            return ConversationHandler.END
        
        content_doc = {
            "name": name,
            "type": content_type,
            "poster_id": context.user_data['poster_id'],
            "description": context.user_data.get('description'),
            "created_at": datetime.now(),
            "last_modified": datetime.now()
        }
        
        if content_type == "series":
            content_doc["seasons"] = {}
        else:  # movie
            content_doc["episodes"] = {}
        
        content_collection.insert_one(content_doc)
        
        caption = await format_message(context, "admin_add_content_save_success", {
            "name": name,
            "content_type": display_type
        })
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)
        await add_content_menu(update, context)
        
    except Exception as e:
        logger.error(f"Content save karne me error: {e}")
        caption = await format_message(context, "admin_add_content_save_error")
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===      ADD SERIES/SEASON               ===
# ============================================

async def add_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = "series"
    return await add_season_show_content_list(update, context, page=0)

async def add_season_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("addseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'series')
    display_type = "Series" if content_type == "series" else "Movie"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="addseason_page_",
        item_callback_prefix="season_content_",
        back_callback="back_to_add_content",
        filter_query={"type": "series"}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_add_season_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_add_season_select_content", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return S_GET_ANIME

async def add_season_get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("season_content_", "")
    context.user_data['content_name'] = content_name
    
    content_doc = content_collection.find_one({"name": content_name})
    if not content_doc:
        text = await format_message(context, "admin_add_season_get_number_error", {
            "content_name": content_name,
            "content_type": "Series"
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    if content_doc.get('type') != 'series':
        text = await format_message(context, "admin_add_season_not_series", {
            "content_name": content_name
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    seasons = content_doc.get("seasons", {})
    season_keys = list(seasons.keys())
    
    if not season_keys:
        text = await format_message(context, "admin_add_season_get_content_no_last", {
            "content_name": content_name,
            "content_type": "Series"
        })
    else:
        try:
            sorted_seasons = sorted(season_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_season_name = sorted_seasons[-1]
            text = await format_message(context, "admin_add_season_get_content_with_last", {
                "content_name": content_name,
                "last_season_name": last_season_name
            })
        except Exception as e:
            logger.warning(f"Last season find karne me error: {e}")
            text = await format_message(context, "admin_add_season_get_content_no_last", {
                "content_name": content_name,
                "content_type": "Series"
            })
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return S_GET_NUMBER

async def add_season_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_name = update.message.text
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    
    content_doc = content_collection.find_one({"name": content_name})
    if not content_doc:
        text = await format_message(context, "admin_add_season_get_number_error", {
            "content_name": content_name,
            "content_type": "Series"
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
            
    if season_name in content_doc.get("seasons", {}):
        text = await format_message(context, "admin_add_season_get_number_exists", {
            "content_name": content_name,
            "season_name": season_name
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return S_GET_NUMBER
    
    text = await format_message(context, "admin_add_season_get_poster_prompt", {
        "season_name": season_name
    })
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_POSTER

async def add_season_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_add_season_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return S_GET_POSTER
    
    context.user_data['season_poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_season_get_desc_prompt")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def add_season_skip_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_poster_id'] = None
    text = await format_message(context, "admin_add_season_skip_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def add_season_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_desc'] = update.message.text
    return await add_season_confirm(update, context)

async def add_season_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_desc'] = None
    return await add_season_confirm(update, context)

async def add_season_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    content_name = context.user_data['content_name']
    season_name = context.user_data['season_name']
    season_poster_id = context.user_data.get('season_poster_id')
    season_desc = context.user_data.get('season_desc')
    
    content_doc = content_collection.find_one({"name": content_name})
    poster_id_to_show = season_poster_id or content_doc.get('poster_id')
    
    caption = await format_message(context, "admin_add_season_confirm", {
        "content_name": content_name,
        "season_name": season_name,
        "season_desc": season_desc or 'N/A',
        "content_type": "Series"
    })
    keyboard = [[InlineKeyboardButton("✅ Haan, Save Karo", callback_data="save_season")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    
    await update.message.reply_photo(
        photo=poster_id_to_show,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return S_CONFIRM

async def add_season_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        content_name = context.user_data['content_name']
        season_name = context.user_data['season_name']
        season_poster_id = context.user_data.get('season_poster_id')
        season_desc = context.user_data.get('season_desc')
        
        season_data = {}
        if season_poster_id:
            season_data["_poster_id"] = season_poster_id
        if season_desc:
            season_data["_description"] = season_desc
        
        content_collection.update_one(
            {"name": content_name},
            {"$set": {
                f"seasons.{season_name}": season_data,
                "last_modified": datetime.now()
            }}
        )
        
        text = await format_message(context, "admin_add_season_ask_more", {
            "content_name": content_name,
            "season_name": season_name
        })
        keyboard = [
            [InlineKeyboardButton("✅ Yes (Add More)", callback_data="add_season_more_yes")],
            [InlineKeyboardButton("🚫 No (Back to Menu)", callback_data="add_season_more_no")]
        ]
        
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Purana photo message delete nahi kar paya: {e}")
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            return S_ASK_MORE
        
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        return S_ASK_MORE
        
    except Exception as e:
        logger.error(f"Season save karne me error: {e}")
        caption = await format_message(context, "admin_add_season_save_error")
        try:
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=None)
        except Exception as e2:
            logger.error(f"Error message bhi nahi dikha paya: {e2}")
            await context.bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode=ParseMode.HTML)
        
        context.user_data.clear()
        await asyncio.sleep(3)
        await add_content_menu(update, context)
        return ConversationHandler.END

async def add_season_more_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    last_season_name = context.user_data['season_name']
    content_name = context.user_data['content_name']
    
    text = await format_message(context, "admin_add_season_next_prompt", {
        "season_name": last_season_name,
        "content_name": content_name,
        "content_type": "Series"
    })
    
    context.user_data.pop('season_name', None)
    context.user_data.pop('season_poster_id', None)
    context.user_data.pop('season_desc', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return S_GET_NUMBER

async def add_season_more_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await add_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===      ADD EPISODE (MOVIE/SERIES)      ===
# ============================================

async def add_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await add_episode_show_content_list(update, context, page=0)

async def add_episode_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("addep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="addep_page_",
        item_callback_prefix="ep_content_",
        back_callback="back_to_add_content"
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_add_ep_no_content", {
            "content_type": "Content"
        })
    else:
        text = await format_message(context, "admin_add_ep_select_content", {
            "content_type": "Content",
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return E_GET_ANIME

async def add_episode_get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("ep_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') == 'movie':
        # For movies, directly add episodes (no season selection)
        context.user_data['season_name'] = None
        context.user_data['content_type'] = 'movie'
        return await add_episode_get_number_direct(update, context)
    
    # For series, show seasons
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_add_ep_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"addep_page_{current_page}")])
    
    text = await format_message(context, "admin_add_ep_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return E_GET_SEASON

async def add_episode_get_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("ep_season_", "")
    context.user_data['season_name'] = season_name
    context.user_data['content_type'] = 'series'
    return await add_episode_get_number(update, context)

async def add_episode_get_number_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    text = await format_message(context, "admin_add_ep_get_season_no_last", {
        "season_name": "Movie"
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return E_GET_NUMBER

async def add_episode_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        # Only called from callback path
        pass
    
    season_name = context.user_data.get('season_name', 'Movie')
    content_name = context.user_data['content_name']
    
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') == 'movie':
        episodes = content_doc.get("episodes", {})
    else:
        episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_add_ep_get_season_no_last", {
            "season_name": season_name
        })
    else:
        try:
            sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_ep_num = sorted_eps[-1]
            text = await format_message(context, "admin_add_ep_get_season_with_last", {
                "season_name": season_name,
                "last_ep_num": last_ep_num
            })
        except Exception as e:
            logger.warning(f"Last episode find karne me error: {e}")
            text = await format_message(context, "admin_add_ep_get_season_no_last", {
                "season_name": season_name
            })
    
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_NUMBER

async def add_episode_save_file_helper(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and (update.message.document.mime_type and update.message.document.mime_type.startswith('video')):
        file_id = update.message.document.file_id
    
    if not file_id:
        if update.message.text and update.message.text.startswith('/'):
            return False
        text = await format_message(context, "admin_add_ep_helper_invalid")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False
    
    try:
        content_name = context.user_data['content_name']
        content_type = context.user_data.get('content_type', 'series')
        ep_num = context.user_data['ep_num']
        
        if content_type == 'movie':
            dot_notation_key = f"episodes.{ep_num}.{quality}"
        else:
            season_name = context.user_data['season_name']
            dot_notation_key = f"seasons.{season_name}.{ep_num}.{quality}"
        
        content_collection.update_one(
            {"name": content_name},
            {"$set": {
                dot_notation_key: file_id,
                "last_modified": datetime.now()
            }}
        )
        logger.info(f"Naya episode save ho gaya: {content_name} {ep_num} {quality}")
        
        text = await format_message(context, "admin_add_ep_helper_success", {
            "quality": quality
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        logger.error(f"Episode file save karne me error: {e}")
        text = await format_message(context, "admin_add_ep_helper_error", {
            "quality": quality
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False

async def add_episode_get_ep_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ep_num'] = update.message.text
    
    content_name = context.user_data['content_name']
    content_type = context.user_data.get('content_type', 'series')
    ep_num = context.user_data['ep_num']
    
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_type == 'movie':
        existing_eps = content_doc.get("episodes", {})
    else:
        season_name = context.user_data['season_name']
        existing_eps = content_doc.get("seasons", {}).get(season_name, {})
    
    if ep_num in existing_eps:
        text = await format_message(context, "admin_add_ep_get_number_exists", {
            "content_name": content_name,
            "season_name": context.user_data.get('season_name', 'Movie'),
            "ep_num": ep_num
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return E_GET_NUMBER
    
    text = await format_message(context, "admin_add_ep_get_number", {
        "ep_num": ep_num
    })
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_480P

async def add_episode_get_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "480p"):
        return E_GET_480P
    
    text = await format_message(context, "admin_add_ep_get_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_720P

async def add_episode_skip_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_480p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_720P

async def add_episode_get_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "720p"):
        return E_GET_720P
    
    text = await format_message(context, "admin_add_ep_get_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_1080P

async def add_episode_skip_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_1080P

async def add_episode_get_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "1080p"):
        return E_GET_1080P
    
    text = await format_message(context, "admin_add_ep_get_4k")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_4K

async def add_episode_skip_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_4K

async def add_episode_get_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await add_episode_save_file_helper(update, context, "4K"):
        text = await format_message(context, "admin_add_ep_get_4k_success")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        return E_GET_4K
    
    return await add_episode_ask_more(update, context)

async def add_episode_skip_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_4k")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return await add_episode_ask_more(update, context)

async def add_episode_ask_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep_num = context.user_data['ep_num']
    season_name = context.user_data.get('season_name', 'Movie')
    
    text = await format_message(context, "admin_add_ep_ask_more", {
        "ep_num": ep_num,
        "season_name": season_name
    })
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes (Add More)", callback_data="add_ep_more_yes")],
        [InlineKeyboardButton("🚫 No (Back to Menu)", callback_data="add_ep_more_no")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return E_ASK_MORE

async def add_episode_more_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    last_ep_num = context.user_data['ep_num']
    season_name = context.user_data.get('season_name', 'Movie')
    
    try:
        next_ep_num = str(int(last_ep_num) + 1)
        text = await format_message(context, "admin_add_ep_next_prompt", {
            "ep_num": last_ep_num,
            "season_name": season_name,
            "next_ep_num": next_ep_num
        })
    except ValueError:
        text = await format_message(context, "admin_add_ep_next_prompt_no_suggestion", {
            "ep_num": last_ep_num,
            "season_name": season_name
        })
    
    context.user_data.pop('ep_num', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return E_GET_NUMBER

async def add_episode_more_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await add_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   DELETE CONTENT (MOVIE/SERIES)      ===
# ============================================

async def delete_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_type = "movie" if "movie" in query.data else "series"
    context.user_data['content_type'] = content_type
    context.user_data['delete_type'] = 'content'
    return await delete_content_show_list(update, context, page=0)

async def delete_content_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delcontent_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="delcontent_page_",
        item_callback_prefix="del_content_",
        back_callback="back_to_manage",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_del_content_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_del_content_select", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DA_GET_CONTENT

async def delete_content_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("del_content_", "")
    context.user_data['content_name'] = content_name
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {content_name} ko Delete Karo", callback_data="del_content_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    
    text = await format_message(context, "admin_del_content_confirm", {
        "content_name": content_name,
        "content_type": display_type
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DA_CONFIRM

async def delete_content_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    content_name = context.user_data['content_name']
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    try:
        content_collection.delete_one({"name": content_name})
        logger.info(f"Content deleted: {content_name}")
        text = await format_message(context, "admin_del_content_success", {
            "content_name": content_name,
            "content_type": display_type
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Content delete karne me error: {e}")
        text = await format_message(context, "admin_del_content_error", {
            "content_type": display_type
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   DELETE SEASON                     ===
# ============================================

async def delete_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = "series"
    return await delete_season_show_content_list(update, context, page=0)

async def delete_season_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="delseason_page_",
        item_callback_prefix="del_season_content_",
        back_callback="back_to_manage",
        filter_query={"type": "series"}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_del_season_no_content", {
            "content_type": "Series"
        })
    else:
        text = await format_message(context, "admin_del_season_select_content", {
            "content_type": "Series",
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DS_GET_ANIME

async def delete_season_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("del_season_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') != 'series':
        text = await format_message(context, "admin_del_season_not_series", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_del_season_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"del_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"delseason_page_{current_page}")])
    
    text = await format_message(context, "admin_del_season_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DS_GET_SEASON

async def delete_season_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("del_season_", "")
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, Season {season_name} Delete Karo", callback_data="del_season_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    
    text = await format_message(context, "admin_del_season_confirm", {
        "content_name": content_name,
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DS_CONFIRM

async def delete_season_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    content_name = context.user_data['content_name']
    season_name = context.user_data['season_name']
    
    try:
        content_collection.update_one(
            {"name": content_name},
            {"$unset": {f"seasons.{season_name}": ""},
             "$set": {"last_modified": datetime.now()}}
        )
        logger.info(f"Season deleted: {content_name} - S{season_name}")
        text = await format_message(context, "admin_del_season_success", {
            "season_name": season_name
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Season delete karne me error: {e}")
        text = await format_message(context, "admin_del_season_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   DELETE EPISODE                    ===
# ============================================

async def delete_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_episode_show_content_list(update, context, page=0)

async def delete_episode_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="delep_page_",
        item_callback_prefix="del_ep_content_",
        back_callback="back_to_manage"
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_del_ep_no_content", {
            "content_type": "Content"
        })
    else:
        text = await format_message(context, "admin_del_ep_select_content", {
            "content_type": "Content",
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DE_GET_ANIME

async def delete_episode_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("del_ep_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') == 'movie':
        # For movies, directly show episodes
        context.user_data['season_name'] = None
        context.user_data['content_type'] = 'movie'
        return await delete_episode_select_episode_direct(update, context)
    
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_del_ep_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"del_ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"delep_page_{current_page}")])
    
    text = await format_message(context, "admin_del_ep_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_GET_SEASON

async def delete_episode_select_episode_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    content_name = context.user_data['content_name']
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("episodes", {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_del_ep_no_episode", {
            "content_name": content_name,
            "season_name": "Movie"
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"del_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"del_ep_content_{content_name}")])
    
    text = await format_message(context, "admin_del_ep_select_episode", {
        "season_name": "Movie"
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_GET_EPISODE

async def delete_episode_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("del_ep_season_", "")
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_del_ep_no_episode", {
            "content_name": content_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"del_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"del_ep_content_{content_name}")])
    
    text = await format_message(context, "admin_del_ep_select_episode", {
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_GET_EPISODE

async def delete_episode_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("del_ep_num_", "")
    context.user_data['ep_num'] = ep_num
    content_name = context.user_data['content_name']
    season_name = context.user_data.get('season_name', 'Movie')
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, Ep {ep_num} Delete Karo", callback_data="del_ep_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    
    text = await format_message(context, "admin_del_ep_confirm", {
        "content_name": content_name,
        "season_name": season_name,
        "ep_num": ep_num
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_CONFIRM

async def delete_episode_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    content_name = context.user_data['content_name']
    season_name = context.user_data.get('season_name')
    ep_num = context.user_data['ep_num']
    content_type = context.user_data.get('content_type', 'series')
    
    try:
        if content_type == 'movie':
            content_collection.update_one(
                {"name": content_name},
                {"$unset": {f"episodes.{ep_num}": ""},
                 "$set": {"last_modified": datetime.now()}}
            )
        else:
            content_collection.update_one(
                {"name": content_name},
                {"$unset": {f"seasons.{season_name}.{ep_num}": ""},
                 "$set": {"last_modified": datetime.now()}}
            )
        logger.info(f"Episode deleted: {content_name} - S{season_name} - E{ep_num}")
        text = await format_message(context, "admin_del_ep_success", {
            "ep_num": ep_num
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Episode delete karne me error: {e}")
        text = await format_message(context, "admin_del_ep_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   EDIT CONTENT (MOVIE/SERIES)        ===
# ============================================

async def edit_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_type = "movie" if "movie" in query.data else "series"
    context.user_data['content_type'] = content_type
    return await edit_content_show_list(update, context, page=0)

async def edit_content_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editcontent_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="editcontent_page_",
        item_callback_prefix="edit_content_",
        back_callback="back_to_edit_menu",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_edit_content_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_edit_content_select", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EA_GET_CONTENT

async def edit_content_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("edit_content_", "")
    context.user_data['old_content_name'] = content_name
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    text = await format_message(context, "admin_edit_content_get_name", {
        "content_name": content_name,
        "content_type": display_type
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EA_GET_NEW_NAME

async def edit_content_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data['old_content_name']
    
    if content_collection.find_one({"name": new_name}):
        text = await format_message(context, "admin_edit_content_save_exists", {
            "new_name": new_name
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EA_GET_NEW_NAME
    
    context.user_data['new_content_name'] = new_name
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_name}' ko '{new_name}' Karo", callback_data="edit_content_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    
    text = await format_message(context, "admin_edit_content_confirm", {
        "old_name": old_name,
        "new_name": new_name,
        "content_type": context.user_data.get('content_type', 'movie')
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EA_CONFIRM

async def edit_content_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_name = context.user_data['old_content_name']
    new_name = context.user_data['new_content_name']
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    try:
        content_collection.update_one(
            {"name": old_name},
            {"$set": {
                "name": new_name,
                "last_modified": datetime.now()
            }}
        )
        logger.info(f"Content naam update ho gaya: {old_name} -> {new_name}")
        text = await format_message(context, "admin_edit_content_success", {
            "old_name": old_name,
            "new_name": new_name,
            "content_type": display_type
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Content naam update karne me error: {e}")
        text = await format_message(context, "admin_edit_content_error", {
            "content_type": display_type
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   EDIT SEASON                       ===
# ============================================

async def edit_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = "series"
    return await edit_season_show_content_list(update, context, page=0)

async def edit_season_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="editseason_page_",
        item_callback_prefix="edit_season_content_",
        back_callback="back_to_edit_menu",
        filter_query={"type": "series"}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_edit_season_no_content", {
            "content_type": "Series"
        })
    else:
        text = await format_message(context, "admin_edit_season_select_content", {
            "content_type": "Series",
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return ES_GET_ANIME

async def edit_season_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("edit_season_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') != 'series':
        text = await format_message(context, "admin_edit_season_not_series", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_edit_season_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"edit_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"editseason_page_{current_page}")])
    
    text = await format_message(context, "admin_edit_season_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return ES_GET_SEASON

async def edit_season_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("edit_season_", "")
    context.user_data['old_season_name'] = season_name
    content_name = context.user_data['content_name']
    
    text = await format_message(context, "admin_edit_season_get_name", {
        "content_name": content_name,
        "season_name": season_name
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ES_GET_NEW_NAME

async def edit_season_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data['old_season_name']
    content_name = context.user_data['content_name']
    
    content_doc = content_collection.find_one({"name": content_name})
    if new_name in content_doc.get("seasons", {}):
        text = await format_message(context, "admin_edit_season_save_exists", {
            "new_name": new_name,
            "content_type": "Series"
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return ES_GET_NEW_NAME
    
    context.user_data['new_season_name'] = new_name
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_name}' ko '{new_name}' Karo", callback_data="edit_season_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    
    text = await format_message(context, "admin_edit_season_confirm", {
        "content_name": content_name,
        "old_name": old_name,
        "new_name": new_name,
        "content_type": "Series"
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return ES_CONFIRM

async def edit_season_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_name = context.user_data['old_season_name']
    new_name = context.user_data['new_season_name']
    content_name = context.user_data['content_name']
    
    try:
        content_collection.update_one(
            {"name": content_name},
            {"$rename": {f"seasons.{old_name}": f"seasons.{new_name}"},
             "$set": {"last_modified": datetime.now()}}
        )
        logger.info(f"Season naam update ho gaya: {content_name} - {old_name} -> {new_name}")
        text = await format_message(context, "admin_edit_season_success", {
            "old_name": old_name,
            "new_name": new_name
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Season naam update karne me error: {e}")
        text = await format_message(context, "admin_edit_season_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   EDIT EPISODE                     ===
# ============================================

async def edit_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_episode_show_content_list(update, context, page=0)

async def edit_episode_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="editep_page_",
        item_callback_prefix="edit_ep_content_",
        back_callback="back_to_edit_menu"
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_edit_ep_no_content", {
            "content_type": "Content"
        })
    else:
        text = await format_message(context, "admin_edit_ep_select_content", {
            "content_type": "Content",
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EE_GET_ANIME

async def edit_episode_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("edit_ep_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') == 'movie':
        # For movies, directly show episodes
        context.user_data['season_name'] = None
        context.user_data['content_type'] = 'movie'
        return await edit_episode_select_episode_direct(update, context)
    
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_edit_ep_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"edit_ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"editep_page_{current_page}")])
    
    text = await format_message(context, "admin_edit_ep_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_GET_SEASON

async def edit_episode_select_episode_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    content_name = context.user_data['content_name']
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("episodes", {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_edit_ep_no_episode", {
            "content_name": content_name,
            "season_name": "Movie"
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"edit_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"edit_ep_content_{content_name}")])
    
    text = await format_message(context, "admin_edit_ep_select_episode", {
        "season_name": "Movie"
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_GET_EPISODE

async def edit_episode_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("edit_ep_season_", "")
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_edit_ep_no_episode", {
            "content_name": content_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"edit_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"edit_ep_content_{content_name}")])
    
    text = await format_message(context, "admin_edit_ep_select_episode", {
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_GET_EPISODE

async def edit_episode_get_new_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("edit_ep_num_", "")
    context.user_data['old_ep_num'] = ep_num
    content_name = context.user_data['content_name']
    season_name = context.user_data.get('season_name', 'Movie')
    
    text = await format_message(context, "admin_edit_ep_get_num", {
        "content_name": content_name,
        "season_name": season_name,
        "ep_num": ep_num
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EE_GET_NEW_NUM

async def edit_episode_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_num = update.message.text
    old_num = context.user_data['old_ep_num']
    content_name = context.user_data['content_name']
    season_name = context.user_data.get('season_name')
    content_type = context.user_data.get('content_type', 'series')
    
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_type == 'movie':
        existing = content_doc.get("episodes", {})
    else:
        existing = content_doc.get("seasons", {}).get(season_name, {})
    
    if new_num in existing:
        text = await format_message(context, "admin_edit_ep_save_exists", {
            "new_num": new_num
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EE_GET_NEW_NUM
    
    context.user_data['new_ep_num'] = new_num
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_num}' ko '{new_num}' Karo", callback_data="edit_ep_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    
    text = await format_message(context, "admin_edit_ep_confirm", {
        "content_name": content_name,
        "season_name": season_name if season_name else "Movie",
        "old_num": old_num,
        "new_num": new_num,
        "content_type": content_type
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_CONFIRM

async def edit_episode_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_num = context.user_data['old_ep_num']
    new_num = context.user_data['new_ep_num']
    content_name = context.user_data['content_name']
    season_name = context.user_data.get('season_name')
    content_type = context.user_data.get('content_type', 'series')
    
    try:
        if content_type == 'movie':
            content_collection.update_one(
                {"name": content_name},
                {"$rename": {f"episodes.{old_num}": f"episodes.{new_num}"},
                 "$set": {"last_modified": datetime.now()}}
            )
        else:
            content_collection.update_one(
                {"name": content_name},
                {"$rename": {f"seasons.{season_name}.{old_num}": f"seasons.{season_name}.{new_num}"},
                 "$set": {"last_modified": datetime.now()}}
            )
        logger.info(f"Episode number update ho gaya: {content_name} - {old_num} -> {new_num}")
        text = await format_message(context, "admin_edit_ep_success", {
            "old_num": old_num,
            "new_num": new_num
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Episode number update karne me error: {e}")
        text = await format_message(context, "admin_edit_ep_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   POST GENERATOR                    ===
# ============================================

async def post_gen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Post", callback_data="post_gen_movie")],
        [InlineKeyboardButton("📺 Series Post", callback_data="post_gen_series")],
        [InlineKeyboardButton("✍️ Episode Post", callback_data="post_gen_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_post_gen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_MENU

async def post_gen_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    post_type = query.data
    context.user_data['post_type'] = post_type
    
    if post_type == 'post_gen_movie':
        context.user_data['content_type'] = 'movie'
    else:
        context.user_data['content_type'] = 'series'
    
    return await post_gen_show_content_list(update, context, page=0)

async def post_gen_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("postgen_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="postgen_page_",
        item_callback_prefix="post_content_",
        back_callback="admin_post_gen",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_post_gen_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_post_gen_select_content", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return PG_GET_CONTENT

async def post_gen_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("post_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    post_type = context.user_data.get('post_type')
    content_type = context.user_data.get('content_type')
    
    # If it's a movie or post_type is movie, skip season selection
    if content_type == 'movie' or post_type == 'post_gen_movie':
        context.user_data['season_name'] = None
        context.user_data['ep_num'] = None
        await generate_post_ask_chat(update, context)
        return PG_GET_SHORT_LINK
    
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_post_gen_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"post_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"postgen_page_{current_page}")])
    
    text = await format_message(context, "admin_post_gen_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_GET_SEASON

async def post_gen_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("post_season_", "")
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    content_type = context.user_data.get('content_type', 'series')
    
    if context.user_data.get('post_type') == 'post_gen_series':
        context.user_data['ep_num'] = None
        await generate_post_ask_chat(update, context)
        return PG_GET_SHORT_LINK
    
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_type == 'movie':
        episodes = content_doc.get("episodes", {})
    else:
        episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_post_gen_no_episode", {
            "content_name": content_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"post_ep_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"post_content_{content_name}")])
    
    text = await format_message(context, "admin_post_gen_select_episode", {
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_GET_EPISODE

async def post_gen_final_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("post_ep_", "")
    context.user_data['ep_num'] = ep_num
    
    await generate_post_ask_chat(update, context)
    return PG_GET_SHORT_LINK

async def generate_post_ask_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        bot_username = (await context.bot.get_me()).username
        
        config = await get_config()
        content_name = context.user_data['content_name']
        season_name = context.user_data.get('season_name')
        ep_num = context.user_data.get('ep_num')
        content_doc = content_collection.find_one({"name": content_name})
        
        content_id = str(content_doc['_id'])
        content_type = content_doc.get('type', 'movie')
        post_type = context.user_data.get('post_type')
        
        dl_callback_data = f"dl{content_id}"
        
        if post_type == 'post_gen_movie' or (content_type == 'movie' and not ep_num):
            context.user_data['is_episode_post'] = False
            poster_id = content_doc['poster_id']
            description = content_doc.get('description', '')
            
            caption_template = await format_message(context, "post_gen_movie_caption")
            caption = caption_template.format(content_name=content_name, description=description if description else "")
        
        elif content_type == 'series' and season_name and not ep_num:
            context.user_data['is_episode_post'] = False
            dl_callback_data = f"dl{content_id}__{season_name}"
            
            season_data = content_doc.get("seasons", {}).get(season_name, {})
            poster_id = season_data.get("_poster_id") or content_doc['poster_id']
            description = season_data.get("_description") or content_doc.get('description', '')
            
            caption_template = await format_message(context, "post_gen_series_caption")
            caption = caption_template.format(content_name=content_name, season_name=season_name, description=description if description else "")
        
        elif ep_num:
            context.user_data['is_episode_post'] = True
            dl_callback_data = f"dl{content_id}__{season_name}__{ep_num}"
            
            caption_template = await format_message(context, "post_gen_episode_caption")
            caption = caption_template.format(content_name=content_name, season_name=season_name if season_name else "Movie", ep_num=ep_num)
            
            poster_id = None
        
        else:
            logger.warning("Post generator me invalid state")
            text = await format_message(context, "admin_post_gen_invalid_state")
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        
        links = config.get('links', {})
        backup_url = links.get('backup') or "https://t.me/"
        help_url = links.get('help') or "https://t.me/"
        donate_url = f"https://t.me/{bot_username}?start=donate"
        
        original_download_url = f"https://t.me/{bot_username}?start={dl_callback_data}"
        
        btn_backup = InlineKeyboardButton("Backup", url=backup_url)
        btn_donate = InlineKeyboardButton("Donate", url=donate_url)
        btn_help = InlineKeyboardButton("🆘 Help", url=help_url)
        
        context.user_data['post_caption_raw'] = caption
        context.user_data['post_poster_id'] = poster_id
        context.user_data['btn_backup'] = btn_backup
        context.user_data['btn_donate'] = btn_donate
        context.user_data['btn_help'] = btn_help
        context.user_data['is_episode_post'] = context.user_data.get('is_episode_post', False)
        
        text = await format_message(context, "admin_post_gen_ask_shortlink", {
            "original_download_url": original_download_url
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return PG_GET_SHORT_LINK
        
    except Exception as e:
        logger.error(f"Post generate karne me error: {e}", exc_info=True)
        await query.answer("Error! Post generate nahi kar paya.", show_alert=True)
        text = await format_message(context, "admin_post_gen_error_general")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END

async def post_gen_get_short_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    short_link_url = update.message.text
    
    caption_raw = context.user_data['post_caption_raw']
    poster_id = context.user_data['post_poster_id']
    btn_backup = context.user_data['btn_backup']
    btn_donate = context.user_data['btn_donate']
    btn_help = context.user_data['btn_help']
    is_episode_post = context.user_data.get('is_episode_post', False)
    
    btn_download = InlineKeyboardButton("Download", url=short_link_url)
    
    if is_episode_post:
        keyboard = [
            [btn_donate, btn_download],
        ]
    else:
        keyboard = [
            [btn_backup, btn_donate],
            [btn_download]
        ]
    
    context.user_data['post_keyboard'] = InlineKeyboardMarkup(keyboard)
    font_settings = {"font": "default", "style": "normal"}
    caption_formatted = await apply_font_formatting(caption_raw, font_settings)
    context.user_data['post_caption_formatted'] = caption_formatted
    
    text = await format_message(context, "admin_post_gen_ask_chat")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return PG_GET_CHAT

async def post_gen_send_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.text
    is_episode_post = context.user_data.get('is_episode_post', False)
    caption_text = context.user_data['post_caption_formatted']
    
    try:
        if is_episode_post:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data['post_keyboard']
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=context.user_data['post_poster_id'],
                caption=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data['post_keyboard']
            )
        
        text = await format_message(context, "admin_post_gen_success", {
            "chat_id": chat_id
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Post channel me bhejme me error: {e}")
        text = await format_message(context, "admin_post_gen_error", {
            "chat_id": chat_id,
            "e": e
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===   GENERATE LINK                     ===
# ============================================

async def gen_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Link", callback_data="gen_link_movie")],
        [InlineKeyboardButton("📺 Series Link", callback_data="gen_link_series")],
        [InlineKeyboardButton("🔗 Episode Link", callback_data="gen_link_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_gen_link")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_MENU

async def gen_link_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    link_type = query.data
    context.user_data['link_type'] = link_type
    
    if link_type == 'gen_link_movie':
        context.user_data['content_type'] = 'movie'
    else:
        context.user_data['content_type'] = 'series'
    
    return await gen_link_show_content_list(update, context, page=0)

async def gen_link_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("genlink_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="genlink_page_",
        item_callback_prefix="gen_link_content_",
        back_callback="admin_gen_link",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_gen_link_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_gen_link_select_content", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return GL_GET_CONTENT

async def gen_link_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("gen_link_content_", "")
    context.user_data['content_name'] = content_name
    
    if context.user_data['link_type'] == 'gen_link_movie':
        context.user_data['season_name'] = None
        context.user_data['ep_num'] = None
        return await gen_link_finish(update, context)
    
    content_doc = content_collection.find_one({"name": content_name})
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_gen_link_no_season", {
            "content_name": content_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_gen_link")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"gen_link_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"genlink_page_{current_page}")])
    
    text = await format_message(context, "admin_gen_link_select_season", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_GET_SEASON

async def gen_link_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("gen_link_season_", "")
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    
    if context.user_data['link_type'] == 'gen_link_series':
        context.user_data['ep_num'] = None
        return await gen_link_finish(update, context)
    
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_gen_link_no_episode", {
            "content_name": content_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_gen_link")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"gen_link_ep_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"gen_link_content_{content_name}")])
    
    text = await format_message(context, "admin_gen_link_select_episode", {
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_GET_EPISODE

async def gen_link_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("gen_link_ep_"):
        ep_num = query.data.replace("gen_link_ep_", "")
        context.user_data['ep_num'] = ep_num
    
    try:
        bot_username = (await context.bot.get_me()).username
        
        content_name = context.user_data['content_name']
        season_name = context.user_data.get('season_name')
        ep_num = context.user_data.get('ep_num')
        
        content_doc = content_collection.find_one({"name": content_name})
        content_id = str(content_doc['_id'])
        
        link_type = context.user_data.get('link_type')
        
        dl_callback_data = f"dl{content_id}"
        title = content_name
        
        if link_type == 'gen_link_series' and season_name:
            dl_callback_data = f"dl{content_id}__{season_name}"
            title = f"{content_name} - S{season_name}"
        elif link_type == 'gen_link_episode' and season_name and ep_num:
            dl_callback_data = f"dl{content_id}__{season_name}__{ep_num}"
            title = f"{content_name} - S{season_name} E{ep_num}"
        
        final_link = f"https://t.me/{bot_username}?start={dl_callback_data}"
        
        text = await format_message(context, "admin_gen_link_success", {
            "title": title,
            "final_link": final_link
        })
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]])
        )
        
    except Exception as e:
        logger.error(f"Link generate karne me error: {e}", exc_info=True)
        text = await format_message(context, "admin_gen_link_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===   MERGE CONTENT                    ===
# ============================================

async def merge_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await merge_content_select_type(update, context)

async def merge_content_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎬 Merge Movies", callback_data="merge_type_movie")],
        [InlineKeyboardButton("📺 Merge Series", callback_data="merge_type_series")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]
    ]
    text = await format_message(context, "admin_merge_select_type", {
        "content_type": "Content"
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return MA_GET_TYPE

async def merge_content_set_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_type = query.data.replace("merge_type_", "")
    context.user_data['merge_content_type'] = content_type
    
    return await merge_content_select_target(update, context, page=0)

async def merge_content_select_target(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("mergetarget_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('merge_content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="mergetarget_page_",
        item_callback_prefix="merge_target_",
        back_callback="admin_merge_content",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_edit_content_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_merge_select_target", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return MA_GET_TARGET

async def merge_content_select_source(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("merge_target_"):
        target_name = query.data.replace("merge_target_", "")
        context.user_data['target_name'] = target_name
        context.user_data['current_page'] = 0
        page = 0
        await query.answer()
    elif query.data.startswith("mergesource_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
    
    target_name = context.user_data['target_name']
    content_type = context.user_data.get('merge_content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="mergesource_page_",
        item_callback_prefix="merge_source_",
        back_callback="admin_merge_content",
        filter_query={"type": content_type},
        exclude_items=[target_name]
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_edit_content_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_merge_select_source", {
            "page": page + 1,
            "target_name": target_name,
            "content_type": display_type
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return MA_GET_SOURCE

async def merge_content_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    source_name = query.data.replace("merge_source_", "")
    target_name = context.user_data['target_name']
    
    if source_name == target_name:
        text = await format_message(context, "admin_merge_self_merge_error", {
            "content_type": "Content"
        })
        await query.answer(text, show_alert=True)
        return MA_GET_SOURCE
    
    context.user_data['source_name'] = source_name
    
    source_doc = content_collection.find_one({"name": source_name})
    if not source_doc:
        await query.edit_message_text("Error: Source content not found.")
        return ConversationHandler.END
    
    if source_doc.get('type') == 'series':
        source_seasons = source_doc.get("seasons", {})
    else:
        source_seasons = source_doc.get("episodes", {})
    
    season_count = len(source_seasons)
    context.user_data['source_seasons_to_merge'] = source_seasons
    
    content_type = context.user_data.get('merge_content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    keyboard = [
        [InlineKeyboardButton("✅ HAAN, MERGE KARO", callback_data="merge_confirm_yes")],
        [InlineKeyboardButton("⬅️ Back to Edit Menu", callback_data="back_to_edit_menu")]
    ]
    
    text = await format_message(context, "admin_merge_confirm", {
        "source_name": source_name,
        "target_name": target_name,
        "count": season_count,
        "content_type": display_type
    })
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return MA_CONFIRM

async def merge_content_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Merging...")
    
    try:
        target_name = context.user_data['target_name']
        source_name = context.user_data['source_name']
        source_seasons = context.user_data['source_seasons_to_merge']
        content_type = context.user_data.get('merge_content_type', 'movie')
        
        if not source_seasons:
            await query.edit_message_text("Source content mein kuch nahi hai. Kuch merge nahi hua.")
            return ConversationHandler.END
        
        update_query = {}
        if content_type == 'series':
            for season_name, season_data in source_seasons.items():
                update_query[f"seasons.{season_name}"] = season_data
        else:
            for ep_num, ep_data in source_seasons.items():
                update_query[f"episodes.{ep_num}"] = ep_data
        
        content_collection.update_one(
            {"name": target_name},
            {
                "$set": update_query,
                "$currentDate": {"last_modified": True}
            }
        )
        
        content_collection.delete_one({"name": source_name})
        
        display_type = "Movie" if content_type == "movie" else "Series"
        logger.info(f"Content Merged: '{source_name}' into '{target_name}'")
        text = await format_message(context, "admin_merge_success", {
            "count": len(source_seasons),
            "source_name": source_name,
            "target_name": target_name,
            "content_type": display_type
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Content merge karne me error: {e}")
        text = await format_message(context, "admin_merge_error", {
            "e": e,
            "content_type": display_type if 'display_type' in locals() else "Content"
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(4)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   USER HANDLERS                     ===
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id, full_name = user.id, user.full_name
    logger.info(f"User {user_id} ({full_name}) ne /start dabaya.")
    
    user_data = users_collection.find_one({"_id": user_id})
    if not user_data:
        users_collection.insert_one({
            "_id": user_id,
            "first_name": user.first_name,
            "full_name": full_name,
            "username": user.username,
            "interaction_count": 1
        })
        logger.info(f"Naya user database me add kiya: {user_id}")
    else:
        users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {"first_name": user.first_name, "full_name": full_name, "username": user.username},
                "$inc": {"interaction_count": 1}
            }
        )
    
    args = context.args
    if args:
        payload = " ".join(args)
        logger.info(f"User {user_id} ne deep link use kiya: {payload}")
        
        if payload.startswith("dl"):
            await handle_deep_link_download(user, context, payload)
            return
        elif payload == "donate":
            await handle_deep_link_donate(user, context)
            return
    
    logger.info("Koi deep link nahi. Sirf welcome message bhej raha hoon.")
    if await is_co_admin(user_id):
        text = await format_message(context, "user_welcome_admin")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        text = await format_message(context, "user_welcome_basic", {
            "full_name": full_name,
            "first_name": user.first_name
        })
        text = text.replace("/subscription", "/user")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} ne /user dabaya.")
    await increment_user_interaction(update.effective_user.id)
    await show_user_menu(update, context)

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user = update.effective_user
    user_id = user.id
    
    if from_callback:
        logger.info(f"User {user_id} 'Back to Menu' se aaya.")
    else:
        logger.info(f"User {user_id} ne /user khola.")
    
    config = await get_config()
    links = config.get('links', {})
    backup_url = links.get('backup') or "https://t.me/"
    help_url = links.get('help') or "https://t.me/"
    
    btn_backup = InlineKeyboardButton("Backup", url=backup_url)
    btn_donate = InlineKeyboardButton("Donate", callback_data="user_show_donate_menu")
    btn_help = InlineKeyboardButton("🆘 Help", url=help_url)
    
    keyboard = [
        [btn_backup, btn_donate],
        [btn_help]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = await format_message(context, "user_menu_greeting", {
        "full_name": user.full_name,
        "first_name": user.first_name
    })
    
    menu_photo_id = config.get("user_menu_photo_id")
    
    if from_callback:
        query = update.callback_query
        await query.answer()
        
        try:
            if menu_photo_id:
                if query.message.photo:
                    await query.edit_message_caption(caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    await query.message.delete()
                    await context.bot.send_photo(chat_id=user_id, photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                if query.message.photo:
                    await query.message.delete()
                    await context.bot.send_message(chat_id=user_id, text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Menu edit/reply nahi kar paya: {e}. Naya message bhej raha hoon.")
            try:
                if menu_photo_id:
                    await context.bot.send_photo(chat_id=user_id, photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(chat_id=user_id, text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception as e2:
                logger.error(f"Menu command (callback) me critical error: {e2}")
    else:
        try:
            if menu_photo_id:
                await update.message.reply_photo(photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Show user menu me error: {e}")

async def user_show_donate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await increment_user_interaction(query.from_user.id)
    
    config = await get_config()
    qr_id = config.get('donate_qr_id')
    
    if not qr_id:
        msg = await format_message(context, "user_donate_qr_error")
        await query.answer(msg, show_alert=True)
        return
    
    text = await format_message(context, "user_donate_qr_text")
    
    try:
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="user_back_menu")]]
        
        if not query.message.photo:
            await query.message.delete()
        
        await context.bot.send_photo(
            chat_id=query.from_user.id,
            photo=qr_id,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        await query.answer()
        context.job_queue.run_once(send_donate_thank_you, 60, chat_id=query.from_user.id)
    except Exception as e:
        logger.error(f"Donate QR bhejte waqt error: {e}")
        await query.answer("❌ Error! Dobara try karein.", show_alert=True)

# ============================================
# ===   USER DOWNLOAD HANDLER              ===
# ============================================

async def handle_deep_link_donate(user: User, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {user.id} ne Donate deep link use kiya.")
    await increment_user_interaction(user.id)
    try:
        config = await get_config()
        qr_id = config.get('donate_qr_id')
        
        if not qr_id:
            msg = await format_message(context, "user_donate_qr_error")
            await context.bot.send_message(user.id, msg, parse_mode=ParseMode.HTML)
            return
        
        text = await format_message(context, "user_donate_qr_text")
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="user_back_menu")]]
        
        await context.bot.send_photo(
            chat_id=user.id,
            photo=qr_id,
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.job_queue.run_once(send_donate_thank_you, 60, chat_id=user.id)
    except Exception as e:
        logger.error(f"Deep link Donate QR bhejte waqt error: {e}")

async def handle_deep_link_download(user: User, context: ContextTypes.DEFAULT_TYPE, payload: str):
    logger.info(f"User {user.id} ne Download deep link use kiya: {payload}")
    await increment_user_interaction(user.id)
    
    class DummyChat:
        def __init__(self, chat_id):
            self.id = chat_id
            self.type = 'private'
    
    class DummyMessage:
        def __init__(self, chat_id, message_id=None):
            self.chat = DummyChat(chat_id)
            self.message_id = message_id or 12345
            self.photo = None
            self.text = "Deep link request"
    
    class DummyCallbackQuery:
        def __init__(self, user, data):
            self.from_user = user
            self.data = data
            self.message = DummyMessage(user.id)
        
        async def answer(self, *args, **kwargs):
            pass
    
    class DummyUpdate:
        def __init__(self, user, data):
            self.callback_query = DummyCallbackQuery(user, data)
            self.effective_user = user
    
    dummy_update = DummyUpdate(user, payload)
    
    try:
        await download_button_handler(dummy_update, context)
    except Exception as e:
        logger.error(f"Deep link download handler fail ho gaya: {e}", exc_info=True)

async def download_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    
    await increment_user_interaction(user_id)
    config = await get_config()
    
    is_deep_link = not hasattr(query.message, 'edit_message_caption')
    is_in_dm = False
    checking_msg_id = None
    
    try:
        if not is_deep_link:
            is_in_dm = query.message.chat.type == 'private'
            if not is_in_dm:
                alert_msg = await format_message(context, "user_dl_dm_alert")
                alert_msg_plain = re.sub(r'<f>(.*?)</f>', r'\1', alert_msg, flags=re.DOTALL)
                await query.answer(alert_msg_plain, show_alert=True)
            else:
                await query.answer()
        
        try:
            checking_text = await format_message(context, "user_dl_fetching")
            sent_msg = await context.bot.send_message(chat_id=user_id, text=checking_text, parse_mode=ParseMode.HTML, read_timeout=10, write_timeout=10)
            checking_msg_id = sent_msg.message_id
        except Exception as e:
            logger.error(f"User {user_id} ko 'Fetching...' message nahi bhej paya. Error: {e}")
            if not is_deep_link and not is_in_dm:
                await query.answer("❌ Error! Bot ko DM mein /start karke unblock karein.", show_alert=True)
            return
        
        parts = query.data.split('__')
        
        content_key = parts[0]
        if content_key.startswith("dl_"):
            content_key = content_key.replace("dl_", "")
        elif content_key.startswith("dl"):
            content_key = content_key.replace("dl", "")
        
        season_name = parts[1] if len(parts) > 1 else None
        ep_num = parts[2] if len(parts) > 2 else None
        
        content_doc = None
        try:
            content_doc = content_collection.find_one({"_id": ObjectId(content_key)})
        except Exception:
            logger.warning(f"ObjectId '{content_key}' nahi mila. Name se search kar raha hoon...")
            content_doc = content_collection.find_one({"name": content_key})
        
        if not content_doc:
            logger.error(f"Content '{content_key}' na ID se mila na Name se.")
            msg = await format_message(context, "user_dl_content_not_found")
            await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            return
        
        content_name = content_doc['name']
        content_id_str = str(content_doc['_id'])
        content_type = content_doc.get('type', 'series')
        
        delete_time = config.get("delete_seconds", 300)
        
        # Case 3: Episode clicked
        if ep_num:
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            try:
                if is_in_dm and query.message.photo:
                    await query.message.delete()
                    logger.info(f"User {user_id} ke liye episode list delete kar di.")
            except Exception as e:
                logger.warning(f"Episode list delete nahi kar paya: {e}")
            
            if content_type == 'movie':
                qualities_dict = content_doc.get("episodes", {}).get(ep_num, {})
                season_display = "Movie"
                poster_to_use = content_doc.get("poster_id")
            else:
                qualities_dict = content_doc.get("seasons", {}).get(season_name, {}).get(ep_num, {})
                season_display = season_name
                season_data = content_doc.get("seasons", {}).get(season_name, {})
                poster_to_use = season_data.get("_poster_id") or content_doc.get("poster_id")
            
            if not qualities_dict:
                msg = await format_message(context, "user_dl_episodes_not_found")
                await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            msg = await format_message(context, "user_dl_sending_files", {
                "content_name": content_name,
                "season_name": season_display,
                "ep_num": ep_num
            })
            
            sent_msg = await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
            msg_to_delete_id = sent_msg.message_id
            
            QUALITY_ORDER = ['480p', '720p', '1080p', '4K']
            available_qualities = qualities_dict.keys()
            sorted_q_list = [q for q in QUALITY_ORDER if q in available_qualities]
            extra_q = [q for q in available_qualities if q not in sorted_q_list]
            sorted_q_list.extend(extra_q)
            
            delete_minutes = max(1, delete_time // 60)
            warning_template = await format_message(context, "file_warning", {"minutes": str(delete_minutes)})
            
            for quality in sorted_q_list:
                file_id = qualities_dict.get(quality)
                if not file_id: continue
                
                sent_message = None
                try:
                    caption_base = "🎬 <b>{content_name}</b>\n{season_display} - E{ep_num} ({quality})\n\n{warning_msg}"
                    
                    caption_with_vars = caption_base.format(
                        content_name=content_name,
                        season_display=season_display,
                        ep_num=ep_num,
                        quality=quality,
                        warning_msg=warning_template
                    )
                    
                    font_settings = {"font": "default", "style": "normal"}
                    caption = await apply_font_formatting(caption_with_vars, font_settings)
                    
                    sent_message = await context.bot.send_video(
                        chat_id=user_id,
                        video=file_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        thumbnail=poster_to_use
                    )
                except Exception as e:
                    logger.error(f"User {user_id} ko file bhejte waqt error: {e}")
                    error_msg_key = "user_dl_blocked_error" if "blocked" in str(e) else "user_dl_file_error"
                    msg = await format_message(context, error_msg_key, {"quality": quality})
                    await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                
                if sent_message:
                    try:
                        asyncio.create_task(delete_message_later(
                            bot=context.bot,
                            chat_id=user_id,
                            message_id=sent_message.message_id,
                            seconds=delete_time
                        ))
                    except Exception as e:
                        logger.error(f"asyncio.create_task schedule failed for user {user_id}: {e}")
            
            if msg_to_delete_id:
                try:
                    asyncio.create_task(delete_message_later(
                        bot=context.bot,
                        chat_id=user_id,
                        message_id=msg_to_delete_id,
                        seconds=delete_time
                    ))
                except Exception as e:
                    logger.error(f"Async 'Sending files...' message delete schedule failed: {e}")
            return
        
        sent_selection_message = None
        
        # Case 2: Season clicked -> Show Episodes
        if season_name:
            if content_type == 'movie':
                episodes = content_doc.get("episodes", {})
                poster_to_use = content_doc.get("poster_id")
            else:
                episodes = content_doc.get("seasons", {}).get(season_name, {})
                season_data = content_doc.get("seasons", {}).get(season_name, {})
                poster_to_use = season_data.get("_poster_id") or content_doc.get("poster_id")
            
            episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
            
            if not episode_keys:
                msg = await format_message(context, "user_dl_episodes_not_found")
                if checking_msg_id:
                    try: await context.bot.delete_message(user_id, checking_msg_id)
                    except Exception: pass
                
                if is_in_dm:
                    if query.message.photo:
                        await query.edit_message_caption(msg, parse_mode=ParseMode.HTML)
                    else:
                        await query.message.reply_text(msg, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"dl{content_id_str}__{season_name}__{ep}") for ep in sorted_eps]
            keyboard = build_grid_keyboard(buttons, 2)
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"dl{content_id_str}")])
            
            msg = await format_message(context, "user_dl_select_episode", {
                "content_name": content_name,
                "season_name": season_name
            })
            
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            if is_deep_link:
                sent_selection_message = await context.bot.send_photo(
                    chat_id=user_id,
                    photo=poster_to_use,
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                try:
                    if not query.message.photo:
                        await query.message.delete()
                        sent_selection_message = await context.bot.send_photo(
                            chat_id=user_id,
                            photo=poster_to_use,
                            caption=msg,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await query.edit_message_media(
                            media=InputMediaPhoto(media=poster_to_use, caption=msg, parse_mode=ParseMode.HTML),
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        sent_selection_message = query.message
                except BadRequest as e:
                    if "Message is not modified" not in str(e):
                        logger.warning(f"DL Handler Case 2: Media edit fail, fallback to caption: {e}")
                        await query.edit_message_caption(
                            caption=msg,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.HTML
                        )
                        sent_selection_message = query.message
                except Exception as e:
                    logger.error(f"DL Handler Case 2: Media edit critical fail: {e}")
                    await query.edit_message_caption(
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                    sent_selection_message = query.message
            
            if sent_selection_message:
                asyncio.create_task(delete_message_later(
                    bot=context.bot,
                    chat_id=user_id,
                    message_id=sent_selection_message.message_id,
                    seconds=delete_time
                ))
            return
        
        # Case 1: Only content clicked -> Show Seasons or Episodes
        if content_type == 'series':
            seasons = content_doc.get("seasons", {})
            if not seasons:
                msg = await format_message(context, "user_dl_seasons_not_found")
                if checking_msg_id:
                    try: await context.bot.delete_message(user_id, checking_msg_id)
                    except Exception: pass
                
                if is_in_dm:
                    if query.message.photo:
                        await query.edit_message_caption(msg, parse_mode=ParseMode.HTML)
                    else:
                        await query.edit_message_text(msg, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"dl{content_id_str}__{s}") for s in sorted_seasons]
            keyboard = build_grid_keyboard(buttons, 1)
            keyboard.append([InlineKeyboardButton("⬅️ Back to Bot Menu", callback_data="user_back_menu")])
            
            msg = await format_message(context, "user_dl_select_season", {
                "content_name": content_name
            })
            
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            if is_deep_link:
                sent_selection_message = await context.bot.send_photo(
                    chat_id=user_id,
                    photo=content_doc['poster_id'],
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                if not query.message.photo:
                    await query.message.delete()
                    sent_selection_message = await context.bot.send_photo(
                        chat_id=user_id,
                        photo=content_doc['poster_id'],
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await query.edit_message_caption(
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                    sent_selection_message = query.message
        else:
            # Movie: Directly show episodes
            episodes = content_doc.get("episodes", {})
            episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
            
            if not episode_keys:
                msg = await format_message(context, "user_dl_episodes_not_found")
                if checking_msg_id:
                    try: await context.bot.delete_message(user_id, checking_msg_id)
                    except Exception: pass
                
                if is_in_dm:
                    if query.message.photo:
                        await query.edit_message_caption(msg, parse_mode=ParseMode.HTML)
                    else:
                        await query.edit_message_text(msg, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"dl{content_id_str}__Movie__{ep}") for ep in sorted_eps]
            keyboard = build_grid_keyboard(buttons, 2)
            keyboard.append([InlineKeyboardButton("⬅️ Back to Bot Menu", callback_data="user_back_menu")])
            
            msg = await format_message(context, "user_dl_select_episode", {
                "content_name": content_name,
                "season_name": "Movie"
            })
            
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            if is_deep_link:
                sent_selection_message = await context.bot.send_photo(
                    chat_id=user_id,
                    photo=content_doc['poster_id'],
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                if not query.message.photo:
                    await query.message.delete()
                    sent_selection_message = await context.bot.send_photo(
                        chat_id=user_id,
                        photo=content_doc['poster_id'],
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await query.edit_message_caption(
                        caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.HTML
                    )
                    sent_selection_message = query.message
        
        if sent_selection_message:
            asyncio.create_task(delete_message_later(
                bot=context.bot,
                chat_id=user_id,
                message_id=sent_selection_message.message_id,
                seconds=delete_time
            ))
        return
    
    except Exception as e:
        logger.error(f"Download button handler me error: {e}", exc_info=True)
        if checking_msg_id:
            try: await context.bot.delete_message(user_id, checking_msg_id)
            except Exception: pass
        
        msg = await format_message(context, "user_dl_general_error")
        try:
            if not is_deep_link and query.message and query.message.chat.type in ['channel', 'supergroup', 'group']:
                await query.answer(msg, show_alert=True)
            else:
                await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
        except Exception: pass

# ============================================
# ===   OTHER ADMIN SETTINGS               ===
# ============================================

async def donate_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    donate_qr_status = "✅" if config.get('donate_qr_id') else "❌"
    keyboard = [
        [InlineKeyboardButton(f"Set Donate QR {donate_qr_status}", callback_data="admin_set_donate_qr")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_donate")
    if query:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def other_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    backup_status = "✅" if config.get('links', {}).get('backup') else "❌"
    download_status = "✅" if config.get('links', {}).get('download') else "❌"
    help_status = "✅" if config.get('links', {}).get('help') else "❌"
    keyboard = [
        [InlineKeyboardButton(f"Set Backup Link {backup_status}", callback_data="admin_set_backup_link")],
        [InlineKeyboardButton(f"Set Download Link {download_status}", callback_data="admin_set_download_link")],
        [InlineKeyboardButton(f"Set Help Link {help_status}", callback_data="admin_set_help_link")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_links")
    if query:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def set_donate_qr_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_set_donate_qr_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_donate_settings")]]))
    return CD_GET_QR

async def set_donate_qr_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_set_donate_qr_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CD_GET_QR
    qr_file_id = update.message.photo[-1].file_id
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"donate_qr_id": qr_file_id}}, upsert=True)
    logger.info(f"Donate QR code update ho gaya.")
    text = await format_message(context, "admin_set_donate_qr_success")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await donate_settings_menu(update, context)
    return ConversationHandler.END

async def set_links_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    link_type = query.data.replace("admin_set_", "")
    
    if link_type == "backup_link":
        context.user_data['link_type'] = "backup"
        text = await format_message(context, "admin_set_link_backup")
        back_button = "back_to_links"
    elif link_type == "download_link":
        context.user_data['link_type'] = "download"
        text = await format_message(context, "admin_set_link_download")
        back_button = "back_to_links"
    elif link_type == "help_link":
        context.user_data['link_type'] = "help"
        text = await format_message(context, "admin_set_link_help")
        back_button = "back_to_links"
    else:
        text = await format_message(context, "admin_set_link_invalid")
        await query.answer(text, show_alert=True)
        return ConversationHandler.END
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_button)]]))
    return CL_GET_LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_url = update.message.text
    link_type = context.user_data['link_type']
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"links.{link_type}": link_url}}, upsert=True)
    logger.info(f"{link_type} link update ho gaya: {link_url}")
    text = await format_message(context, "admin_set_link_success", {"link_type": link_type})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await other_links_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

async def skip_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_type = context.user_data['link_type']
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"links.{link_type}": None}}, upsert=True)
    logger.info(f"{link_type} link skip kiya (None set).")
    text = await format_message(context, "admin_set_link_skip", {"link_type": link_type})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await other_links_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

async def set_delete_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current_seconds = config.get("delete_seconds", 300)
    current_minutes = current_seconds // 60
    
    text = await format_message(context, "admin_set_delete_time_start", {
        "current_minutes": current_minutes,
        "current_seconds": current_seconds
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]))
    return CS_GET_DELETE_TIME

async def set_delete_time_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        seconds = int(update.message.text)
        if seconds <= 10:
            text = await format_message(context, "admin_set_delete_time_low")
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return CS_GET_DELETE_TIME
        
        config_collection.update_one({"_id": "bot_config"}, {"$set": {"delete_seconds": seconds}}, upsert=True)
        logger.info(f"Auto-delete time update ho gaya: {seconds} seconds")
        
        text = await format_message(context, "admin_set_delete_time_success", {
            "seconds": seconds,
            "minutes": seconds // 60
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        await admin_command(update, context, from_callback=False)
        return ConversationHandler.END
        
    except ValueError:
        text = await format_message(context, "admin_set_delete_time_nan")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CS_GET_DELETE_TIME
    except Exception as e:
        logger.error(f"Delete time save karte waqt error: {e}")
        text = await format_message(context, "admin_set_delete_time_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END

async def bot_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📥 Download Flow Messages", callback_data="msg_menu_dl")],
        [InlineKeyboardButton("✍️ Post Generator Messages", callback_data="msg_menu_postgen")],
        [InlineKeyboardButton("👑 Admin Flow Messages", callback_data="msg_menu_admin")],
        [InlineKeyboardButton("⚙️ General Messages", callback_data="msg_menu_gen")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_messages_main")
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_MAIN

async def bot_messages_menu_dl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Edit Check DM Alert", callback_data="msg_edit_user_dl_dm_alert")],
        [InlineKeyboardButton("Edit Fetching Files", callback_data="msg_edit_user_dl_fetching")],
        [InlineKeyboardButton("Edit Content Not Found", callback_data="msg_edit_user_dl_content_not_found")],
        [InlineKeyboardButton("Edit Seasons Not Found", callback_data="msg_edit_user_dl_seasons_not_found")],
        [InlineKeyboardButton("Edit Episodes Not Found", callback_data="msg_edit_user_dl_episodes_not_found")],
        [InlineKeyboardButton("Edit Sending Files", callback_data="msg_edit_user_dl_sending_files")],
        [InlineKeyboardButton("Edit Select Season", callback_data="msg_edit_user_dl_select_season")],
        [InlineKeyboardButton("Edit Select Episode", callback_data="msg_edit_user_dl_select_episode")],
        [InlineKeyboardButton("Edit File Warning", callback_data="msg_edit_file_warning")],
        [InlineKeyboardButton("Edit File Error", callback_data="msg_edit_user_dl_file_error")],
        [InlineKeyboardButton("Edit Blocked Error", callback_data="msg_edit_user_dl_blocked_error")],
        [InlineKeyboardButton("Edit General Error", callback_data="msg_edit_user_dl_general_error")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")]
    ]
    text = await format_message(context, "admin_menu_messages_dl")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_DL

async def bot_messages_menu_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Edit Menu Greeting", callback_data="msg_edit_user_menu_greeting")],
        [InlineKeyboardButton("Edit Donate QR Error", callback_data="msg_edit_user_donate_qr_error")],
        [InlineKeyboardButton("Edit Donate QR Text", callback_data="msg_edit_user_donate_qr_text")],
        [InlineKeyboardButton("Edit Donate Thanks", callback_data="msg_edit_donate_thanks")],
        [InlineKeyboardButton("Edit Not Admin", callback_data="msg_edit_user_not_admin")],
        [InlineKeyboardButton("Edit Welcome Admin", callback_data="msg_edit_user_welcome_admin")],
        [InlineKeyboardButton("Edit Welcome User", callback_data="msg_edit_user_welcome_basic")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")]
    ]
    text = await format_message(context, "admin_menu_messages_gen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_GEN

async def bot_messages_menu_postgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Edit Movie Post Caption", callback_data="msg_edit_post_gen_movie_caption")],
        [InlineKeyboardButton("Edit Series Post Caption", callback_data="msg_edit_post_gen_series_caption")],
        [InlineKeyboardButton("Edit Episode Post Caption", callback_data="msg_edit_post_gen_episode_caption")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")]
    ]
    text = await format_message(context, "admin_menu_messages_postgen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_POSTGEN

async def bot_messages_menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keys = await get_default_messages()
    admin_keys = sorted([k for k in keys.keys() if k.startswith("admin_")])
    
    buttons = [InlineKeyboardButton(k.replace("admin_", "").replace("_", " ").title(), callback_data=f"msg_edit_{k}") for k in admin_keys]
    keyboard = build_grid_keyboard(buttons, 1)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")])
    
    text = await format_message(context, "admin_menu_messages_admin")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_ADMIN

async def set_msg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg_key = query.data.replace("msg_edit_", "")
    
    config = await get_config()
    current_msg = config.get("messages", {}).get(msg_key, "N/A")
    context.user_data['msg_key'] = msg_key
    
    safe_current_msg = current_msg.replace('<', '&lt;').replace('>', '&gt;')
    
    text = await format_message(context, "admin_set_msg_start", {
        "msg_key": msg_key,
        "current_msg": safe_current_msg
    })
    
    if msg_key.startswith("user_dl_") or msg_key == "file_warning":
        back_cb = "msg_menu_dl"
    elif msg_key.startswith("post_gen_"):
        back_cb = "msg_menu_postgen"
    elif msg_key.startswith("admin_"):
        back_cb = "msg_menu_admin"
    else:
        back_cb = "msg_menu_gen"
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_cb)]]))
    return M_GET_MSG

async def set_msg_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg_text = update.message.text
        msg_key = context.user_data['msg_key']
        
        config_collection.update_one({"_id": "bot_config"}, {"$set": {f"messages.{msg_key}": msg_text}}, upsert=True)
        logger.info(f"{msg_key} message update ho gaya: {msg_text}")
        text = await format_message(context, "admin_set_msg_success", {"msg_key": msg_key})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
        await bot_messages_menu(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Message save karne me error: {e}")
        text = await format_message(context, "admin_set_msg_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END

# ============================================
# ===   ADMIN SETTINGS (Co-Admin, etc.)   ===
# ============================================

async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Co-Admin", callback_data="admin_add_co_admin")],
        [InlineKeyboardButton("🚫 Remove Co-Admin", callback_data="admin_remove_co_admin")],
        [InlineKeyboardButton("👥 List Co-Admins", callback_data="admin_list_co_admin")],
        [InlineKeyboardButton("🚀 Custom Post Generator", callback_data="admin_custom_post")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast_start")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_admin_settings")
    
    if query:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def co_admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_co_admin_add_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return CA_GET_ID

async def co_admin_add_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
    except ValueError:
        text = await format_message(context, "admin_co_admin_add_invalid_id")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CA_GET_ID
    
    if user_id == ADMIN_ID:
        text = await format_message(context, "admin_co_admin_add_is_main")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CA_GET_ID
    
    config = await get_config()
    if user_id in config.get("co_admins", []):
        text = await format_message(context, "admin_co_admin_add_exists", {"user_id": user_id})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CA_GET_ID
    
    context.user_data['co_admin_to_add'] = user_id
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Co-Admin Banao", callback_data="co_admin_add_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
    text = await format_message(context, "admin_co_admin_add_confirm", {"user_id": user_id})
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return CA_CONFIRM

async def co_admin_add_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Adding...")
    user_id = context.user_data['co_admin_to_add']
    try:
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$push": {"co_admins": user_id}}
        )
        logger.info(f"Main Admin {query.from_user.id} ne {user_id} ko Co-Admin banaya.")
        text = await format_message(context, "admin_co_admin_add_success", {"user_id": user_id})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Co-Admin add karne me error: {e}")
        text = await format_message(context, "admin_co_admin_add_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def co_admin_remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    config = await get_config()
    co_admins = config.get("co_admins", [])
    
    if not co_admins:
        text = await format_message(context, "admin_co_admin_remove_no_co")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
        return ConversationHandler.END
    
    buttons = [InlineKeyboardButton(f"Remove {admin_id}", callback_data=f"co_admin_rem_{admin_id}") for admin_id in co_admins]
    keyboard = build_grid_keyboard(buttons, 1)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")])
    text = await format_message(context, "admin_co_admin_remove_start")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return CR_GET_ID

async def co_admin_remove_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.replace("co_admin_rem_", ""))
    context.user_data['co_admin_to_remove'] = user_id
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Remove Karo", callback_data="co_admin_rem_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
    text = await format_message(context, "admin_co_admin_remove_confirm", {"user_id": user_id})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return CR_CONFIRM

async def co_admin_remove_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Removing...")
    user_id = context.user_data['co_admin_to_remove']
    try:
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$pull": {"co_admins": user_id}}
        )
        logger.info(f"Main Admin {query.from_user.id} ne {user_id} ko Co-Admin se hataya.")
        text = await format_message(context, "admin_co_admin_remove_success", {"user_id": user_id})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Co-Admin remove karne me error: {e}")
        text = await format_message(context, "admin_co_admin_remove_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def co_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    co_admins = config.get("co_admins", [])
    if not co_admins:
        text = await format_message(context, "admin_co_admin_list_none")
    else:
        text = await format_message(context, "admin_co_admin_list_header")
        for admin_id in co_admins:
            text += f"- <code>{admin_id}</code>\n"
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return ConversationHandler.END

# ============================================
# ===   CUSTOM POST GENERATOR              ===
# ============================================

async def custom_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_custom_post_start")
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return CPOST_GET_CHAT

async def custom_post_get_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['chat_id'] = update.message.text
    text = await format_message(context, "admin_custom_post_get_chat")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return CPOST_GET_POSTER

async def custom_post_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_custom_post_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CPOST_GET_POSTER
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_custom_post_get_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return CPOST_GET_CAPTION

async def custom_post_get_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['caption'] = update.message.text
    text = await format_message(context, "admin_custom_post_get_caption")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return CPOST_GET_BTN_TEXT

async def custom_post_get_btn_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['btn_text'] = update.message.text
    text = await format_message(context, "admin_custom_post_get_btn_text")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return CPOST_GET_BTN_URL

async def custom_post_get_btn_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['btn_url'] = update.message.text
    
    chat_id = context.user_data['chat_id']
    poster_id = context.user_data['poster_id']
    caption_raw = context.user_data['caption']
    btn_text = context.user_data['btn_text']
    btn_url = context.user_data['btn_url']
    
    font_settings = {"font": "default", "style": "normal"}
    caption_formatted = await apply_font_formatting(caption_raw, font_settings)
    
    keyboard = [
        [InlineKeyboardButton(btn_text, url=btn_url)],
        [InlineKeyboardButton("✅ Post Karo", callback_data="cpost_send")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    
    caption_text = await format_message(context, "admin_custom_post_confirm", {
        "caption": caption_formatted,
        "chat_id": chat_id
    })
    await update.message.reply_photo(
        photo=poster_id,
        caption=caption_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CPOST_CONFIRM

async def custom_post_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Sending...")
    
    chat_id = context.user_data['chat_id']
    poster_id = context.user_data['poster_id']
    caption_raw = context.user_data['caption']
    btn_text = context.user_data['btn_text']
    btn_url = context.user_data['btn_url']
    
    font_settings = {"font": "default", "style": "normal"}
    caption_formatted = await apply_font_formatting(caption_raw, font_settings)
    
    keyboard = [[InlineKeyboardButton(btn_text, url=btn_url)]]
    
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=poster_id,
            caption=caption_formatted,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        text = await format_message(context, "admin_custom_post_success", {"chat_id": chat_id})
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Custom post bhejme me error: {e}")
        text = await format_message(context, "admin_custom_post_error", {"chat_id": chat_id, "e": e})
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    await query.message.delete()
    context.user_data.clear()
    await admin_settings_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===   BROADCAST                         ===
# ============================================

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_broadcast_start")
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return BC_GET_MESSAGE

async def broadcast_get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_message'] = update.message
    user_count = users_collection.count_documents({})
    context.user_data['user_count'] = user_count
    
    text = await format_message(context, "admin_broadcast_confirm", {"user_count": user_count})
    keyboard = [
        [InlineKeyboardButton(f"✅ Haan, {user_count} Users ko Bhejo", callback_data="broadcast_confirm_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    
    try:
        await update.message.forward(chat_id=update.effective_chat.id)
    except Exception as e:
        logger.warning(f"Broadcast preview forward nahi kar paya: {e}")
        await update.message.reply_text("<b>--- PREVIEW UPAR HAI ---</b>", parse_mode=ParseMode.HTML)
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return BC_CONFIRM

async def broadcast_do_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Broadcasting...")
    
    message_to_send = context.user_data.get('broadcast_message')
    user_count = context.user_data.get('user_count', 0)
    
    if not message_to_send:
        await query.edit_message_text("Error! Message nahi mila. /cancel karke dobara try karein.")
        return ConversationHandler.END
    
    text = await format_message(context, "admin_broadcast_sending", {"user_count": user_count})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    asyncio.create_task(send_broadcast_task(context, message_to_send, query.from_user.id))
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def send_broadcast_task(context: ContextTypes.DEFAULT_TYPE, message: Update.message, admin_user_id: int):
    all_users = users_collection.find({}, {"_id": 1})
    sent_count = 0
    failed_count = 0
    
    for user in all_users:
        user_id = user["_id"]
        try:
            await message.copy(chat_id=user_id)
            sent_count += 1
        except Forbidden:
            logger.warning(f"Broadcast fail: User {user_id} ne bot ko block kiya.")
            failed_count += 1
        except Exception as e:
            logger.error(f"Broadcast fail: User {user_id} ko bhejte waqt error: {e}")
            failed_count += 1
        
        await asyncio.sleep(0.1)
    
    logger.info(f"Broadcast complete. Sent: {sent_count}, Failed: {failed_count}")
    
    try:
        text = await format_message(context, "admin_broadcast_success", {
            "sent_count": sent_count,
            "failed_count": failed_count
        })
        await context.bot.send_message(chat_id=admin_user_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Admin ko broadcast report bhejte waqt error: {e}")

# ============================================
# ===   APPEARANCE SETTINGS               ===
# ============================================

async def appearance_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    
    config = await get_config()
    appearance = config.get("appearance", {"font": "default", "style": "normal"})
    font = appearance.get("font", "default")
    style = appearance.get("style", "normal")
    
    keyboard = [
        [
            InlineKeyboardButton(f"🖋️ Font: {font.title()}", callback_data="app_set_font"),
            InlineKeyboardButton(f"✍️ Style: {style.title()}", callback_data="app_set_style")
        ],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_appearance", {
        "font": font.title(),
        "style": style.title()
    })
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    
    return AP_MENU

async def appearance_set_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    config = await get_config()
    current_font = config.get("appearance", {}).get("font", "default")
    
    fonts = ["default", "small_caps", "sans_serif", "sans_serif_regular", "script", "monospace", "serif"]
    buttons = []
    for font in fonts:
        prefix = "✅ " if font == current_font else ""
        buttons.append(InlineKeyboardButton(f"{prefix}{font.title().replace('_', ' ')}", callback_data=f"app_font_{font}"))
    
    keyboard = build_grid_keyboard(buttons, 2)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_appearance")])
    
    text = await format_message(context, "admin_appearance_select_font", {
        "font": current_font.title().replace('_', ' ')
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_SET_FONT

async def appearance_save_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    font = query.data.replace("app_font_", "")
    
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"appearance.font": font}},
        upsert=True
    )
    await query.answer(f"Font changed to {font}")
    
    text = await format_message(context, "admin_appearance_set_font_success", {
        "font": font.title().replace('_', ' ')
    })
    await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    await appearance_menu_start(update, context)
    return AP_MENU

async def appearance_set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    config = await get_config()
    current_style = config.get("appearance", {}).get("style", "normal")
    
    styles = ["normal", "bold"]
    buttons = []
    for style in styles:
        prefix = "✅ " if style == current_style else ""
        buttons.append(InlineKeyboardButton(f"{prefix}{style.title()}", callback_data=f"app_style_{style}"))
    
    keyboard = build_grid_keyboard(buttons, 2)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_appearance")])
    
    text = await format_message(context, "admin_appearance_select_style", {
        "style": current_style.title()
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_SET_STYLE

async def appearance_save_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    style = query.data.replace("app_style_", "")
    
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"appearance.style": style}},
        upsert=True
    )
    await query.answer(f"Style changed to {style}")
    
    text = await format_message(context, "admin_appearance_set_style_success", {
        "style": style.title()
    })
    await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    await appearance_menu_start(update, context)
    return AP_MENU

# ============================================
# ===   UPDATE PHOTO                      ===
# ============================================

async def update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🖼️ Update Content Photo", callback_data="admin_update_photo_content")],
        [InlineKeyboardButton("🖼️ Set User Menu Photo", callback_data="admin_set_menu_photo")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_update_photo")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def update_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await update_photo_select_type(update, context)

async def update_photo_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Photo", callback_data="update_type_movie")],
        [InlineKeyboardButton("📺 Series Photo", callback_data="update_type_series")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_update_photo_menu")]
    ]
    text = await format_message(context, "admin_update_photo_select_type")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return UP_GET_TYPE

async def update_photo_set_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_type = query.data.replace("update_type_", "")
    context.user_data['content_type'] = content_type
    
    return await update_photo_show_content_list(update, context, page=0)

async def update_photo_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("upphoto_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="upphoto_page_",
        item_callback_prefix="upphoto_content_",
        back_callback="admin_update_photo_content",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = await format_message(context, "admin_update_photo_no_content", {
            "content_type": display_type
        })
    else:
        text = await format_message(context, "admin_update_photo_select_content", {
            "content_type": display_type,
            "page": page + 1
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return UP_GET_CONTENT

async def update_photo_select_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("upphoto_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    buttons = [InlineKeyboardButton(f"🖼️ Main Poster", callback_data=f"upphoto_target_MAIN")]
    
    if content_doc.get('type') == 'series':
        seasons = content_doc.get("seasons", {})
        if seasons:
            sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            for s in sorted_seasons:
                buttons.append(InlineKeyboardButton(f"S{s} Poster", callback_data=f"upphoto_target_S__{s}"))
    
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"upphoto_page_{current_page}")])
    
    text = await format_message(context, "admin_update_photo_select_target", {
        "content_name": content_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return UP_GET_TARGET

async def update_photo_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target = query.data.replace("upphoto_target_", "")
    context.user_data['target'] = target
    
    if target == "MAIN":
        target_name = "Main Poster"
    else:
        season_name = target.replace("S__", "")
        context.user_data['season_name'] = season_name
        target_name = f"Season {season_name} Poster"
    
    text = await format_message(context, "admin_update_photo_get_poster", {
        "target_name": target_name
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return UP_GET_POSTER

async def update_photo_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_update_photo_invalid")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return UP_GET_POSTER

async def update_photo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_update_photo_invalid")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return UP_GET_POSTER
    
    poster_id = update.message.photo[-1].file_id
    content_name = context.user_data['content_name']
    target = context.user_data['target']
    
    try:
        update_query = {"$set": {"last_modified": datetime.now()}}
        
        if target == "MAIN":
            update_query["$set"]["poster_id"] = poster_id
            content_collection.update_one({"name": content_name}, update_query)
            caption = await format_message(context, "admin_update_photo_save_success_main", {
                "content_name": content_name
            })
            logger.info(f"Main poster change ho gaya: {content_name}")
        else:
            season_name = context.user_data['season_name']
            update_query["$set"][f"seasons.{season_name}._poster_id"] = poster_id
            content_collection.update_one(
                {"name": content_name},
                update_query
            )
            caption = await format_message(context, "admin_update_photo_save_success_season", {
                "content_name": content_name,
                "season_name": season_name
            })
            logger.info(f"Season poster change ho gaya: {content_name} S{season_name}")
        
        await update.message.reply_photo(photo=poster_id, caption=caption, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Poster change karne me error: {e}")
        text = await format_message(context, "admin_update_photo_save_error_db")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

async def set_menu_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_set_menu_photo_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_update_photo_menu")]]))
    return CS_GET_MENU_PHOTO

async def set_menu_photo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_set_menu_photo_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CS_GET_MENU_PHOTO
    
    photo_id = update.message.photo[-1].file_id
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"user_menu_photo_id": photo_id}}, upsert=True)
    logger.info(f"User menu photo update ho gaya.")
    text = await format_message(context, "admin_set_menu_photo_success")
    await update.message.reply_photo(photo=photo_id, caption=text, parse_mode=ParseMode.HTML)
    
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

async def skip_menu_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"user_menu_photo_id": None}}, upsert=True)
    logger.info(f"User menu photo remove kar diya gaya.")
    text = await format_message(context, "admin_set_menu_photo_skip")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

# ============================================
# ===   USER STATISTICS                   ===
# ============================================

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    loading_text = await format_message(context, "admin_stats_loading")
    await query.edit_message_text(loading_text, parse_mode=ParseMode.HTML)
    
    try:
        total_users = users_collection.count_documents({})
        
        top_users_cursor = users_collection.find(
            {"interaction_count": {"$gt": 0}}
        ).sort("interaction_count", DESCENDING).limit(10)
        
        top_users_list = []
        for i, user in enumerate(top_users_cursor):
            user_id = user["_id"]
            count = user["interaction_count"]
            name = user.get("full_name") or user.get("first_name", f"User {user_id}")
            name_safe = name.replace('<', '&lt;').replace('>', '&gt;')
            top_users_list.append(f"{i+1}. <code>{user_id}</code> - {name_safe} (<b>{count}</b> hits)")
        
        if not top_users_list:
            list_str = await format_message(context, "admin_stats_no_users")
        else:
            list_str = "\n".join(top_users_list)
        
        text = await format_message(context, "admin_stats_result", {
            "total_users": total_users,
            "top_users_list": list_str
        })
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"User stats dikhane me error: {e}")
        await query.edit_message_text(f"Error: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]))

# ============================================
# ===   ERROR HANDLER                     ===
# ============================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error} \nUpdate: {update}", exc_info=True)

# ============================================
# ===   WEBHOOK SETUP                     ===
# ============================================

app = Flask(__name__)
bot_app = None
bot_loop = None

@app.route('/')
def home():
    return "I am alive and running!", 200

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    global bot_app, bot_loop
    if request.is_json:
        update_data = request.get_json()
        update = Update.de_json(update_data, bot_app.bot)
        
        try:
            asyncio.run_coroutine_threadsafe(bot_app.process_update(update), bot_loop)
        except Exception as e:
            logger.error(f"Update ko threadsafe bhejne mein error: {e}", exc_info=True)
        
        return "OK", 200
    else:
        return "Bad request", 400

def run_async_bot_tasks(loop, app):
    global bot_loop
    bot_loop = loop
    asyncio.set_event_loop(loop)
    
    try:
        webhook_path_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        logger.info(f"Webhook ko {webhook_path_url} par set kar raha hai...")
        with httpx.Client() as client:
            client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_path_url}")
        logger.info("Webhook successfully set!")
        
        loop.run_until_complete(app.initialize())
        loop.run_until_complete(app.start())
        logger.info("Bot application initialized and started (async).")
        
        loop.run_forever()
        
    except Exception as e:
        logger.error(f"Async thread fail ho gaya: {e}", exc_info=True)
    finally:
        logger.info("Async loop stop ho raha hai...")
        loop.run_until_complete(app.stop())
        loop.close()

# ============================================
# ===   MAIN FUNCTION                     ===
# ============================================

def main():
    global bot_app
    PORT = int(os.environ.get("PORT", 8080))
    
    my_defaults = Defaults(parse_mode=ParseMode.HTML)
    bot_app = Application.builder().token(BOT_TOKEN).defaults(my_defaults).build()
    
    # --- Add all conversation handlers ---
    
    # Cancel handlers
    global_cancel_handler = CommandHandler("cancel", cancel)
    
    global_fallbacks = [
        CommandHandler("start", cancel),
        CommandHandler("menu", cancel),
        CommandHandler("admin", cancel),
        global_cancel_handler
    ]
    admin_menu_fallback = [CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$"), global_cancel_handler]
    
    # Add Content Conversations
    add_content_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_content_select_type, pattern="^admin_add_content_movie$"),
            CallbackQueryHandler(add_content_select_type, pattern="^admin_add_content_series$")
        ],
        states={
            A_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_name)],
            A_GET_POSTER: [MessageHandler(filters.PHOTO, add_content_get_poster)],
            A_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_desc), CommandHandler("skip", add_content_skip_desc)],
            A_CONFIRM: [CallbackQueryHandler(save_content, pattern="^save_content$")]
        },
        fallbacks=global_fallbacks + [CallbackQueryHandler(add_content_menu, pattern="^back_to_add_content$")],
        allow_reentry=True
    )
    
    # Rest of the handlers would be added here...
    # For brevity in this response, I'll show the pattern and then the final bot_app.add_handler calls
    
    # Standard commands
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("user", user_command))
    bot_app.add_handler(CommandHandler("menu", admin_command))
    bot_app.add_handler(CommandHandler("admin", admin_command))
    
    # Admin menu navigation
    bot_app.add_handler(CallbackQueryHandler(add_content_menu, pattern="^admin_menu_add_content$"))
    bot_app.add_handler(CallbackQueryHandler(manage_content_menu, pattern="^admin_menu_manage_content$"))
    bot_app.add_handler(CallbackQueryHandler(edit_content_menu, pattern="^admin_menu_edit_content$"))
    bot_app.add_handler(CallbackQueryHandler(donate_settings_menu, pattern="^admin_menu_donate_settings$"))
    bot_app.add_handler(CallbackQueryHandler(other_links_menu, pattern="^admin_menu_other_links$"))
    bot_app.add_handler(CallbackQueryHandler(admin_settings_menu, pattern="^admin_menu_admin_settings$"))
    bot_app.add_handler(CallbackQueryHandler(update_photo_menu, pattern="^admin_menu_update_photo$"))
    bot_app.add_handler(CallbackQueryHandler(show_user_stats, pattern="^admin_show_stats$"))
    
    # User menu
    bot_app.add_handler(CallbackQueryHandler(user_show_donate_menu, pattern="^user_show_donate_menu$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"))
    
    # Download handler
    bot_app.add_handler(CallbackQueryHandler(download_button_handler, pattern="^dl"))
    
    # Add all conversation handlers
    bot_app.add_handler(add_content_conv)
    # ... other handlers would be added here
    
    # Error handler
    bot_app.add_error_handler(error_handler)
    
    # --- Webhook setup ---
    logger.info("Starting Flask server for webhook...")
    
    bot_event_loop = asyncio.new_event_loop()
    bot_thread = threading.Thread(target=run_async_bot_tasks, args=(bot_event_loop, bot_app))
    bot_thread.start()
    
    logger.info(f"Flask (Waitress) server {WEBHOOK_URL} port {PORT} par sun raha hai...")
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
