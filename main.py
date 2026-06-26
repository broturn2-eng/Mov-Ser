# ============================================
# ===       WORKING BOT (v37)              ===
# ===       MOVIES & SERIES SUPPORT         ===
# ===  (Based on original working anime bot) ===
# ============================================
import os
import logging
import re
import asyncio
import threading
import httpx
from datetime import datetime
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

# ============================================
# ===        FONT MANAGER                  ===
# ============================================
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

# ============================================
# ===        BOT SETUP                     ===
# ============================================
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

# ============================================
# ===        DATABASE CONNECTION           ===
# ============================================
try:
    logger.info("MongoDB se connect karne ki koshish...")
    client = MongoClient(MONGO_URI)
    db = client['MovieBotDB']
    users_collection = db['users']
    content_collection = db['content']
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

# ============================================
# ===        ADMIN CHECKS                  ===
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
            {"$inc": {"interaction_count": 1}}
        )
    except Exception as e:
        logger.error(f"User {user_id} ka interaction_count update karne me error: {e}")

# ============================================
# ===        BACK/CALLBACK FUNCTIONS       ===
# ============================================
async def back_to_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

async def back_to_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if context.user_data:
        context.user_data.clear()
    await add_content_menu(update, context)
    return ConversationHandler.END

async def back_to_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await manage_content_menu(update, context)
    return ConversationHandler.END

async def back_to_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await edit_content_menu(update, context)
    return ConversationHandler.END

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_user_menu(update, context, from_callback=True)
    return ConversationHandler.END

async def back_to_donate_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await donate_settings_menu(update, context)
    return ConversationHandler.END

async def back_to_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await other_links_menu(update, context)
    return ConversationHandler.END

async def back_to_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await bot_messages_menu(update, context)
    return ConversationHandler.END

async def back_to_admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def back_to_appearance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await appearance_menu_start(update, context)
    return AP_MENU

async def back_to_update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await update_photo_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===       CONVERSATION STATES            ===
# ============================================
# Add Movie/Series
(ADD_NAME, ADD_POSTER, ADD_DESC, ADD_CONFIRM) = range(4)

# Add Season
(SEL_CONTENT, SEL_SEASON_NAME, SEL_SEASON_POSTER, SEL_SEASON_DESC, SEL_SEASON_CONFIRM, SEL_SEASON_ASK_MORE) = range(10, 16)

# Add Episode
(EP_SEL_CONTENT, EP_SEL_SEASON, EP_SEL_NUMBER, EP_480P, EP_720P, EP_1080P, EP_4K, EP_ASK_MORE) = range(20, 28)

# Delete
(DEL_TYPE, DEL_CONTENT, DEL_CONFIRM) = range(30, 33)
(DEL_SEASON_CONTENT, DEL_SEASON_SELECT, DEL_SEASON_CONFIRM) = range(33, 36)
(DEL_EP_CONTENT, DEL_EP_SEASON, DEL_EP_SELECT, DEL_EP_CONFIRM) = range(36, 40)

# Edit
(EDIT_TYPE, EDIT_CONTENT, EDIT_NEW_NAME, EDIT_CONFIRM) = range(40, 44)
(EDIT_SEASON_CONTENT, EDIT_SEASON_SELECT, EDIT_SEASON_NEW_NAME, EDIT_SEASON_CONFIRM) = range(44, 48)
(EDIT_EP_CONTENT, EDIT_EP_SEASON, EDIT_EP_SELECT, EDIT_EP_NEW_NUM, EDIT_EP_CONFIRM) = range(48, 53)

