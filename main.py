# ============================================
# ===       COMPLETE MOVIE BOT (v5)        ===
# ===       FIXED APPEARANCE MENU           ===
# ===       FONTS & STYLES WORKING          ===
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

try:
    logger.info("MongoDB se connect karne ki koshish...")
    client = MongoClient(MONGO_URI)
    db = client['MovieBotDB']
    users_collection = db['users']
    movies_collection = db['movies']
    config_collection = db['config']
    
    movies_collection.create_index([("name", ASCENDING)])
    movies_collection.create_index([("created_at", DESCENDING)])
    movies_collection.create_index([("last_modified", DESCENDING)])
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

async def get_config():
    config = config_collection.find_one({"_id": "bot_config"})
    
    if not config:
        default_config = {
            "_id": "bot_config",
            "donate_qr_id": None,
            "links": {"backup": "https://t.me/", "download": None, "help": "https://t.me/"},
            "user_menu_photo_id": None,
            "delete_seconds": 300,
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
    if "links" not in config:
        config["links"] = {"backup": "https://t.me/", "download": None, "help": "https://t.me/"}
        needs_update = True
    elif "help" not in config["links"]:
        config["links"]["help"] = "https://t.me/"
        needs_update = True

    if needs_update:
        update_set = {
            "user_menu_photo_id": config.get("user_menu_photo_id"),
            "delete_seconds": config.get("delete_seconds", 300),
            "co_admins": config.get("co_admins", []),
            "appearance": config.get("appearance", {"font": "default", "style": "normal"}),
            "links": config.get("links", {"backup": "https://t.me/", "download": None, "help": "https://t.me/"})
        }
        config_collection.update_one({"_id": "bot_config"}, {"$set": update_set})

    return config

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
    except Exception as e:
        logger.warning(f"Message delete karne me error: {e}")

async def send_donate_thank_you(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.send_message(chat_id=job.chat_id, text="❤️ Support karne ke liye shukriya!", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning(f"Thank you message bhejte waqt error: {e}")

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
# ===        CONVERSATION STATES           ===
# ============================================
(M_GET_NAME, M_GET_POSTER, M_GET_DESC, M_GET_480P, M_GET_720P, M_GET_1080P, M_GET_4K, M_CONFIRM) = range(8)
(DA_GET_MOVIE, DA_CONFIRM) = range(8, 10)
(EA_GET_MOVIE, EA_GET_NEW_NAME, EA_CONFIRM) = range(10, 13)
(PG_MENU, PG_GET_MOVIE, PG_GET_SHORT_LINK, PG_GET_CHAT) = range(13, 17)
(GL_MENU, GL_GET_MOVIE) = range(17, 19)
(CD_GET_QR, CL_GET_LINK, CS_GET_DELETE_TIME) = range(19, 22)
(UP_GET_MOVIE, UP_GET_POSTER) = range(22, 24)
(CA_GET_ID, CA_CONFIRM, CR_GET_ID, CR_CONFIRM) = range(24, 28)
(CPOST_CHAT, CPOST_POSTER, CPOST_CAPTION, CPOST_BTN_TEXT, CPOST_BTN_URL, CPOST_CONFIRM) = range(28, 34)
(MM_MAIN, MM_DL, MM_GEN, MM_POSTGEN, MM_GET_MSG, MM_ADMIN) = range(34, 40)
(AP_MENU, AP_FONT, AP_STYLE) = range(40, 43)
(CS_MENU_PHOTO,) = range(43, 44)
(BC_GET_MSG, BC_CONFIRM) = range(44, 46)

# ============================================
# ===        BACK FUNCTIONS                ===
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

async def back_to_update_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await update_photo_menu(update, context)
    return ConversationHandler.END

async def back_to_gen_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await gen_link_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===        CANCEL HANDLER                ===
# ============================================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.id} ne operation cancel kiya.")
    if context.user_data:
        context.user_data.clear()
    
    reply_text = "Operation cancel kar diya gaya hai."
    
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
# ===        ADMIN COMMANDS                ===
# ============================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    if not await is_co_admin(user_id):
        if not from_callback:
            if update.message:
                await update.message.reply_text("Aap admin nahi hain.", parse_mode=ParseMode.HTML)
            else:
                await update.callback_query.answer("Aap admin nahi hain.", show_alert=True)
        return
        
    logger.info("Admin/Co-Admin ne /admin command use kiya.")
    
    if not await is_main_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
            [
                InlineKeyboardButton("🗑️ Delete Movie", callback_data="admin_del_movie"),
                InlineKeyboardButton("✏️ Edit Movie", callback_data="admin_edit_movie")
            ],
            [
                InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")
            ],
            [
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo"),
                InlineKeyboardButton("📊 User Stats", callback_data="admin_show_stats")
            ],
        ]
        admin_menu_text = "👑 <b>Salaam, Co-Admin!</b> 👑\nAapka content panel taiyyar hai."
    
    else:
        keyboard = [
            [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
            [
                InlineKeyboardButton("🗑️ Delete Movie", callback_data="admin_del_movie"),
                InlineKeyboardButton("✏️ Edit Movie", callback_data="admin_edit_movie")
            ],
            [
                InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")
            ],
            [
                InlineKeyboardButton("🔗 Other Links", callback_data="admin_menu_other_links"),
                InlineKeyboardButton("❤️ Donation", callback_data="admin_menu_donate_settings")
            ],
            [
                InlineKeyboardButton("⏱️ Auto-Delete Time", callback_data="admin_set_delete_time"),
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo")
            ],
            [
                InlineKeyboardButton("🎨 Bot Appearance", callback_data="admin_menu_appearance"),
                InlineKeyboardButton("📊 User Stats", callback_data="admin_show_stats")
            ],
            [InlineKeyboardButton("⚙ Bot Messages", callback_data="admin_menu_messages")],
            [InlineKeyboardButton("🛠️ Admin Settings", callback_data="admin_menu_admin_settings")]
        ]
        admin_menu_text = "👑 <b>Salaam, Admin Boss!</b> 👑\nAapka control panel taiyyar hai."
    
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
        [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "➕ <b>Add Content</b> ➕\n\nAap kya add karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def manage_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Movie", callback_data="admin_del_movie")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "🗑️ <b>Delete Content</b> 🗑️\n\nAap kya delete karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def edit_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Movie", callback_data="admin_edit_movie")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "✏️ <b>Edit Content</b> ✏️\n\nAap kya edit karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# ============================================
# ===        ADD MOVIE                     ===
# ============================================
async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    context.user_data['qualities'] = {}
    await query.edit_message_text("Salaam Admin! Movie ka <b>Naam</b> kya hai?\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return M_GET_NAME

async def add_movie_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Badhiya! Ab movie ka <b>Poster (Photo)</b> bhejo.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return M_GET_POSTER

async def add_movie_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Ye photo nahi hai. Please ek photo bhejo.", parse_mode=ParseMode.HTML)
        return M_GET_POSTER
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    await update.message.reply_text("Poster mil gaya! Ab <b>Description (Synopsis)</b> bhejo.\n\n/skip ya /cancel.", parse_mode=ParseMode.HTML)
    return M_GET_DESC

async def add_movie_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Ab <b>480p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_480P

async def add_movie_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = None
    await update.message.reply_text("Description skip! Ab <b>480p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_480P

async def _save_movie_file(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('video'):
        file_id = update.message.document.file_id
    
    if not file_id:
        if update.message.text and update.message.text.startswith('/'):
            return False
        await update.message.reply_text("Ye video file nahi hai. Please dobara video file bhejein ya /skip karein.", parse_mode=ParseMode.HTML)
        return False

    context.user_data['qualities'][quality] = file_id
    await update.message.reply_text(f"✅ <b>{quality}</b> save ho gaya.", parse_mode=ParseMode.HTML)
    return True

async def add_movie_get_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_file(update, context, "480p"):
        return M_GET_480P
    await update.message.reply_text("Ab <b>720p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_720P

async def add_movie_skip_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ 480p skip kar diya.\n\nAb <b>720p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_720P

async def add_movie_get_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_file(update, context, "720p"):
        return M_GET_720P
    await update.message.reply_text("Ab <b>1080p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def add_movie_skip_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ 720p skip kar diya.\n\nAb <b>1080p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def add_movie_get_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_file(update, context, "1080p"):
        return M_GET_1080P
    await update.message.reply_text("Ab <b>4K</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_4K

async def add_movie_skip_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ 1080p skip kar diya.\n\nAb <b>4K</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
    return M_GET_4K

async def add_movie_get_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _save_movie_file(update, context, "4K"):
        await update.message.reply_text("✅ 4K save ho gaya.", parse_mode=ParseMode.HTML)
    else:
        return M_GET_4K
    return await add_movie_confirm(update, context)

async def add_movie_skip_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ 4K skip kar diya.", parse_mode=ParseMode.HTML)
    return await add_movie_confirm(update, context)

async def add_movie_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('qualities'):
        await update.message.reply_text("⚠️ Error! Aapne kam se kam ek file add nahi ki. Dobara try karein.", parse_mode=ParseMode.HTML)
        await update.message.reply_text("Ab <b>480p</b> quality ki video file bhejein.\nYa /skip type karein.", parse_mode=ParseMode.HTML)
        return M_GET_480P

    name = context.user_data['name']
    poster_id = context.user_data['poster_id']
    desc = context.user_data.get('description', 'N/A')
    file_count = len(context.user_data['qualities'])
    
    caption = f"<b>{name}</b>\n\n{desc}\n\n--- Details Check Karo ---\nTotal Files: <b>{file_count}</b>"
    keyboard = [[InlineKeyboardButton("✅ Save", callback_data="save_movie")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    
    try:
        await update.message.reply_photo(photo=poster_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning(f"Confirm movie details me error: {e}")
        await update.message.reply_text("❌ Error! Poster bhej nahi paya. Dobara try karein.", parse_mode=ParseMode.HTML)
        return M_GET_4K
        
    return M_CONFIRM

async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        name = context.user_data['name']
        if movies_collection.find_one({"name": name}):
            await query.edit_message_caption(caption=f"⚠️ Error: Ye movie naam '{name}' pehle se hai.", parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)
            await add_content_menu(update, context)
            return ConversationHandler.END
        
        movie_doc = {
            "name": name,
            "poster_id": context.user_data['poster_id'],
            "description": context.user_data.get('description'),
            "qualities": context.user_data['qualities'],
            "created_at": datetime.now(),
            "last_modified": datetime.now()
        }
        movies_collection.insert_one(movie_doc)
        await query.edit_message_caption(caption=f"✅ Success! '{name}' add ho gaya hai.", parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)
        await add_content_menu(update, context)
    except Exception as e:
        logger.error(f"Movie save karne me error: {e}")
        await query.edit_message_caption(caption="❌ Error! Database me save nahi kar paya.", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===        DELETE MOVIE                  ===
# ============================================
async def delete_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_movie_show_list(update, context, page=0)

async def delete_movie_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delmovie_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    movies, keyboard = await build_paginated_keyboard(
        collection=movies_collection,
        page=page,
        page_callback_prefix="delmovie_page_",
        item_callback_prefix="del_movie_",
        back_callback="back_to_manage"
    )
    
    if not movies and page == 0:
        text = "❌ Error: Abhi koi movie add nahi hui hai."
    else:
        text = f"Kaunsi <b>Movie</b> delete karni hai?\n\n<b>Recently Updated First</b> (Sabse naya pehle):\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DA_GET_MOVIE

async def delete_movie_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_name = query.data.replace("del_movie_", "")
    context.user_data['movie_name'] = movie_name
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {movie_name} ko Delete Karo", callback_data="del_movie_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    text = f"⚠️ <b>FINAL WARNING</b> ⚠️\n\nAap <b>{movie_name}</b> ko delete karne wale hain. Iske saare files delete ho jayenge.\n\n<b>Are you sure?</b>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DA_CONFIRM

async def delete_movie_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    movie_name = context.user_data['movie_name']
    try:
        movies_collection.delete_one({"name": movie_name})
        logger.info(f"Movie deleted: {movie_name}")
        await query.edit_message_text(f"✅ Success!\nMovie '{movie_name}' delete ho gayi hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Movie delete karne me error: {e}")
        await query.edit_message_text("❌ Error! Movie delete nahi ho payi.", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===        EDIT MOVIE                    ===
# ============================================
async def edit_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_movie_show_list(update, context, page=0)

async def edit_movie_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editmovie_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    movies, keyboard = await build_paginated_keyboard(
        collection=movies_collection,
        page=page,
        page_callback_prefix="editmovie_page_",
        item_callback_prefix="edit_movie_",
        back_callback="back_to_edit_menu"
    )
    
    if not movies and page == 0:
        text = "❌ Error: Abhi koi movie add nahi hui hai."
    else:
        text = f"Kaunsi <b>Movie</b> ka naam edit karna hai?\n\n<b>Recently Updated First</b> (Sabse naya pehle):\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EA_GET_MOVIE

async def edit_movie_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_name = query.data.replace("edit_movie_", "")
    context.user_data['old_movie_name'] = movie_name
    await query.edit_message_text(f"Aapne <b>{movie_name}</b> select kiya hai.\n\nAb iska <b>Naya Naam</b> bhejo.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return EA_GET_NEW_NAME

async def edit_movie_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data['old_movie_name']
    
    if movies_collection.find_one({"name": new_name}):
        await update.message.reply_text(f"⚠️ Error! Naya naam '{new_name}' pehle se maujood hai. Koi doosra naam dein.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
        return EA_GET_NEW_NAME
    
    context.user_data['new_movie_name'] = new_name
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_name}' ko '{new_name}' Karo", callback_data="edit_movie_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    text = f"<b>Confirm Karo:</b>\n\nPurana Naam: <code>{old_name}</code>\nNaya Naam: <code>{new_name}</code>\n\n<b>Are you sure?</b>"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EA_CONFIRM

async def edit_movie_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_name = context.user_data['old_movie_name']
    new_name = context.user_data['new_movie_name']
    try:
        movies_collection.update_one(
            {"name": old_name},
            {"$set": {"name": new_name, "last_modified": datetime.now()}}
        )
        logger.info(f"Movie naam update ho gaya: {old_name} -> {new_name}")
        await query.edit_message_text(f"✅ Success!\nMovie '{old_name}' ka naam badal kar '{new_name}' ho gaya hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Movie naam update karne me error: {e}")
        await query.edit_message_text("❌ Error! Movie naam update nahi ho paya.", parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===        POST GENERATOR                ===
# ============================================
async def post_gen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("✍️ Movie Post", callback_data="post_gen_movie")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "✍️ <b>Post Generator</b> ✍️\n\nAap kis tarah ka post generate karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_MENU

async def post_gen_select_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await post_gen_show_movie_list(update, context, page=0)

async def post_gen_show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("postgen_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page 
        
    movies, keyboard = await build_paginated_keyboard(
        collection=movies_collection,
        page=page,
        page_callback_prefix="postgen_page_",
        item_callback_prefix="post_movie_",
        back_callback="admin_post_gen" 
    )
    
    if not movies and page == 0:
        text = "❌ Error: Abhi koi movie add nahi hui hai."
    else:
        text = f"Kaunsi <b>Movie</b> select karna hai?\n\n<b>Recently Updated First</b> (Sabse naya pehle):\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return PG_GET_MOVIE

async def post_gen_ask_shortlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_name = query.data.replace("post_movie_", "")
    context.user_data['movie_name'] = movie_name
    
    try:
        bot_username = (await context.bot.get_me()).username
        config = await get_config()
        movie_doc = movies_collection.find_one({"name": movie_name})
        
        movie_id = str(movie_doc['_id'])
        dl_callback_data = f"dl{movie_id}"
        
        poster_id = movie_doc['poster_id']
        description = movie_doc.get('description', '')
        
        caption_template = "✅ <b>{movie_name}</b>\n\n<b>📖 Synopsis:</b>\n{description}\n\nNeeche [Download] button dabake download karein!"
        caption = caption_template.format(movie_name=movie_name, description=description if description else "")
        
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
        
        await query.edit_message_text(f"✅ <b>Post Ready!</b>\n\nAapka original download link hai:\n<code>{original_download_url}</code>\n\nPlease iska <b>shortened link</b> reply mein bhejein.\n(Agar link change nahi karna hai, toh upar waala link hi copy karke bhej dein.)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
        return PG_GET_SHORT_LINK 
        
    except Exception as e:
        logger.error(f"Post generate karne me error: {e}", exc_info=True)
        await query.answer("Error! Post generate nahi kar paya.", show_alert=True)
        await query.edit_message_text("❌ Error! Post generate nahi ho paya. Logs check karein.", parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END
        
async def post_gen_get_short_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    short_link_url = update.message.text
    
    caption_raw = context.user_data['post_caption_raw']
    poster_id = context.user_data['post_poster_id']
    btn_backup = context.user_data['btn_backup']
    btn_donate = context.user_data['btn_donate']
    btn_help = context.user_data['btn_help']
    
    btn_download = InlineKeyboardButton("Download", url=short_link_url)
    
    keyboard = [
        [btn_backup, btn_donate],
        [btn_download]            
    ]
    
    context.user_data['post_keyboard'] = InlineKeyboardMarkup(keyboard)
    font_settings = {"font": "default", "style": "normal"}
    caption_formatted = await apply_font_formatting(caption_raw, font_settings)
    context.user_data['post_caption_formatted'] = caption_formatted
    
    await update.message.reply_text("✅ Short Link Saved!\n\nAb uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.\n(Example: @MyMovieChannel ya -100123456789)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return PG_GET_CHAT

async def post_gen_send_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.text
    caption_text = context.user_data['post_caption_formatted']
    
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=context.user_data['post_poster_id'],
            caption=caption_text,
            parse_mode=ParseMode.HTML,
            reply_markup=context.user_data['post_keyboard']
        )

        await update.message.reply_text(f"✅ Success!\nPost ko '{chat_id}' par bhej diya gaya hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Post channel me bhejme me error: {e}")
        await update.message.reply_text(f"❌ Error!\nPost '{chat_id}' par nahi bhej paya. Check karo ki bot uss channel me admin hai ya ID sahi hai.\nError: {e}", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===        GENERATE LINK                 ===
# ============================================
async def gen_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔗 Movie Link", callback_data="gen_link_movie")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "🔗 <b>Generate Download Link</b> 🔗\n\nAap kis cheez ka link generate karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_MENU

async def gen_link_select_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await gen_link_show_movie_list(update, context, page=0)

async def gen_link_show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("genlink_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page 
        
    movies, keyboard = await build_paginated_keyboard(
        collection=movies_collection,
        page=page,
        page_callback_prefix="genlink_page_",
        item_callback_prefix="gen_link_movie_",
        back_callback="admin_gen_link" 
    )
    
    if not movies and page == 0:
        text = "❌ Error: Abhi koi movie add nahi hui hai."
    else:
        text = f"Kaunsi <b>Movie</b> select karna hai?\n\n<b>Recently Updated First</b> (Sabse naya pehle):\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return GL_GET_MOVIE

async def gen_link_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    movie_name = query.data.replace("gen_link_movie_", "")
    
    try:
        bot_username = (await context.bot.get_me()).username
        
        movie_doc = movies_collection.find_one({"name": movie_name})
        movie_id = str(movie_doc['_id'])
        
        dl_callback_data = f"dl{movie_id}" 
        title = movie_name
        
        final_link = f"https://t.me/{bot_username}?start={dl_callback_data}"
        
        await query.edit_message_text(
            f"✅ <b>Link Generated!</b>\n\n<b>Target:</b> {title}\n<b>Link:</b>\n<code>{final_link}</code>\n\nIs link ko copy karke kahin bhi paste karein.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]])
        )
        
    except Exception as e:
        logger.error(f"Link generate karne me error: {e}", exc_info=True)
        await query.edit_message_text("❌ Error! Link generate nahi ho paya. Logs check karein.", parse_mode=ParseMode.HTML)
        
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===        UPDATE PHOTO                  ===
# ============================================
async def update_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await update_photo_show_movie_list(update, context, page=0)

async def update_photo_show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("upphoto_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    movies, keyboard = await build_paginated_keyboard(
        collection=movies_collection,
        page=page,
        page_callback_prefix="upphoto_page_",
        item_callback_prefix="upphoto_movie_",
        back_callback="back_to_update_photo_menu"
    )
    
    if not movies and page == 0:
        text = "❌ Error: Abhi koi movie add nahi hui hai."
    else:
        text = f"Kaunsi <b>Movie</b> ka poster update karna hai?\n\n<b>Recently Updated First</b> (Sabse naya pehle):\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return UP_GET_MOVIE

async def update_photo_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    movie_name = query.data.replace("upphoto_movie_", "")
    context.user_data['movie_name'] = movie_name
    
    await query.edit_message_text(f"Aapne <b>{movie_name}</b> select kiya hai.\n\nAb naya <b>Poster (Photo)</b> bhejo.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return UP_GET_POSTER

async def update_photo_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ye photo nahi hai. Please ek photo bhejo ya /cancel karo.", parse_mode=ParseMode.HTML)
    return UP_GET_POSTER 

async def update_photo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Ye photo nahi hai. Please ek photo bhejo.", parse_mode=ParseMode.HTML)
        return UP_GET_POSTER
    
    poster_id = update.message.photo[-1].file_id
    movie_name = context.user_data['movie_name']
    
    try:
        movies_collection.update_one(
            {"name": movie_name},
            {"$set": {"poster_id": poster_id, "last_modified": datetime.now()}}
        )
        logger.info(f"Main poster change ho gaya: {movie_name}")

        await update.message.reply_photo(photo=poster_id, caption=f"✅ Success!\n{movie_name} ka <b>Main Poster</b> change ho gaya hai.", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Poster change karne me error: {e}")
        await update.message.reply_text("❌ Error! Poster update nahi ho paya.", parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_command(update, context, from_callback=False) 
    return ConversationHandler.END

# ============================================
# ===        OTHER ADMIN FUNCTIONS         ===
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
    text = "❤️ <b>Donation Settings</b> ❤️\n\nSirf QR code se donation accept karein."
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
    text = "🔗 <b>Other Links</b> 🔗\n\nDoosre links yahan set karein."
    if query:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

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
    text = "🛠️ <b>Admin Settings</b> 🛠️\n\nYahan aap Co-Admins aur doosri advanced settings manage kar sakte hain."
    
    if query:
        if query.message.photo:
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🖼️ Update Movie Photo", callback_data="admin_update_photo_content")],
        [InlineKeyboardButton("🖼️ Set User Menu Photo", callback_data="admin_set_menu_photo")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = "🖼️ <b>Photo Settings</b> 🖼️\n\nAap kaunsi photo change karna chahte hain?"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Stats calculate kar raha hoon...", parse_mode=ParseMode.HTML)
    try:
        total_users = users_collection.count_documents({})
        top_users_cursor = users_collection.find({"interaction_count": {"$gt": 0}}).sort("interaction_count", DESCENDING).limit(10)
        top_users_list = []
        for i, user in enumerate(top_users_cursor):
            user_id = user["_id"]
            count = user["interaction_count"]
            name = user.get("full_name") or user.get("first_name", f"User {user_id}")
            name_safe = name.replace('<', '&lt;').replace('>', '&gt;')
            top_users_list.append(f"{i+1}. <code>{user_id}</code> - {name_safe} (<b>{count}</b> hits)")
        if not top_users_list:
            list_str = "Abhi bot par koi top users nahi hain."
        else:
            list_str = "\n".join(top_users_list)
        text = f"📊 <b>User Statistics</b> 📊\n\nTotal Users: <b>{total_users}</b>\n\n🥇 <b>Top 10 Active Users:</b>\n{list_str}"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"User stats dikhane me error: {e}")
        await query.edit_message_text(f"Error: {e}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]))

# ============================================
# ===        BOT APPEARANCE - FIXED        ===
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
    text = f"🎨 <b>Bot Appearance</b> 🎨\n\nBot ke messages ka look aur feel yahaan change karein.\n\nCurrent Font: <b>{font.title()}</b>\nCurrent Style: <b>{style.title()}</b>"
    
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
    
    text = f"Kaunsa font select karna hai?\n\nCurrent: <b>{current_font.title().replace('_', ' ')}</b>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_FONT

async def appearance_save_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    font = query.data.replace("app_font_", "")
    
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"appearance.font": font}},
        upsert=True
    )
    await query.answer(f"Font changed to {font}")
    
    await query.message.reply_text(f"✅ Success! Font ko <b>{font.title().replace('_', ' ')}</b> par set kar diya gaya hai.", parse_mode=ParseMode.HTML)
    
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
    
    text = f"Kaunsa style select karna hai?\n\nCurrent: <b>{current_style.title()}</b>"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_STYLE

async def appearance_save_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    style = query.data.replace("app_style_", "")
    
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"appearance.style": style}},
        upsert=True
    )
    await query.answer(f"Style changed to {style}")
    
    await query.message.reply_text(f"✅ Success! Style ko <b>{style.title()}</b> par set kar diya gaya hai.", parse_mode=ParseMode.HTML)
    
    await appearance_menu_start(update, context)
    return AP_MENU

# ============================================
# ===        SET USER MENU PHOTO           ===
# ============================================
async def set_menu_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("User menu mein dikhaane ke liye <b>Photo</b> bhejo.\n\n/skip - Photo hata do.\n/cancel - Cancel.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_update_photo_menu")]]))
    return CS_MENU_PHOTO

async def set_menu_photo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Ye photo nahi hai. Please ek photo bhejo ya /skip karein.", parse_mode=ParseMode.HTML)
        return CS_MENU_PHOTO

    photo_id = update.message.photo[-1].file_id
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"user_menu_photo_id": photo_id}}, upsert=True)
    logger.info(f"User menu photo update ho gaya.")
    await update.message.reply_photo(photo=photo_id, caption="✅ Success! Naya user menu photo set ho gaya hai.", parse_mode=ParseMode.HTML)

    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

async def skip_menu_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"user_menu_photo_id": None}}, upsert=True)
    logger.info(f"User menu photo remove kar diya gaya.")
    await update.message.reply_text("✅ Success! User menu photo hata diya gaya hai.", parse_mode=ParseMode.HTML)

    await admin_command(update, context, from_callback=False)
    return ConversationHandler.END

# ============================================
# ===        CO-ADMIN FUNCTIONS            ===
# ============================================
async def co_admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Naye Co-Admin ki <b>Telegram User ID</b> bhejein.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return CA_GET_ID

async def co_admin_add_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Yeh valid User ID nahi hai. Please sirf number bhejein.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
        return CA_GET_ID

    if user_id == ADMIN_ID:
        await update.message.reply_text("Aap Main Admin hain, khud ko add nahi kar sakte.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
        return CA_GET_ID

    config = await get_config()
    if user_id in config.get("co_admins", []):
        await update.message.reply_text(f"User <code>{user_id}</code> pehle se Co-Admin hai.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
        return CA_GET_ID

    context.user_data['co_admin_to_add'] = user_id
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Co-Admin Banao", callback_data="co_admin_add_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
    await update.message.reply_text(f"Aap user ID <code>{user_id}</code> ko <b>Co-Admin</b> banane wale hain.\n\nWoh content add, remove, aur post generate kar payenge.\n\n<b>Are you sure?</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
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
        await query.edit_message_text(f"✅ Success!\nUser ID <code>{user_id}</code> ab Co-Admin hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Co-Admin add karne me error: {e}")
        await query.edit_message_text("❌ Error! Co-Admin add nahi ho paya.", parse_mode=ParseMode.HTML)

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
        await query.edit_message_text("Abhi koi Co-Admin nahi hai.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
        return ConversationHandler.END

    buttons = [InlineKeyboardButton(f"Remove {admin_id}", callback_data=f"co_admin_rem_{admin_id}") for admin_id in co_admins]
    keyboard = build_grid_keyboard(buttons, 1) 
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")])
    await query.edit_message_text("Kis Co-Admin ko remove karna hai?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return CR_GET_ID

async def co_admin_remove_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.replace("co_admin_rem_", ""))
    context.user_data['co_admin_to_remove'] = user_id

    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Remove Karo", callback_data="co_admin_rem_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
    await query.edit_message_text(f"Aap Co-Admin ID <code>{user_id}</code> ko remove karne wale hain.\n\n<b>Are you sure?</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
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
        await query.edit_message_text(f"✅ Success!\nCo-Admin ID <code>{user_id}</code> remove ho gaya hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Co-Admin remove karne me error: {e}")
        await query.edit_message_text("❌ Error! Co-Admin remove nahi ho paya.", parse_mode=ParseMode.HTML)

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
        text = "Abhi koi Co-Admin nahi hai."
    else:
        text = "<b>List of Co-Admins:</b>\n"
        for admin_id in co_admins:
            text += f"- <code>{admin_id}</code>\n"

    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return ConversationHandler.END

# ============================================
# ===        CUSTOM POST GENERATOR         ===
# ============================================
async def custom_post_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚀 <b>Custom Post Generator</b>\n\nAb uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.\n(Example: @MyMovieChannel ya -100123456789)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return CPOST_CHAT

async def custom_post_get_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['chat_id'] = update.message.text
    await update.message.reply_text("Chat ID set! Ab post ka <b>Poster (Photo)</b> bhejo.\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return CPOST_POSTER

async def custom_post_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Ye photo nahi hai. Please ek photo bhejo.", parse_mode=ParseMode.HTML)
        return CPOST_POSTER
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    await update.message.reply_text("Poster set! Ab post ka <b>Caption</b> (text) bhejo.\n(Aap <code>&lt;f&gt;...&lt;/f&gt;</code> tags use kar sakte hain)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return CPOST_CAPTION

async def custom_post_get_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['caption'] = update.message.text
    await update.message.reply_text("Caption set! Ab custom button ka <b>Text</b> bhejo.\n(Example: 'Join Now')\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return CPOST_BTN_TEXT

async def custom_post_get_btn_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['btn_text'] = update.message.text
    await update.message.reply_text("Button text set! Ab button ka <b>URL (Link)</b> bhejo.\n(Example: 'https://t.me/mychannel')\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML)
    return CPOST_BTN_URL

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

    await update.message.reply_photo(
        photo=poster_id,
        caption=f"<b>--- PREVIEW ---</b>\n\n{caption_formatted}\n\n<b>Target:</b> <code>{chat_id}</code>",
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
        await query.message.reply_text(f"✅ Success!\nPost ko '{chat_id}' par bhej diya gaya hai.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Custom post bhejme me error: {e}")
        await query.message.reply_text(f"❌ Error!\nPost '{chat_id}' par nahi bhej paya.\nError: {e}", parse_mode=ParseMode.HTML)

    await query.message.delete() 
    context.user_data.clear()
    await admin_settings_menu(update, context)
    return ConversationHandler.END

# ============================================
# ===        BROADCAST                     ===
# ============================================
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📢 <b>Broadcast Message</b>\n\nAb woh message bhejo jo aap sabhi users ko bhejna chahte hain.\n(Text, Photo, Video, kuch bhi...)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return BC_GET_MSG

async def broadcast_get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_message'] = update.message
    
    user_count = users_collection.count_documents({})
    context.user_data['user_count'] = user_count
    
    keyboard = [
        [InlineKeyboardButton(f"✅ Haan, {user_count} Users ko Bhejo", callback_data="broadcast_confirm_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    
    try:
        await update.message.forward(chat_id=update.effective_chat.id)
    except Exception as e:
        logger.warning(f"Broadcast preview forward nahi kar paya: {e}")
        await update.message.reply_text("<b>--- PREVIEW UPAR HAI ---</b>", parse_mode=ParseMode.HTML)

    await update.message.reply_text(f"⚠️ <b>Confirm Karo</b> ⚠️\n\nAap yeh message sabhi <b>{user_count}</b> users ko bhej rahe hain.\n\n<b>Are you sure?</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return BC_CONFIRM

async def broadcast_do_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Broadcasting...")
    
    message_to_send = context.user_data.get('broadcast_message')
    user_count = context.user_data.get('user_count', 0)
    
    if not message_to_send:
        await query.edit_message_text("Error! Message nahi mila. /cancel karke dobara try karein.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    await query.edit_message_text(f"⏳ Broadcast shuru kar raha hoon... Total <b>{user_count}</b> users.\n\nIsme time lag sakta hai. Bot ko band na karein.", parse_mode=ParseMode.HTML)
    
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
        await context.bot.send_message(chat_id=admin_user_id, text=f"✅ <b>Broadcast Complete!</b>\n\nSent to: <b>{sent_count}</b> users\nFailed for: <b>{failed_count}</b> users", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Admin ko broadcast report bhejte waqt error: {e}")

# ============================================
# ===        SET DELETE TIME               ===
# ============================================
async def set_delete_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current_seconds = config.get("delete_seconds", 300) 
    current_minutes = current_seconds // 60
    
    await query.edit_message_text(f"Abhi file auto-delete <b>{current_minutes} minute(s)</b> ({current_seconds} seconds) par set hai.\n\nNaya time <b>seconds</b> mein bhejo.\n(Example: <code>300</code> for 5 minutes)\n\n/cancel - Cancel.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]))
    return CS_GET_DELETE_TIME

async def set_delete_time_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        seconds = int(update.message.text)
        if seconds <= 10:
            await update.message.reply_text("Time 10 second se zyada hona chahiye.", parse_mode=ParseMode.HTML)
            return CS_GET_DELETE_TIME
                
        config_collection.update_one({"_id": "bot_config"}, {"$set": {"delete_seconds": seconds}}, upsert=True)
        logger.info(f"Auto-delete time update ho gaya: {seconds} seconds")
        
        await update.message.reply_text(f"✅ Success! Auto-delete time ab <b>{seconds} seconds</b> ({seconds // 60} min) par set ho gaya hai.", parse_mode=ParseMode.HTML)
        await admin_command(update, context, from_callback=False) 
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("Yeh number nahi hai. Please sirf seconds bhejein (jaise 180) ya /cancel karein.", parse_mode=ParseMode.HTML)
        return CS_GET_DELETE_TIME
    except Exception as e:
        logger.error(f"Delete time save karte waqt error: {e}")
        await update.message.reply_text("❌ Error! Save nahi kar paya.", parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END

# ============================================
# ===        BOT MESSAGES MENU             ===
# ============================================
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
    text = "⚙️ <b>Bot Messages</b> ⚙️\n\nAap bot ke replies ko edit karne ke liye category select karein."
    
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return MM_MAIN

# ============================================
# ===        USER COMMANDS                 ===
# ============================================
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} ne /menu dabaya (Admin Panel).")
    await admin_command(update, context)

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
        await update.message.reply_text("Salaam, Admin! Admin panel ke liye /menu use karein.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"Salaam, {full_name}! Apna user menu dekhne ke liye /user use karein.", parse_mode=ParseMode.HTML)

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

    keyboard = [[btn_backup, btn_donate], [btn_help]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    menu_text = f"Salaam {user.full_name}! Ye raha aapka menu:"

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
        await query.answer("Donation info abhi admin ne set nahi ki hai.", show_alert=True)
        return

    text = "❤️ <b>Support Us!</b>\n\nAgar aapko hamara kaam pasand aata hai, toh aap humein support kar sakte hain."
    
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
            await context.bot.send_message(user.id, "❌ Donation info abhi admin ne set nahi ki hai.", parse_mode=ParseMode.HTML)
            return
        text = "❤️ <b>Support Us!</b>\n\nAgar aapko hamara kaam pasand aata hai, toh aap humein support kar sakte hain."
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="user_back_menu")]]
        await context.bot.send_photo(chat_id=user.id, photo=qr_id, caption=text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
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
                await query.answer("✅ Check your DM (private chat) with me!", show_alert=True)
            else:
                await query.answer()
        
        try:
            checking_text = "⏳ Fetching files..."
            sent_msg = await context.bot.send_message(chat_id=user_id, text=checking_text, parse_mode=ParseMode.HTML)
            checking_msg_id = sent_msg.message_id
        except Exception as e:
            logger.error(f"User {user_id} ko 'Fetching...' message nahi bhej paya. Error: {e}")
            return

        parts = query.data.split('__')
        
        movie_key = parts[0].replace("dl", "")
        quality_to_send = parts[1] if len(parts) > 1 else None
        
        movie_doc = None
        try:
            movie_doc = movies_collection.find_one({"_id": ObjectId(movie_key)})
        except Exception:
            movie_doc = movies_collection.find_one({"name": movie_key})
        
        if not movie_doc:
            await context.bot.send_message(user_id, "❌ Error: Movie nahi mili.", parse_mode=ParseMode.HTML)
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            return
            
        movie_name = movie_doc['name']
        movie_id_str = str(movie_doc['_id'])
        delete_time = config.get("delete_seconds", 300)

        # Quality selected - send file
        if quality_to_send:
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            file_id = movie_doc.get("qualities", {}).get(quality_to_send)
            
            if not file_id:
                await context.bot.send_message(user_id, f"❌ Error! {quality_to_send} file nahi bhej paya. Please try again.", parse_mode=ParseMode.HTML)
                return

            poster_to_use = movie_doc.get("poster_id")
            delete_minutes = max(1, delete_time // 60)
            warning_msg = f"⚠️ Yeh file {delete_minutes} minute(s) mein automatically delete ho jaayegi."
            
            caption = f"🎬 <b>{movie_name}</b> ({quality_to_send})\n\n{warning_msg}"

            try:
                sent_message = await context.bot.send_video(
                    chat_id=user_id,
                    video=file_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    thumbnail=poster_to_use
                )
                asyncio.create_task(delete_message_later(
                    bot=context.bot,
                    chat_id=user_id,
                    message_id=sent_message.message_id,
                    seconds=delete_time
                ))
            except Exception as e:
                logger.error(f"User {user_id} ko file bhejte waqt error: {e}")
                error_msg = "❌ Error! File nahi bhej paya. Aapne bot ko block kiya hua hai." if "blocked" in str(e) else f"❌ Error! {quality_to_send} file nahi bhej paya. Please try again."
                await context.bot.send_message(user_id, error_msg, parse_mode=ParseMode.HTML)
            
            return

        # Movie selected - show qualities
        qualities = movie_doc.get("qualities", {})
        if not qualities:
            await context.bot.send_message(user_id, "❌ Error: Is movie ke liye files nahi mile.", parse_mode=ParseMode.HTML)
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            return
        
        QUALITY_ORDER = ['480p', '720p', '1080p', '4K']
        buttons = []
        for q in QUALITY_ORDER:
            if q in qualities:
                buttons.append(InlineKeyboardButton(f"{q}", callback_data=f"dl{movie_id_str}__{q}"))
        
        keyboard = build_grid_keyboard(buttons, 2)
        keyboard.append([InlineKeyboardButton("⬅️ Back to Bot Menu", callback_data="user_back_menu")])
        
        msg = f"<b>{movie_name}</b>\n\nQuality select karein:"
        
        if checking_msg_id:
            try: await context.bot.delete_message(user_id, checking_msg_id)
            except Exception: pass
        
        poster_to_use = movie_doc['poster_id']
        sent_selection_message = None
        
        try:
            if is_deep_link:
                sent_selection_message = await context.bot.send_photo(
                    chat_id=user_id, photo=poster_to_use, caption=msg,
                    reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML
                )
            else:
                if not query.message.photo:
                    await query.message.delete()
                    sent_selection_message = await context.bot.send_photo(
                        chat_id=user_id, photo=poster_to_use, caption=msg,
                        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML
                    )
                else:
                    await query.edit_message_media(
                        media=InputMediaPhoto(media=poster_to_use, caption=msg, parse_mode=ParseMode.HTML),
                        reply_markup=InlineKeyboardMarkup(keyboard)
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
            if "Message is not modified" not in str(e):
                logger.warning(f"Quality select menu edit nahi kar paya: {e}")
        
        return

    except Exception as e:
        logger.error(f"Download button handler me error: {e}", exc_info=True)
        if checking_msg_id:
            try: await context.bot.delete_message(user_id, checking_msg_id)
            except Exception: pass
        try:
            await context.bot.send_message(user_id, "❌ Error! Please try again.", parse_mode=ParseMode.HTML)
        except Exception: pass

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
    global_cancel_handler = CommandHandler("cancel", cancel)
    
    # Fallbacks
    global_fallbacks = [
        CommandHandler("start", cancel),
        CommandHandler("menu", cancel),
        CommandHandler("admin", cancel),
        global_cancel_handler
    ]
    admin_menu_fallback = [CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$"), global_cancel_handler]
    add_content_fallback = [CallbackQueryHandler(back_to_add_content, pattern="^back_to_add_content$"), global_cancel_handler]
    manage_fallback = [CallbackQueryHandler(back_to_manage, pattern="^back_to_manage$"), global_cancel_handler]
    edit_fallback = [CallbackQueryHandler(back_to_edit_menu, pattern="^back_to_edit_menu$"), global_cancel_handler]
    donate_settings_fallback = [CallbackQueryHandler(back_to_donate_settings, pattern="^back_to_donate_settings$"), global_cancel_handler]
    links_fallback = [CallbackQueryHandler(back_to_links, pattern="^back_to_links$"), global_cancel_handler]
    admin_settings_fallback = [CallbackQueryHandler(back_to_admin_settings, pattern="^back_to_admin_settings$"), global_cancel_handler]
    update_photo_fallback = [CallbackQueryHandler(back_to_update_photo, pattern="^back_to_update_photo_menu$"), global_cancel_handler]
    appearance_fallback = [CallbackQueryHandler(back_to_appearance, pattern="^back_to_appearance$"), global_cancel_handler]
    gen_link_fallback = [CallbackQueryHandler(back_to_gen_link, pattern="^back_to_gen_link$"), global_cancel_handler]

    # Add Movie Conversation
    add_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_movie_start, pattern="^admin_add_movie$")],
        states={
            M_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_get_name)],
            M_GET_POSTER: [MessageHandler(filters.PHOTO, add_movie_get_poster)],
            M_GET_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_get_desc),
                CommandHandler("skip", add_movie_skip_desc)
            ],
            M_GET_480P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_480p), CommandHandler("skip", add_movie_skip_480p)],
            M_GET_720P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_720p), CommandHandler("skip", add_movie_skip_720p)],
            M_GET_1080P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_1080p), CommandHandler("skip", add_movie_skip_1080p)],
            M_GET_4K: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_4k), CommandHandler("skip", add_movie_skip_4k)],
            M_CONFIRM: [CallbackQueryHandler(save_movie, pattern="^save_movie$")]
        },
        fallbacks=global_fallbacks + add_content_fallback,
        allow_reentry=True
    )

    # Delete Movie Conversation
    delete_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_movie_start, pattern="^admin_del_movie$")],
        states={
            DA_GET_MOVIE: [
                CallbackQueryHandler(delete_movie_show_list, pattern="^delmovie_page_"),
                CallbackQueryHandler(delete_movie_confirm, pattern="^del_movie_")
            ],
            DA_CONFIRM: [CallbackQueryHandler(delete_movie_do, pattern="^del_movie_confirm_yes$")]
        },
        fallbacks=global_fallbacks + manage_fallback,
        allow_reentry=True
    )

    # Edit Movie Conversation
    edit_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_movie_start, pattern="^admin_edit_movie$")],
        states={
            EA_GET_MOVIE: [
                CallbackQueryHandler(edit_movie_show_list, pattern="^editmovie_page_"),
                CallbackQueryHandler(edit_movie_get_new_name, pattern="^edit_movie_")
            ],
            EA_GET_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_movie_save)],
            EA_CONFIRM: [CallbackQueryHandler(edit_movie_do, pattern="^edit_movie_confirm_yes$")]
        },
        fallbacks=global_fallbacks + edit_fallback,
        allow_reentry=True
    )

    # Post Generator Conversation
    post_gen_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(post_gen_menu, pattern="^admin_post_gen$")],
        states={
            PG_MENU: [CallbackQueryHandler(post_gen_select_movie, pattern="^post_gen_movie$")],
            PG_GET_MOVIE: [
                CallbackQueryHandler(post_gen_show_movie_list, pattern="^postgen_page_"),
                CallbackQueryHandler(post_gen_ask_shortlink, pattern="^post_movie_")
            ],
            PG_GET_SHORT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_gen_get_short_link)],
            PG_GET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_gen_send_to_chat)]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )

    # Generate Link Conversation
    gen_link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(gen_link_menu, pattern="^admin_gen_link$")],
        states={
            GL_MENU: [CallbackQueryHandler(gen_link_select_movie, pattern="^gen_link_movie$")],
            GL_GET_MOVIE: [
                CallbackQueryHandler(gen_link_show_movie_list, pattern="^genlink_page_"),
                CallbackQueryHandler(gen_link_finish, pattern="^gen_link_movie_")
            ],
        },
        fallbacks=global_fallbacks + gen_link_fallback,
        allow_reentry=True
    )

    # Update Photo Conversation
    update_photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_photo_start, pattern="^admin_update_photo_content$")],
        states={
            UP_GET_MOVIE: [
                CallbackQueryHandler(update_photo_show_movie_list, pattern="^upphoto_page_"),
                CallbackQueryHandler(update_photo_get_poster, pattern="^upphoto_movie_")
            ],
            UP_GET_POSTER: [
                MessageHandler(filters.PHOTO, update_photo_save),
                MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.PHOTO, update_photo_invalid_input)
            ]
        },
        fallbacks=global_fallbacks + update_photo_fallback,
        allow_reentry=True
    )

    # Appearance Conversation
    appearance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(appearance_menu_start, pattern="^admin_menu_appearance$")],
        states={
            AP_MENU: [
                CallbackQueryHandler(appearance_set_font, pattern="^app_set_font$"),
                CallbackQueryHandler(appearance_set_style, pattern="^app_set_style$")
            ],
            AP_FONT: [
                CallbackQueryHandler(appearance_save_font, pattern="^app_font_"),
                CallbackQueryHandler(back_to_appearance, pattern="^back_to_appearance$")
            ],
            AP_STYLE: [
                CallbackQueryHandler(appearance_save_style, pattern="^app_style_"),
                CallbackQueryHandler(back_to_appearance, pattern="^back_to_appearance$")
            ]
        },
        fallbacks=global_fallbacks + appearance_fallback,
        allow_reentry=True
    )

    # Standard commands
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("user", user_command))
    bot_app.add_handler(CommandHandler("menu", menu_command))
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
    bot_app.add_handler(CallbackQueryHandler(set_menu_photo_start, pattern="^admin_set_menu_photo$"))
    bot_app.add_handler(CallbackQueryHandler(co_admin_add_start, pattern="^admin_add_co_admin$"))
    bot_app.add_handler(CallbackQueryHandler(co_admin_remove_start, pattern="^admin_remove_co_admin$"))
    bot_app.add_handler(CallbackQueryHandler(co_admin_list, pattern="^admin_list_co_admin$"))
    bot_app.add_handler(CallbackQueryHandler(custom_post_start, pattern="^admin_custom_post$"))
    bot_app.add_handler(CallbackQueryHandler(broadcast_start, pattern="^admin_broadcast_start$"))
    bot_app.add_handler(CallbackQueryHandler(set_delete_time_start, pattern="^admin_set_delete_time$"))
    bot_app.add_handler(CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"))

    # User menu
    bot_app.add_handler(CallbackQueryHandler(user_show_donate_menu, pattern="^user_show_donate_menu$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"))

    # Download handler
    bot_app.add_handler(CallbackQueryHandler(download_button_handler, pattern="^dl"))

    # Add conversation handlers
    bot_app.add_handler(add_movie_conv)
    bot_app.add_handler(delete_movie_conv)
    bot_app.add_handler(edit_movie_conv)
    bot_app.add_handler(post_gen_conv)
    bot_app.add_handler(gen_link_conv)
    bot_app.add_handler(update_photo_conv)
    bot_app.add_handler(appearance_conv)

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