# Other States
(CD_GET_QR, CL_GET_LINK, CS_GET_DELETE_TIME) = range(60, 63)
(UP_TYPE, UP_CONTENT, UP_TARGET, UP_POSTER) = range(63, 67)
(CA_GET_ID, CA_CONFIRM, CR_GET_ID, CR_CONFIRM) = range(67, 71)
(CPOST_CHAT, CPOST_POSTER, CPOST_CAPTION, CPOST_BTN_TEXT, CPOST_BTN_URL, CPOST_CONFIRM) = range(71, 77)
(MM_MAIN, MM_DL, MM_GEN, MM_POSTGEN, MM_GET_MSG, MM_ADMIN) = range(77, 83)
(AP_MENU, AP_FONT, AP_STYLE) = range(83, 86)
(CS_MENU_PHOTO,) = range(86, 87)
(BC_GET_MSG, BC_CONFIRM) = range(87, 89)
(MERGE_TYPE, MERGE_TARGET, MERGE_SOURCE, MERGE_CONFIRM) = range(89, 93)

# ============================================
# ===        MESSAGE HELPERS               ===
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
        "user_dl_dm_alert": "✅ <f>Check your DM (private chat) with me!</f>",
        "user_dl_content_not_found": "❌ <f>Error: Content nahi mila.</f>",
        "user_dl_file_error": "❌ <f>Error! {quality} file nahi bhej paya.</f>",
        "user_dl_blocked_error": "❌ <f>Error! File nahi bhej paya. Aapne bot ko block kiya.</f>",
        "user_dl_episodes_not_found": "❌ <f>Error: Is season ke liye episodes nahi mile.</f>",
        "user_dl_seasons_not_found": "❌ <f>Error: Is content ke liye seasons nahi mile.</f>",
        "user_dl_general_error": "❌ <f>Error! Please try again.</f>",
        "user_dl_sending_files": "✅ <b>{content_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>Aapke saare files bhej raha hoon...</f>",
        "user_dl_select_episode": "<b>{content_name}</b> | <b>Season {season_name}</b>\n\n<f>Episode select karein:</f>",
        "user_dl_select_season": "<b>{content_name}</b>\n\n<f>Season select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {minutes} minute(s) mein automatically delete ho jaayegi.</f></b>",
        "user_dl_fetching": "⏳ <f>Fetching files...</f>",
        "user_menu_greeting": "<f>Salaam {full_name}! Ye raha aapka menu:</f>",
        "user_donate_qr_error": "❌ <f>Donation info abhi admin ne set nahi ki hai.</f>",
        "user_donate_qr_text": "❤️ <b><f>Support Us!</f></b>\n\n<f>Agar aapko hamara kaam pasand aata hai, toh aap humein support kar sakte hain.</f>",
        "donate_thanks": "❤️ <f>Support karne ke liye shukriya!</f>",
        "user_not_admin": "<f>Aap admin nahi hain.</f>",
        "user_welcome_admin": "<f>Salaam, Admin! Admin panel ke liye</f> /menu <f>use karein.</f>",
        "user_welcome_basic": "<f>Salaam, {full_name}! Apna user menu dekhne ke liye</f> /user <f>use karein.</f>",
        "admin_cancel": "<f>Operation cancel kar diya gaya hai.</f>",
        "admin_panel_main": "👑 <b><f>Salaam, Admin Boss!</f></b> 👑\n<f>Aapka control panel taiyyar hai.</f>",
        "admin_panel_co": "👑 <b><f>Salaam, Co-Admin!</f></b> 👑\n<f>Aapka content panel taiyyar hai.</f>",
    }

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

async def delete_message_later(bot, chat_id: int, message_id: int, seconds: int):
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Auto-deleted message {message_id} for user {chat_id}")
    except Exception as e:
        logger.warning(f"Message delete karne me error: {e}")

async def send_donate_thank_you(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        msg = await format_message(context, "donate_thanks")
        await context.bot.send_message(chat_id=job.chat_id, text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning(f"Thank you message bhejte waqt error: {e}")

# ============================================
# ===        CANCEL HANDLER                ===
# ============================================
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
# ===        ADMIN COMMANDS & MENUS        ===
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
        keyboard = [
            [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
            [InlineKeyboardButton("📺 Add Series", callback_data="admin_add_series")],
            [InlineKeyboardButton("➕ Add Season", callback_data="admin_add_season")],
            [InlineKeyboardButton("➕ Add Episode", callback_data="admin_add_episode")],
            [InlineKeyboardButton("🗑️ Delete Content", callback_data="admin_menu_manage_content")],
            [InlineKeyboardButton("✏️ Edit Content", callback_data="admin_menu_edit_content")],
            [InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen")],
            [InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")],
        ]
        admin_menu_text = await format_message(context, "admin_panel_co")
    else:
        keyboard = [
            [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
            [InlineKeyboardButton("📺 Add Series", callback_data="admin_add_series")],
            [InlineKeyboardButton("➕ Add Season", callback_data="admin_add_season")],
            [InlineKeyboardButton("➕ Add Episode", callback_data="admin_add_episode")],
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
                InlineKeyboardButton("📊 User Stats", callback_data="admin_show_stats")
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
    # Redirect to admin menu since we have separate buttons
    await admin_command(update, context, from_callback=True)

async def manage_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Movie", callback_data="admin_del_movie")],
        [InlineKeyboardButton("🗑️ Delete Series", callback_data="admin_del_series")],
        [InlineKeyboardButton("🗑️ Delete Season", callback_data="admin_del_season")],
        [InlineKeyboardButton("🗑️ Delete Episode", callback_data="admin_del_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "🗑️ <b><f>Delete Content</f></b> 🗑️\n\n<f>Aap kya delete karna chahte hain?</f>"
    
    if from_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def edit_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Movie Name", callback_data="admin_edit_movie")],
        [InlineKeyboardButton("✏️ Edit Series Name", callback_data="admin_edit_series")],
        [InlineKeyboardButton("✏️ Edit Season Name", callback_data="admin_edit_season")],
        [InlineKeyboardButton("✏️ Edit Episode Number", callback_data="admin_edit_episode")],
        [InlineKeyboardButton("🔄 Merge Content", callback_data="admin_merge_content")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "✏️ <b><f>Edit Content</f></b> ✏️\n\n<f>Aap kya edit karna chahte hain?</f>"
    
    if from_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# ============================================
# ===        ADD MOVIE                     ===
# ============================================
async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = 'movie'
    
    text = "<f>Salaam Admin! Movie ka <b>Naam</b> kya hai?</f>\n\n/cancel - <f>Cancel.</f>"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ADD_NAME

async def add_series_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = 'series'
    
    text = "<f>Salaam Admin! Series ka <b>Naam</b> kya hai?</f>\n\n/cancel - <f>Cancel.</f>"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ADD_NAME

async def add_content_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content_name'] = update.message.text
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    text = f"<f>Badhiya! Ab {display_type} ka <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return ADD_POSTER

async def add_content_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = "Ye photo nahi hai. Please ek photo bhejo."
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return ADD_POSTER
    
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    text = "<f>Poster mil gaya! Ab <b>Description (Synopsis)</b> bhejo.</f>\n\n/skip <f>ya</f> /cancel."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return ADD_DESC

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
    
    caption = f"<b>{name}</b>\n\n{desc if desc else ''}\n\n<f>--- Details Check Karo ---</f>"
    keyboard = [[InlineKeyboardButton("✅ Save", callback_data="save_content")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]
    
    if update.message:
        try:
            await update.message.reply_photo(photo=poster_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Confirm content details me error: {e}")
            text = "❌ <b><f>Error!</f></b> <f>Poster bhej nahi paya. Dobara try karein.</f>"
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return ADD_DESC
    return ADD_CONFIRM

async def save_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        name = context.user_data['content_name']
        content_type = context.user_data.get('content_type', 'movie')
        display_type = "Movie" if content_type == "movie" else "Series"
        
        if content_collection.find_one({"name": name}):
            caption = f"⚠️ <b><f>Error:</f></b> <f>Ye {display_type} naam</f> '{name}' <f>pehle se hai.</f>"
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)
            await admin_command(update, context, from_callback=True)
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
        else:
            content_doc["episodes"] = {}
        
        content_collection.insert_one(content_doc)
        
        caption = f"✅ <b><f>Success!</f></b> '{name}' <f>add ho gaya hai.</f>"
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)
        await admin_command(update, context, from_callback=True)
        
    except Exception as e:
        logger.error(f"Content save karne me error: {e}")
        caption = "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>"
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===        ADD SEASON                    ===
# ============================================
async def add_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await add_season_show_content_list(update, context, page=0)

async def add_season_show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("addseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page
    
    items, keyboard = await build_paginated_keyboard(
        collection=content_collection,
        page=page,
        page_callback_prefix="addseason_page_",
        item_callback_prefix="season_content_",
        back_callback="admin_menu",
        filter_query={"type": "series"}
    )
    
    if not items and page == 0:
        text = "❌ <f>Error: Abhi koi Series add nahi hui hai. Pehle 'Add Series' se add karein.</f>"
    else:
        text = f"<f>Aap kis Series mein season add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page + 1})</f>"
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return SEL_CONTENT

async def add_season_get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("season_content_", "")
    context.user_data['content_name'] = content_name
    
    content_doc = content_collection.find_one({"name": content_name})
    if not content_doc:
        text = "⚠️ <b><f>Error!</f></b> <f>Series database mein nahi mili.</f> /cancel <f>karke dobara try karein.</f>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    if content_doc.get('type') != 'series':
        text = f"❌ <b><f>Error!</f></b> '{content_name}' <f>ek movie hai, isme season add nahi kar sakte.</f>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    seasons = content_doc.get("seasons", {})
    season_keys = list(seasons.keys())
    
    if not season_keys:
        text = f"<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Is Series mein abhi koi season nahi hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
    else:
        try:
            sorted_seasons = sorted(season_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_season_name = sorted_seasons[-1]
            text = f"<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Last added season:</f> <b>{last_season_name}</b>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
        except Exception as e:
            logger.warning(f"Last season find karne me error: {e}")
            text = f"<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Is Series mein abhi koi season nahi hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return SEL_SEASON_NAME

async def add_season_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_name = update.message.text
    context.user_data['season_name'] = season_name
    content_name = context.user_data['content_name']
    
    content_doc = content_collection.find_one({"name": content_name})
    if not content_doc:
        text = "⚠️ <b><f>Error!</f></b> <f>Series database mein nahi mili.</f> /cancel <f>karke dobara try karein.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
            
    if season_name in content_doc.get("seasons", {}):
        text = f"⚠️ <b><f>Error!</f></b> '{content_name}' <f>mein 'Season {season_name}' pehle se hai.</f>\n\n<f>Koi doosra naam/number type karein ya</f> /cancel <f>karein.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return SEL_SEASON_NAME
    
    text = f"<f>Aapne Season</f> '{season_name}' <f>select kiya hai.</f>\n\n<f>Ab is season ka <b>Poster (Photo)</b> bhejo.</f>\n\n/skip - <f>Default poster use karo.</f>\n/cancel - <f>Cancel.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return SEL_SEASON_POSTER

async def add_season_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = "<f>Ye photo nahi hai. Please ek photo bhejo.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return SEL_SEASON_POSTER
    
    context.user_data['season_poster_id'] = update.message.photo[-1].file_id
    text = "<f>Poster mil gaya! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return SEL_SEASON_DESC

async def add_season_skip_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_poster_id'] = None
    text = "<f>Default poster set! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return SEL_SEASON_DESC

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
    
    caption = f"<b><f>Confirm Karo:</f></b>\n<f>Series:</f> <b>{content_name}</b>\n<f>Naya Season:</f> <b>{season_name}</b>\n<f>Description:</f> {season_desc or 'N/A'}\n\n<f>Save kar doon?</f>"
    keyboard = [[InlineKeyboardButton("✅ Haan, Save Karo", callback_data="save_season")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]
    
    await update.message.reply_photo(
        photo=poster_id_to_show,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return SEL_SEASON_CONFIRM

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
        
        text = f"✅ <f>Season</f> <b>{season_name}</b> <f>save ho gaya!</f>\n\n<f>Aap</f> <b>{content_name}</b> <f>mein aur season add karna chahte hain?</f>"
        keyboard = [
            [InlineKeyboardButton("✅ Yes (Add More)", callback_data="add_season_more_yes")],
            [InlineKeyboardButton("🚫 No (Back to Menu)", callback_data="add_season_more_no")]
        ]
        
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Purana photo message delete nahi kar paya: {e}")
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            return SEL_SEASON_ASK_MORE
        
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        return SEL_SEASON_ASK_MORE
        
    except Exception as e:
        logger.error(f"Season save karne me error: {e}")
        caption = "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>"
        try:
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=None)
        except Exception as e2:
            logger.error(f"Error message bhi nahi dikha paya: {e2}")
            await context.bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode=ParseMode.HTML)
        
        context.user_data.clear()
        await asyncio.sleep(3)
        await admin_command(update, context, from_callback=True)
        return ConversationHandler.END

async def add_season_more_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    last_season_name = context.user_data['season_name']
    content_name = context.user_data['content_name']
    
    text = f"<f>Last Season:</f> <b>{last_season_name}</b>. <f>Series:</f> <b>{content_name}</b>\n\n<f>Ab agla <b>Season Number/Naam</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>"
    
    context.user_data.pop('season_name', None)
    context.user_data.pop('season_poster_id', None)
    context.user_data.pop('season_desc', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return SEL_SEASON_NAME

async def add_season_more_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

# ============================================
# ===        ADD EPISODE                   ===
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
        back_callback="admin_menu"
    )
    
    if not items and page == 0:
        text = "❌ <f>Error: Abhi koi content add nahi hua hai. Pehle 'Add Movie' ya 'Add Series' se add karein.</f>"
    else:
        text = f"<f>Aap kis content mein episode add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page + 1})</f>"
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EP_SEL_CONTENT

async def add_episode_get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("ep_content_", "")
    context.user_data['content_name'] = content_name
    content_doc = content_collection.find_one({"name": content_name})
    
    if content_doc.get('type') == 'movie':
        context.user_data['season_name'] = None
        context.user_data['content_type'] = 'movie'
        text = f"<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n<f>Is movie mein abhi koi episode nahi hai.</f>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n<f>(Agar yeh ek single movie hai, toh</f> <code>1</code> <f>type karein.)</f>\n\n/cancel - <f>Cancel.</f>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return EP_SEL_NUMBER
    
    # For series, show seasons
    seasons = content_doc.get("seasons", {})
    if not seasons:
        text = f"❌ <b><f>Error!</f></b> '{content_name}' <f>mein koi season nahi hai.</f>\n\n<f>Pehle</f> <code>➕ Add Season</code> <f>se season add karo.</f>"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Content", callback_data=f"addep_page_{current_page}")])
    
    text = f"<f>Aapne</f> <b>{content_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EP_SEL_SEASON

async def add_episode_get_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("ep_season_", "")
    context.user_data['season_name'] = season_name
    context.user_data['content_type'] = 'series'
    
    content_name = context.user_data['content_name']
    content_doc = content_collection.find_one({"name": content_name})
    episodes = content_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = f"<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Is season mein abhi koi episode nahi hai.</f>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
    else:
        try:
            sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_ep_num = sorted_eps[-1]
            text = f"<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Last added episode:</f> <b>{last_ep_num}</b>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
        except Exception as e:
            logger.warning(f"Last episode find karne me error: {e}")
            text = f"<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Is season mein abhi koi episode nahi hai.</f>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n\n/cancel - <f>Cancel.</f>"
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EP_SEL_NUMBER

async def add_episode_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = f"⚠️ <b><f>Error!</f></b> '{content_name}' - Episode {ep_num} <f>pehle se maujood hai. Please pehle isse delete karein ya koi doosra episode number dein.</f>\n\n/cancel - <f>Cancel.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EP_SEL_NUMBER
    
    text = f"<f>Aapne</f> <b>Episode {ep_num}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>480p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_480P

async def add_episode_save_file_helper(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and (update.message.document.mime_type and update.message.document.mime_type.startswith('video')):
        file_id = update.message.document.file_id
    
    if not file_id:
        if update.message.text and update.message.text.startswith('/'):
            return False
        text = "<f>Ye video file nahi hai. Please dobara video file bhejein ya</f> /skip <f>karein.</f>"
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
        
        text = f"✅ <b>{quality}</b> <f>save ho gaya.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        logger.error(f"Episode file save karne me error: {e}")
        text = f"❌ <b><f>Error!</f></b> {quality} <f>save nahi kar paya. Logs check karein.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False

async def add_episode_get_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "480p"):
        return EP_480P
    
    text = "<f>Ab <b>720p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_720P

async def add_episode_skip_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ <f>480p skip kar diya.</f>\n\n<f>Ab <b>720p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_720P

async def add_episode_get_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "720p"):
        return EP_720P
    
    text = "<f>Ab <b>1080p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_1080P

async def add_episode_skip_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ <f>720p skip kar diya.</f>\n\n<f>Ab <b>1080p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_1080P

async def add_episode_get_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await add_episode_save_file_helper(update, context, "1080p"):
        return EP_1080P
    
    text = "<f>Ab <b>4K</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_4K

async def add_episode_skip_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ <f>1080p skip kar diya.</f>\n\n<f>Ab <b>4K</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return EP_4K

async def add_episode_get_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await add_episode_save_file_helper(update, context, "4K"):
        text = "✅ <b><f>Success!</f></b> <f>Saari qualities save ho gayi hain.</f>"
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        return EP_4K
    
    return await add_episode_ask_more(update, context)

async def add_episode_skip_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ <f>4K skip kar diya.</f>\n\n✅ <b><f>Success!</f></b> <f>Episode save ho gaya hai.</f>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return await add_episode_ask_more(update, context)

async def add_episode_ask_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ep_num = context.user_data['ep_num']
    season_name = context.user_data.get('season_name', 'Movie')
    
    text = f"✅ <f>Ep</f> <b>{ep_num}</b> <f>save ho gaya!</f>\n\n<f>Aap</f> <b>S{season_name}</b> <f>mein aur episode add karna chahte hain?</f>"
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes (Add More)", callback_data="add_ep_more_yes")],
        [InlineKeyboardButton("🚫 No (Back to Menu)", callback_data="add_ep_more_no")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EP_ASK_MORE

async def add_episode_more_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    last_ep_num = context.user_data['ep_num']
    season_name = context.user_data.get('season_name', 'Movie')
    
    try:
        next_ep_num = str(int(last_ep_num) + 1)
        text = f"<f>Last Ep:</f> <b>{last_ep_num}</b>. <f>Season:</f> <b>{season_name}</b>\n\n<f>Ab agla <b>Episode Number</b> bhejo.</f>\n<f>(Suggestion: {next_ep_num})</f>\n\n/cancel - <f>Cancel.</f>"
    except ValueError:
        text = f"<f>Last Ep:</f> <b>{last_ep_num}</b>. <f>Season:</f> <b>{season_name}</b>\n\n<f>Ab agla <b>Episode Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>"
    
    context.user_data.pop('ep_num', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EP_SEL_NUMBER

async def add_episode_more_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

# ============================================
# ===        DELETE FUNCTIONS              ===
# ============================================
async def delete_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = 'movie'
    return await delete_content_show_list(update, context, page=0)

async def delete_series_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['content_type'] = 'series'
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
        back_callback="admin_menu_manage_content",
        filter_query={"type": content_type}
    )
    
    if not items and page == 0:
        text = f"❌ <f>Error: Abhi koi {display_type} add nahi hua hai.</f>"
    else:
        text = f"<f>Kaunsa <b>{display_type}</b> delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page + 1})</f>"
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DEL_CONTENT

async def delete_content_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    content_name = query.data.replace("del_content_", "")
    context.user_data['content_name'] = content_name
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {content_name} ko Delete Karo", callback_data="del_content_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_manage_content")]]
    
    text = f"⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{content_name}</b> <f>ko delete karne wale hain. Iske saare seasons aur episodes delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DEL_CONFIRM

async def delete_content_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    content_name = context.user_data['content_name']
    content_type = context.user_data.get('content_type', 'movie')
    display_type = "Movie" if content_type == "movie" else "Series"
    
    try:
        content_collection.delete_one({"name": content_name})
        logger.info(f"Content deleted: {content_name}")
        text = f"✅ <b><f>Success!</f></b>\n<f>{display_type}</f> '{content_name}' <f>delete ho gaya hai.</f>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Content delete karne me error: {e}")
        text = f"❌ <b><f>Error!</f></b> <f>{display_type} delete nahi ho paya.</f>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===        USER HANDLERS                 ===
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
# ===        USER DOWNLOAD HANDLER         ===
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
            sent_msg = await context.bot.send_message(chat_id=user_id, text=checking_text, parse_mode=ParseMode.HTML)
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
        
        # Episode clicked
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
        
        # Season clicked -> Show Episodes
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
                        logger.warning(f"DL Handler: Media edit fail, fallback to caption: {e}")
                        await query.edit_message_caption(
                            caption=msg,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode=ParseMode.HTML
                        )
                        sent_selection_message = query.message
                except Exception as e:
                    logger.error(f"DL Handler: Media edit critical fail: {e}")
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
        
        # Only content clicked -> Show Seasons or Episodes
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
# ===        OTHER ADMIN SETTINGS          ===
# ============================================
async def donate_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    # ... (implementation)
    pass

async def other_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    # ... (implementation)
    pass

async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    # ... (implementation)
    pass

async def update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ... (implementation)
    pass

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ... (implementation)
    pass

async def post_gen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ... (implementation)
    pass

async def gen_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # ... (implementation)
    pass

async def appearance_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    # ... (implementation)
    return AP_MENU

async def bot_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    # ... (implementation)
    return MM_MAIN

# ============================================
# ===        ERROR HANDLER                 ===
# ============================================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error} \nUpdate: {update}", exc_info=True)

# ============================================
# ===        WEBHOOK SETUP                 ===
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
# ===        MAIN FUNCTION                 ===
# ============================================
def main():
    global bot_app
    PORT = int(os.environ.get("PORT", 8080))
    
    my_defaults = Defaults(parse_mode=ParseMode.HTML)
    bot_app = Application.builder().token(BOT_TOKEN).defaults(my_defaults).build()
    
    # Cancel handler
    global_cancel_handler = CommandHandler("cancel", cancel_command)
    
    # Fallbacks
    global_fallbacks = [
        CommandHandler("start", cancel_command),
        CommandHandler("menu", cancel_command),
        CommandHandler("admin", cancel_command),
        global_cancel_handler
    ]
    
    admin_menu_fallback = [CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$"), global_cancel_handler]
    
    # Add Movie Conversation
    add_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_movie_start, pattern="^admin_add_movie$")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_name)],
            ADD_POSTER: [MessageHandler(filters.PHOTO, add_content_get_poster)],
            ADD_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_desc),
                CommandHandler("skip", add_content_skip_desc)
            ],
            ADD_CONFIRM: [CallbackQueryHandler(save_content, pattern="^save_content$")]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # Add Series Conversation
    add_series_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_series_start, pattern="^admin_add_series$")],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_name)],
            ADD_POSTER: [MessageHandler(filters.PHOTO, add_content_get_poster)],
            ADD_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_get_desc),
                CommandHandler("skip", add_content_skip_desc)
            ],
            ADD_CONFIRM: [CallbackQueryHandler(save_content, pattern="^save_content$")]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # Add Season Conversation
    add_season_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_season_start, pattern="^admin_add_season$")],
        states={
            SEL_CONTENT: [
                CallbackQueryHandler(add_season_show_content_list, pattern="^addseason_page_"),
                CallbackQueryHandler(add_season_get_content, pattern="^season_content_")
            ],
            SEL_SEASON_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_season_get_name)],
            SEL_SEASON_POSTER: [
                MessageHandler(filters.PHOTO, add_season_get_poster),
                CommandHandler("skip", add_season_skip_poster)
            ],
            SEL_SEASON_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_season_get_desc),
                CommandHandler("skip", add_season_skip_desc)
            ],
            SEL_SEASON_CONFIRM: [CallbackQueryHandler(add_season_save, pattern="^save_season$")],
            SEL_SEASON_ASK_MORE: [
                CallbackQueryHandler(add_season_more_yes, pattern="^add_season_more_yes$"),
                CallbackQueryHandler(add_season_more_no, pattern="^add_season_more_no$")
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # Add Episode Conversation
    add_episode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_episode_start, pattern="^admin_add_episode$")],
        states={
            EP_SEL_CONTENT: [
                CallbackQueryHandler(add_episode_show_content_list, pattern="^addep_page_"),
                CallbackQueryHandler(add_episode_get_content, pattern="^ep_content_")
            ],
            EP_SEL_SEASON: [
                CallbackQueryHandler(add_episode_get_season, pattern="^ep_season_"),
                CallbackQueryHandler(add_episode_show_content_list, pattern="^addep_page_")
            ],
            EP_SEL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_episode_get_number)],
            EP_480P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_episode_get_480p), CommandHandler("skip", add_episode_skip_480p)],
            EP_720P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_episode_get_720p), CommandHandler("skip", add_episode_skip_720p)],
            EP_1080P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_episode_get_1080p), CommandHandler("skip", add_episode_skip_1080p)],
            EP_4K: [MessageHandler(filters.ALL & ~filters.COMMAND, add_episode_get_4k), CommandHandler("skip", add_episode_skip_4k)],
            EP_ASK_MORE: [
                CallbackQueryHandler(add_episode_more_yes, pattern="^add_ep_more_yes$"),
                CallbackQueryHandler(add_episode_more_no, pattern="^add_ep_more_no$")
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # Delete Movie Conversation
    delete_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_movie_start, pattern="^admin_del_movie$")],
        states={
            DEL_CONTENT: [
                CallbackQueryHandler(delete_content_show_list, pattern="^delcontent_page_"),
                CallbackQueryHandler(delete_content_confirm, pattern="^del_content_")
            ],
            DEL_CONFIRM: [CallbackQueryHandler(delete_content_do, pattern="^del_content_confirm_yes$")]
        },
        fallbacks=global_fallbacks + [CallbackQueryHandler(manage_content_menu, pattern="^admin_menu_manage_content$")],
        allow_reentry=True
    )
    
    # Delete Series Conversation
    delete_series_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_series_start, pattern="^admin_del_series$")],
        states={
            DEL_CONTENT: [
                CallbackQueryHandler(delete_content_show_list, pattern="^delcontent_page_"),
                CallbackQueryHandler(delete_content_confirm, pattern="^del_content_")
            ],
            DEL_CONFIRM: [CallbackQueryHandler(delete_content_do, pattern="^del_content_confirm_yes$")]
        },
        fallbacks=global_fallbacks + [CallbackQueryHandler(manage_content_menu, pattern="^admin_menu_manage_content$")],
        allow_reentry=True
    )
    
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
    bot_app.add_handler(CallbackQueryHandler(post_gen_menu, pattern="^admin_post_gen$"))
    bot_app.add_handler(CallbackQueryHandler(gen_link_menu, pattern="^admin_gen_link$"))
    
    # User menu
    bot_app.add_handler(CallbackQueryHandler(user_show_donate_menu, pattern="^user_show_donate_menu$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"))
    
    # Download handler
    bot_app.add_handler(CallbackQueryHandler(download_button_handler, pattern="^dl"))
    
    # Add conversation handlers
    bot_app.add_handler(add_movie_conv)
    bot_app.add_handler(add_series_conv)
    bot_app.add_handler(add_season_conv)
    bot_app.add_handler(add_episode_conv)
    bot_app.add_handler(delete_movie_conv)
    bot_app.add_handler(delete_series_conv)
    
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
