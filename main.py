# ============================================
# ===       COMPLETE FINAL FIX (v34)       ===
# ============================================
# === (FEAT: Add Broadcast feature)        ===
# === (FEAT: Add User Statistics)          ===
# === (FIX: Admin menu layout)             ===
# ============================================
import os
import logging
import re # NAYA: Regex ke liye
import asyncio 
import threading 
import httpx 
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING 
from bson.objectid import ObjectId 
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, User, InputMediaPhoto
from telegram.constants import ParseMode # NAYA: HTML ke liye
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
from telegram.error import BadRequest, Forbidden # NAYA: Broadcast ke liye
# Flask server ke liye
from flask import Flask, request 
from waitress import serve 

# --- Font Manager (NAYA FEATURE) ---

# Har font ke liye Normal aur Bold map
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
        'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙', # <-- FIX
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
    # NAYA FONT 1: sans_serif_regular
    'sans_serif_regular': {
        'a': '𝖺', 'b': '𝖻', 'c': '𝖼', 'd': '𝖽', 'e': '𝖾', 'f': '𝖿', 'g': '𝗀', 'h': '𝗁', 'i': '𝗂',
        'j': '𝗃', 'k': '𝗄', 'l': '𝗅', 'm': '𝗆', 'n': '𝗇', 'o': '𝗈', 'p': '𝗉', 'q': '𝗊', 'r': '𝗋',
        's': '𝗌', 't': '𝗍', 'u': '𝗎', 'v': '𝗏', 'w': '𝗐', 'x': '𝗑', 'y': '𝗒', 'z': '𝗓',
        'A': '𝖠', 'B': '𝖡', 'C': '𝖢', 'D': '𝖣', 'E': '𝖤', 'F': '𝖥', 'G': '𝖦', 'H': '𝖧', 'I': '𝖨',
        'J': '𝖩', 'K': '𝖪', 'L': '𝖫', 'M': '𝖬', 'N': '𝖭', 'O': '𝖮', 'P': '𝖯', 'Q': '𝖰', 'R': '𝖱',
        'S': '𝖲', 'T': '𝖳', 'U': '𝖴', 'V': '𝖵', 'W': '𝖶', 'X': '𝖷', 'Y': '𝖸', 'Z': '𝖹',
        '0': '𝟢', '1': '𝟣', '2': '𝟤', '3': '𝟥', '4': '𝟦', '5': '𝟧', '6': '𝟨', '7': '𝟩', '8': '𝟪', '9': '𝟫'
    },
    # NAYA FONT 2: sans_serif_regular_bold
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
        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐', # <-- FIX
        'J': '𝘑', 'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙', # <-- FIX
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
# Small Caps ko bold nahi hota, isliye uska bold map normal hi hai
FONT_MAPS['small_caps_bold'] = FONT_MAPS['small_caps']
# Monospace ka bold nahi hota
FONT_MAPS['monospace_bold'] = FONT_MAPS['monospace']
# Default ke liye bold (yeh sans_serif_regular_bold se alag hai)
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
    """
    <f>...</f> tags ke andar ke text ko font apply karega.
    (FIX v31: HTML tags jaise <b> ko ignore karega)
    """
    font = font_settings.get('font', 'default')
    style = font_settings.get('style', 'normal')
    
    if font == 'default' and style == 'normal':
        return raw_text.replace('<f>', '').replace('</f>', '') # Tags hata do

    # Sahi map select karo
    map_key = f"{font}_{style}" if style == 'bold' else font
    font_map = FONT_MAPS.get(map_key, {})
    
    if not font_map:
        # Fallback
        map_key = 'default_bold' if style == 'bold' else 'default'
        font_map = FONT_MAPS.get(map_key, {})
        if not font_map: # Agar default_bold bhi fail ho
             return raw_text.replace('<f>', '').replace('</f>', '')

    def replace_chars_html_safe(text_chunk):
        # Yeh function sirf plain text par chalega
        return "".join([font_map.get(char, char) for char in text_chunk])

    def process_tags(match):
        content = match.group(1) # <f> ke andar ka content
        
        # Content ko HTML tags aur text me todo
        # Yeh 'Salaam <b>Naam</b>' ko ['Salaam ', '<b>', 'Naam', '</b>', ''] me tod dega
        parts = re.split(r'(<[^>]+>)', content)
        
        processed_parts = []
        for part in parts:
            if re.match(r'<[^>]+>', part):
                # Yeh ek HTML tag hai (jaise <b>), isko chhedo mat
                processed_parts.append(part)
            else:
                # Yeh plain text hai, ispar font apply karo
                processed_parts.append(replace_chars_html_safe(part))
        
        return "".join(processed_parts)

    # <f> tag ke andar sab kuch process karo
    try:
        formatted_text = re.sub(r'<f>(.*?)</f>', process_tags, raw_text, flags=re.DOTALL)
        return formatted_text
    except Exception as e:
        logger.error(f"Font formatting me error: {e}")
        return raw_text.replace('<f>', '').replace('</f>', '')


# --- Baaki ka Bot Code ---
load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Secrets Load Karo ---
try:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID") 
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Optional - Chat with Partner
    DEVELOPER_CONTACT = os.getenv("DEVELOPER_CONTACT", "")  # e.g. https://t.me/username
    
    if not BOT_TOKEN or not MONGO_URI or not ADMIN_ID or not LOG_CHANNEL_ID:
        logger.error("Error: Secrets missing. BOT_TOKEN, MONGO_URI, ADMIN_ID, aur LOG_CHANNEL_ID check karo.")
        exit()
    if not WEBHOOK_URL:
        logger.error("Error: WEBHOOK_URL missing! Render > Environment mein set karo.")
        exit()
except Exception as e:
    logger.error(f"Error reading secrets: {e}")
    exit()

# --- Database Connection ---
try:
    logger.info("MongoDB se connect karne ki koshish...")
    client = MongoClient(MONGO_URI)
    db = client['AnimeBotDB']
    users_collection = db['users']
    animes_collection = db['animes'] 
    config_collection = db['config']
    request_logs_collection = db['request_logs']  # movie request limits
    partner_chat_collection = db['partner_chats']  # AI chat daily limits
    movie_requests_collection = db['movie_requests']  # admin chats panel
    request_bans_collection = db['request_bans']  # temp ban from requests
    
    animes_collection.create_index([("name", ASCENDING)])
    animes_collection.create_index([("created_at", DESCENDING)]) 
    animes_collection.create_index([("last_modified", DESCENDING)]) # NAYA: Smart sort ke liye
    users_collection.create_index([("interaction_count", DESCENDING)]) # NAYA: Stats ke liye
    
    # NAYA v34: Purane users ke liye interaction_count add karo
    users_collection.update_many(
        {"interaction_count": {"$exists": False}},
        {"$set": {"interaction_count": 0}}
    )
    
    client.admin.command('ping') 
    logger.info("MongoDB se successfully connect ho gaya!")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    exit()

ITEMS_PER_PAGE = 15  # 3 columns x 5 rows

# --- NAYA: Admin & Co-Admin Checks ---
async def is_main_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def is_co_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    config = await get_config()
    return user_id in config.get("co_admins", [])

async def is_co_admin_only(user_id: int) -> bool:
    """True if co-admin but NOT main admin"""
    if user_id == ADMIN_ID:
        return False
    return await is_co_admin(user_id)

async def deny_co_admin_feature(update: Update, context: ContextTypes.DEFAULT_TYPE, feature_name: str = "this feature"):
    """Co-admin ko block + Contact Developer button"""
    config = await get_config()
    dev_link = config.get("developer_contact") or DEVELOPER_CONTACT or ""
    text = (
        f"❌ <b>Access Denied</b>\n\n"
        f"Co-Admins cannot use <b>{feature_name}</b>.\n"
        f"Please contact the developer."
    )
    keyboard = []
    if dev_link:
        keyboard.append([InlineKeyboardButton("📞 Contact Developer", url=dev_link if dev_link.startswith("http") else f"https://t.me/{dev_link.lstrip('@')}")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")])
    markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    if query:
        await query.answer("Access denied", show_alert=True)
        try:
            await query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception:
            await context.bot.send_message(query.from_user.id, text, reply_markup=markup, parse_mode=ParseMode.HTML)
    elif update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

# --- NAYA v34: User Stats Helper ---

# --- Request limit: 3 per day per user ---
async def is_request_banned(user_id: int) -> tuple:
    """Returns (banned: bool, message: str)"""
    from datetime import datetime
    doc = request_bans_collection.find_one({"user_id": user_id})
    if not doc:
        return False, ""
    until = doc.get("until")
    if until and until > datetime.utcnow():
        mins = int((until - datetime.utcnow()).total_seconds() // 60)
        return True, f"🚫 You are temporarily banned from requests.\nTry again after <b>{mins} minutes</b>."
    # expired
    request_bans_collection.delete_one({"user_id": user_id})
    return False, ""

def _format_wait(seconds: int) -> str:
    """Seconds to human wait string"""
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


async def _refresh_btn_text():
    config = await get_config()
    return config.get("btn_text_refresh_timer") or "🔄 Refresh Timer"

async def send_request_limit_msg(update_or_user, context, limit_msg: str, user_id: int = None):
    """Limit / cooldown message + Refresh button"""
    rtxt = await _refresh_btn_text()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(rtxt, callback_data="request_timer_refresh")]
    ])
    if hasattr(update_or_user, "message") and update_or_user.message:
        await update_or_user.message.reply_text(limit_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif hasattr(update_or_user, "callback_query") and update_or_user.callback_query:
        try:
            await update_or_user.callback_query.edit_message_text(limit_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await context.bot.send_message(update_or_user.effective_user.id, limit_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        # user object or chat id
        uid = user_id or (update_or_user.id if hasattr(update_or_user, "id") else update_or_user)
        await context.bot.send_message(uid, limit_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)



async def thankyou_timer_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Refreshing...")
    from datetime import datetime
    user_id = query.from_user.id
    doc = db['user_delete_timers'].find_one({"user_id": user_id, "type": "thankyou"})
    rtxt = await _refresh_btn_text()
    # Keep existing keyboard structure roughly
    config = await get_config()
    keyboard = []
    row = []
    p1, p2 = config.get("promo_channel_1"), config.get("promo_channel_2")
    b1 = config.get("promo_btn1_text") or "📢 Join Channel"
    b2 = config.get("promo_btn2_text") or "📢 Join Channel 2"
    if p1: row.append(InlineKeyboardButton(b1, url=p1))
    if p2: row.append(InlineKeyboardButton(b2, url=p2))
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton(rtxt, callback_data="thankyou_timer_refresh")])
    msg = config.get("promo_thank_you_msg") or "🙏 <b>Thank you for your time and consideration!</b>"
    if not doc or not doc.get("deadline"):
        await query.edit_message_text(msg + "\n\n✅ Timer over.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return
    left = int((doc["deadline"] - datetime.utcnow()).total_seconds())
    if left <= 0:
        await query.edit_message_text(msg + "\n\n✅ Timer over.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return
    h, m, s = left // 3600, (left % 3600) // 60, left % 60
    tstr = f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")
    await query.edit_message_text(
        f"{msg}\n\n⏳ <i>This message auto-deletes in <b>{tstr}</b></i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def file_timer_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh remaining auto-delete time — ONLY status message below files.
    File captions (admin ka original warning text) bilkul mat chhedo."""
    query = update.callback_query
    await query.answer("Refreshing...")
    from datetime import datetime
    user_id = query.from_user.id
    doc = db['user_delete_timers'].find_one({"user_id": user_id})
    rtxt = await _refresh_btn_text()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(rtxt, callback_data="file_timer_refresh")]])
    if not doc or not doc.get("deadline"):
        await query.edit_message_text("✅ No active file timer (already deleted or none).", reply_markup=keyboard)
        return
    deadline = doc["deadline"]
    now = datetime.utcnow()
    left = int((deadline - now).total_seconds())
    if left <= 0:
        await query.edit_message_text("✅ Timer over — files should be deleted.", reply_markup=keyboard)
        return
    h, m, s = left // 3600, (left % 3600) // 60, left % 60
    tstr = f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")
    
    # Sirf neeche wala status message update — file warning text same rahega
    try:
        await query.edit_message_text(
            f"⏳ <b>Files auto-delete in:</b> <code>{tstr}</code>\n\nRefresh dabake remaining time dekho.",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.warning(f"file_timer_refresh status edit failed: {e}")

async def request_timer_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh button - show updated remaining time"""
    query = update.callback_query
    await query.answer("Refreshing...")
    user_id = query.from_user.id
    allowed, remaining, limit_msg = await check_request_limit(user_id)
    rtxt = await _refresh_btn_text()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(rtxt, callback_data="request_timer_refresh")]
    ])
    if allowed:
        text = (
            f"✅ <b>You can request now!</b>\n\n"
            f"Remaining today: <b>{remaining}/3</b>\n\n"
            f"Send /request or tap Request a Movie."
        )
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await query.edit_message_text(limit_msg, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def check_request_limit(user_id: int) -> tuple:
    """Returns (allowed: bool, remaining: int, message: str)
    Rules: max 3 / 24h AND 8 hours gap between each request.
    """
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    
    # Ban check (admin 3h ban)
    ban = db['request_bans'].find_one({"user_id": user_id, "until": {"$gt": now}})
    if ban:
        left = int((ban["until"] - now).total_seconds())
        return False, 0, (
            f"🚫 <b>You are temporarily banned from requesting.</b>\n\n"
            f"⏳ Wait: <b>{_format_wait(left)}</b>"
        )
    
    day_ago = now - timedelta(hours=24)
    recent = list(request_logs_collection.find(
        {"user_id": user_id, "created_at": {"$gte": day_ago}}
    ).sort("created_at", -1))
    count = len(recent)
    limit = 3
    remaining = max(0, limit - count)
    
    # Daily limit
    if count >= limit:
        # Next available = 24h after oldest of last 3, or after newest+8h - simpler: 24h from first of today window
        oldest = recent[-1]["created_at"] if recent else now
        unlock = oldest + timedelta(hours=24)
        left = int((unlock - now).total_seconds())
        return False, 0, (
            f"⏳ <b>Daily limit reached (3 requests).</b>\n\n"
            f"Wait: <b>{_format_wait(left)}</b>\n"
            f"You can request again after cooldown."
        )
    
    # 8 hour gap after last request
    if recent:
        last = recent[0]["created_at"]
        unlock = last + timedelta(hours=8)
        if now < unlock:
            left = int((unlock - now).total_seconds())
            return False, remaining, (
                f"⏳ <b>Please wait before next request.</b>\n\n"
                f"Cooldown left: <b>{_format_wait(left)}</b>\n"
                f"Gap: 8 hours between requests.\n"
                f"Daily remaining after wait: <b>{remaining}/3</b>"
            )
    
    return True, remaining, ""

async def log_movie_request(user_id: int):
    from datetime import datetime
    request_logs_collection.insert_one({
        "user_id": user_id,
        "created_at": datetime.utcnow()
    })

# --- Partner chat limit: 1000 replies per day ---
async def check_partner_chat_limit(user_id: int) -> tuple:
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    doc = partner_chat_collection.find_one({"user_id": user_id, "date": start.strftime("%Y-%m-%d")})
    count = (doc or {}).get("count", 0)
    if count >= 1000:
        return False, 0
    return True, 1000 - count

async def inc_partner_chat(user_id: int):
    from datetime import datetime
    day = datetime.utcnow().strftime("%Y-%m-%d")
    partner_chat_collection.update_one(
        {"user_id": user_id, "date": day},
        {"$inc": {"count": 1}, "$setOnInsert": {"user_id": user_id, "date": day}},
        upsert=True
    )

async def call_groq_partner(user_message: str, language: str, history: list = None) -> str:
    """Groq free API - partner style chat"""
    if not GROQ_API_KEY:
        return "⚠️ AI Partner is not configured. Admin must set GROQ_API_KEY."
    lang_map = {
        "english": "English",
        "hindi": "Hindi",
        "hinglish": "Hinglish (Hindi+English mix)",
        "bengali": "Bengali",
        "arabic": "Arabic",
    }
    lang_name = lang_map.get(language, "English")
    system = (
        f"You are a friendly chat partner. Reply only in {lang_name}. "
        f"Be helpful, short and natural. You help users about movies/series requests casually. "
        f"Do not mention you are an AI unless asked."
    )
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_message})
    try:
        import urllib.request
        import json as _json
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=_json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7,
            }).encode(),
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "⚠️ Partner is busy right now. Please try again later."


async def increment_user_interaction(user_id: int):
    """User ki interaction count badhayega."""
    try:
        users_collection.update_one(
            {"_id": user_id},
            {"$inc": {"interaction_count": 1}}
        )
    except Exception as e:
        logger.error(f"User {user_id} ka interaction_count update karne me error: {e}")


# --- NAYA: Message Formatting Helper (v32 FIX) ---
async def format_message(context: ContextTypes.DEFAULT_TYPE, key: str, variables: dict = None) -> str:
    """
    DB se message laayega, variables replace karega, aur font apply karega.
    (FIX: Pehle variables replace karo, phir font apply karo)
    """
    config = await get_config()
    
    # 1. Message template - ADMIN CUSTOM (DB) pehle, phir language pack, phir default
    default_messages = await get_default_messages()
    lang = config.get("bot_language", "hinglish")
    
    raw_text = None
    # Custom messages (Bot Messages se set) hamesha sabse pehle
    raw_text = (config.get("messages") or {}).get(key)
    if not raw_text and lang and lang != "hinglish" and lang in LANGUAGE_PACKS:
        raw_text = LANGUAGE_PACKS[lang].get(key)
    if not raw_text:
        raw_text = default_messages.get(key, f"MISSING_KEY: {key}")
    
    # 2. Variables (jaise {anime_name}) replace karo (PEHLE)
    if variables:
        # Variables ko HTML-safe banao (agar woh text hain)
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
            # Koshish karo ki problem waale variable ke bina format ho
            try:
                text_with_vars = raw_text.format_map(safe_variables)
            except:
                text_with_vars = raw_text # Fallback
        except Exception as e:
             logger.error(f"Message format karne me error: {e} (Key: {key})")
             text_with_vars = raw_text # Fallback
    else:
        text_with_vars = raw_text

    # 3. Font settings apply karo (BAAD MEIN)
    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    formatted_text = await apply_font_formatting(text_with_vars, font_settings)

    return formatted_text


# --- NAYA: Saare Default Messages Ek Jagah (v34 Update) ---

# ============================================
# ===     MULTI LANGUAGE PACKS             ===
# ============================================
LANGUAGE_PACKS = {
    "english": {
        "admin_panel_main": "👑 <b><f>Hello, Admin!</f></b> 👑\n<f>Your control panel is ready.</f>",
        "admin_panel_co": "👑 <b><f>Hello, Co-Admin!</f></b> 👑\n<f>Your content panel is ready.</f>",
        "admin_menu_add_content": "➕ <b><f>Add Content</f></b> ➕\n\n<f>What do you want to add?</f>",
        "admin_menu_post_gen": "✍️ <b><f>Post Generator</f></b> ✍️\n\n<f>What type of post do you want to generate?</f>",
        "admin_cancel": "<f>Operation cancelled.</f>",
        "user_request_limit": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "user_request_prompt": "🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel",
        "user_request_received": "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience.",
        "user_request_admin_notify": "📩 <b>New Movie Request</b>\n\nFrom: {name} (@{username})\nID: <code>{user_id}</code>\n\n{text}\n\n💡 <i>Is message pe Reply karke user ko jawab do.</i>",
        "user_request_cancelled": "❌ Request cancelled.",
        "user_dl_anime_not_found": "❌ <f>Error: Series/Movie not found.</f>",
        "user_dl_select_season": "<b>{anime_name}</b>\n\n<f>Select season:</f>",
        "user_dl_select_episode": "<b>{anime_name}</b> | <b>Season {season_name}</b>\n\n<f>Select episode:</f>",
        "user_dl_sending_files": "✅ <b>{anime_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>Sending all your files...</f>",
        "file_warning": "⚠️ <b><f>This file will auto-delete in {time}</f></b> ({minutes} min).",
    },
    "hindi": {
        "admin_panel_main": "👑 <b><f>नमस्ते, एडमिन!</f></b> 👑\n<f>आपका कंट्रोल पैनल तैयार है।</f>",
        "admin_panel_co": "👑 <b><f>नमस्ते, को-एडमिन!</f></b> 👑\n<f>आपका कंटेंट पैनल तैयार है।</f>",
        "admin_menu_add_content": "➕ <b><f>कंटेंट जोड़ें</f></b> ➕\n\n<f>आप क्या जोड़ना चाहते हैं?</f>",
        "admin_menu_post_gen": "✍️ <b><f>पोस्ट जनरेटर</f></b> ✍️\n\n<f>किस तरह की पोस्ट बनानी है?</f>",
        "admin_cancel": "<f>ऑपरेशन रद्द कर दिया गया।</f>",
        "user_request_limit": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "user_request_prompt": "🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel",
        "user_request_received": "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience.",
        "user_request_admin_notify": "📩 <b>New Movie Request</b>\n\nFrom: {name} (@{username})\nID: <code>{user_id}</code>\n\n{text}\n\n💡 <i>Is message pe Reply karke user ko jawab do.</i>",
        "user_request_cancelled": "❌ Request cancelled.",
        "user_dl_anime_not_found": "❌ <f>त्रुटि: सीरीज़/मूवी नहीं मिली।</f>",
        "user_dl_select_season": "<b>{anime_name}</b>\n\n<f>सीज़न चुनें:</f>",
        "user_dl_select_episode": "<b>{anime_name}</b> | <b>सीज़न {season_name}</b>\n\n<f>एपिसोड चुनें:</f>",
        "user_dl_sending_files": "✅ <b>{anime_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>आपकी सभी फाइलें भेज रहा हूँ...</f>",
        "file_warning": "⚠️ <b><f>यह फाइल {minutes} मिनट में अपने आप डिलीट हो जाएगी।</f></b>",
    },
    "bengali": {
        "admin_panel_main": "👑 <b><f>নমস্কার, অ্যাডমিন!</f></b> 👑\n<f>আপনার কন্ট্রোল প্যানেল প্রস্তুত।</f>",
        "admin_panel_co": "👑 <b><f>নমস্কার, কো-অ্যাডমিন!</f></b> 👑\n<f>আপনার কন্টেন্ট প্যানেল প্রস্তুত।</f>",
        "admin_menu_add_content": "➕ <b><f>কন্টেন্ট যোগ করুন</f></b> ➕\n\n<f>আপনি কী যোগ করতে চান?</f>",
        "admin_menu_post_gen": "✍️ <b><f>পোস্ট জেনারেটর</f></b> ✍️\n\n<f>কী ধরনের পোস্ট তৈরি করবেন?</f>",
        "admin_cancel": "<f>অপারেশন বাতিল করা হয়েছে।</f>",
        "user_request_limit": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "user_request_prompt": "🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel",
        "user_request_received": "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience.",
        "user_request_admin_notify": "📩 <b>New Movie Request</b>\n\nFrom: {name} (@{username})\nID: <code>{user_id}</code>\n\n{text}\n\n💡 <i>Is message pe Reply karke user ko jawab do.</i>",
        "user_request_cancelled": "❌ Request cancelled.",
        "user_dl_anime_not_found": "❌ <f>ত্রুটি: সিরিজ/মুভি পাওয়া যায়নি।</f>",
        "user_dl_select_season": "<b>{anime_name}</b>\n\n<f>সিজন বেছে নিন:</f>",
        "user_dl_select_episode": "<b>{anime_name}</b> | <b>সিজন {season_name}</b>\n\n<f>এপিসোড বেছে নিন:</f>",
        "user_dl_sending_files": "✅ <b>{anime_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>আপনার সব ফাইল পাঠাচ্ছি...</f>",
        "file_warning": "⚠️ <b><f>এই ফাইল {minutes} মিনিটে নিজে থেকে মুছে যাবে।</f></b>",
    },
    "arabic": {
        "admin_panel_main": "👑 <b><f>مرحباً أيها المشرف!</f></b> 👑\n<f>لوحة التحكم جاهزة.</f>",
        "admin_panel_co": "👑 <b><f>مرحباً أيها المشرف المساعد!</f></b> 👑\n<f>لوحة المحتوى جاهزة.</f>",
        "admin_menu_add_content": "➕ <b><f>إضافة محتوى</f></b> ➕\n\n<f>ماذا تريد أن تضيف؟</f>",
        "admin_menu_post_gen": "✍️ <b><f>مولّد المنشورات</f></b> ✍️\n\n<f>ما نوع المنشور؟</f>",
        "admin_cancel": "<f>تم إلغاء العملية.</f>",
        "user_request_limit": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "user_request_prompt": "🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel",
        "user_request_received": "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience.",
        "user_request_admin_notify": "📩 <b>New Movie Request</b>\n\nFrom: {name} (@{username})\nID: <code>{user_id}</code>\n\n{text}\n\n💡 <i>Is message pe Reply karke user ko jawab do.</i>",
        "user_request_cancelled": "❌ Request cancelled.",
        "user_dl_anime_not_found": "❌ <f>خطأ: السلسلة/الفيلم غير موجود.</f>",
        "user_dl_select_season": "<b>{anime_name}</b>\n\n<f>اختر الموسم:</f>",
        "user_dl_select_episode": "<b>{anime_name}</b> | <b>الموسم {season_name}</b>\n\n<f>اختر الحلقة:</f>",
        "user_dl_sending_files": "✅ <b>{anime_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>جاري إرسال جميع الملفات...</f>",
        "file_warning": "⚠️ <b><f>سيتم حذف هذا الملف تلقائياً خلال {minutes} دقيقة.</f></b>",
    },
    # hinglish = default messages (already in get_default_messages)
}


async def get_default_messages():
    """
    Saare default messages ki list, <f> tags aur HTML ke saath.
    """
    return {
        # === Download Flow ===
        "user_dl_dm_alert": "✅ <f>Check your DM (private chat) with me!</f>",
        "user_request_limit": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "user_request_prompt": "🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel",
        "user_request_received": "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience.",
        "user_request_admin_notify": "📩 <b>New Movie Request</b>\n\nFrom: {name} (@{username})\nID: <code>{user_id}</code>\n\n{text}\n\n💡 <i>Is message pe Reply karke user ko jawab do.</i>",
        "user_request_cancelled": "❌ Request cancelled.",
        "user_dl_anime_not_found": "❌ <f>Error: Series/Movie nahi mila.</f>",
        "request_limit_reached": "⏳ <b>You can request a movie after the bot cooldown.</b>\n\nLimit: <b>3 requests per day</b>.",
        "request_start": "🎬 <b>Request a Movie</b>\n\nRemaining today: <b>{remaining}/3</b>\n\nApni movie/series ka naam bhejo.\n/cancel - Cancel",
        "request_received": "✅ <b>Your request has been received.</b>\n\n<i>Developer will update it shortly. Please keep patience.</i>\n\nRemaining today: <b>{remaining}/3</b>",
        "request_cancelled": "❌ Request cancelled.",
        "request_admin_notify": "🎬 <b>NEW MOVIE REQUEST</b>\n\nFrom: <b>{name}</b> ({username})\nID: <code>{user_id}</code>\n\nRequest:\n<code>{request_text}</code>\n\n<i>Is message pe Reply karke user ko jawab bhej sakte ho.</i>",
        "request_dev_reply_prefix": "📩 <b>Developer Reply:</b>\n\n{reply}",

        "user_dl_file_error": "❌ <f>Error! {quality} file nahi bhej paya. Please try again.</f>",
        "user_dl_blocked_error": "❌ <f>Error! File nahi bhej paya. Aapne bot ko block kiya hua hai.</f>",
        "user_dl_episodes_not_found": "❌ <f>Error: Is season ke liye episodes nahi mile.</f>",
        "user_dl_seasons_not_found": "❌ <f>Error: Is Series ke liye seasons nahi mile.</f>",
        "user_dl_general_error": "❌ <f>Error! Please try again.</f>",
        "user_dl_sending_files": "✅ <b>{anime_name}</b> | <b>S{season_name}</b> | <b>E{ep_num}</b>\n\n<f>Aapke saare files bhej raha hoon...</f>",
        "user_dl_select_episode": "<b>{anime_name}</b> | <b>Season {season_name}</b>\n\n<f>Episode select karein:</f>",
        "user_dl_select_season": "<b>{anime_name}</b>\n\n<f>Season select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {time} mein auto-delete ho jaayegi.</f></b>",
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
        "post_gen_anime_caption": "✅ <b>{anime_name}</b>\n\n<b><f>📖 Synopsis:</f></b>\n{description}\n\n<f>Neeche [Download] button dabake download karein!</f>",
        "post_gen_season_caption": "✅ <b>{anime_name}</b>\n<b>[ S{season_name} ]</b>\n\n<b><f>📖 Synopsis:</f></b>\n{description}\n\n<f>Neeche [Download] button dabake download karein!</f>",
        "post_gen_episode_caption": "✨ <b><f>Episode {ep_num} Added</f></b> ✨\n\n🎬 <b><f>Series:</f></b> {anime_name}\n➡️ <b><f>Season:</f></b> {season_name}\n\n<f>Neeche [Download] button dabake download karein!</f>",

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

        # === Admin: Add Anime ===
        "admin_add_anime_start": "<f>Salaam Admin! Series ka <b>Naam</b> kya hai?</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_anime_get_name": "<f>Badhiya! Ab Series ka <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_anime_get_poster_error": "Ye photo nahi hai. Please ek photo bhejo.",
        "admin_add_anime_get_poster": "<f>Poster mil gaya! Ab <b>Description (Synopsis)</b> bhejo.</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_anime_confirm": "<b>{name}</b>\n\n{description}\n\n<f>--- Details Check Karo ---</f>",
        "admin_add_anime_confirm_error": "❌ <f>Error: Poster bhej nahi paya. Dobara try karein ya</f> /cancel.",
        "admin_add_anime_save_exists": "⚠️ <b><f>Error:</f></b> <f>Ye Series naam</f> '{name}' <f>pehle se hai.</f>",
        "admin_add_anime_save_success": "✅ <b><f>Success!</f></b> '{name}' <f>add ho gaya hai.</f>",
        "admin_add_anime_save_error": "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>",

        # === Admin: Add Season ===
        "admin_add_season_select_anime": "<f>Aap kis Series mein season add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_add_season_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai. Pehle 'Add Series' se add karein.</f>",
        "admin_add_season_get_anime": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_anime_with_last": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n<f>Last added season:</f> <b>{last_season_name}</b>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_anime_no_last": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n<f>Is Series mein abhi koi season nahi hai.</f>\n\n<f>Ab is season ka <b>Number ya Naam</b> bhejo.</f>\n<f>(Jaise: 1, 2, Movie)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_number_error": "⚠️ <b><f>Error!</f></b> <f>Series</f> '{anime_name}' <f>database mein nahi mila.</f> /cancel <f>karke dobara try karein.</f>",
        "admin_add_season_get_number_exists": "⚠️ <b><f>Error!</f></b> '{anime_name}' <f>mein 'Season {season_name}' pehle se hai.</f>\n\n<f>Koi doosra naam/number type karein ya</f> /cancel <f>karein.</f>",
        "admin_add_season_get_poster_prompt": "<f>Aapne Season</f> '{season_name}' <f>select kiya hai.</f>\n\n<f>Ab is season ka <b>Poster (Photo)</b> bhejo.</f>\n\n/skip - <f>Default Series poster use karo.</f>\n/cancel - <f>Cancel.</f>",
        "admin_add_season_get_poster_error": "<f>Ye photo nahi hai. Please ek photo bhejo.</f>",
        "admin_add_season_get_desc_prompt": "<f>Poster mil gaya! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_season_skip_poster": "<f>Default poster set! Ab is season ka <b>Description</b> bhejo.</f>\n<f>(Yeh post generator mein use hoga)</f>\n\n/skip <f>ya</f> /cancel.",
        "admin_add_season_confirm": "<b><f>Confirm Karo:</f></b>\n<f>Series:</f> <b>{anime_name}</b>\n<f>Naya Season:</f> <b>{season_name}</b>\n<f>Description:</f> {season_desc}\n\n<f>Save kar doon?</f>",
        "admin_add_season_save_success": "✅ <b><f>Success!</f></b>\n<b>{anime_name}</b> <f>mein</f> <b>Season {season_name}</b> <f>add ho gaya hai.</f>",
        "admin_add_season_save_error": "❌ <b><f>Error!</f></b> <f>Database me save nahi kar paya.</f>",
        "admin_add_season_ask_more": "✅ <f>Season</f> <b>{season_name}</b> <f>save ho gaya!</f>\n\n<f>Aap</f> <b>{anime_name}</b> <f>mein aur season add karna chahte hain?</f>", 
        "admin_add_season_next_prompt": "<f>Last Season:</f> <b>{season_name}</b>. <f>Series:</f> <b>{anime_name}</b>\n\n<f>Ab agla <b>Season Number/Naam</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        
        # === Admin: Add Episode ===
        "admin_add_ep_select_anime": "<f>Aap kis Series mein episode add karna chahte hain?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_add_ep_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai. Pehle 'Add Series' se add karein.</f>",
        "admin_add_ep_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>\n\n<f>Pehle</f> <code>➕ Add Season</code> <f>se season add karo.</f>",
        "admin_add_ep_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_add_ep_get_season_with_last": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Last added episode:</f> <b>{last_ep_num}</b>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n<f>(Agar yeh ek movie hai, toh</f> <code>1</code> <f>type karein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_get_season_no_last": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n<f>Is season mein abhi koi episode nahi hai.</f>\n\n<f>Ab <b>Episode Number</b> bhejo.</f>\n<f>(Jaise: 1, 2, 3...)</f>\n<f>(Agar yeh ek movie hai, toh</f> <code>1</code> <f>type karein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_add_ep_get_number": "<f>Aapne</f> <b>Episode {ep_num}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>480p</b> quality ki video file bhejein.</f>\n<f>Ya</f> /skip <f>type karein.</f>",
        "admin_add_ep_get_number_exists": "⚠️ <b><f>Error!</f></b> '{anime_name}' - Season {season_name} - Episode {ep_num} <f>pehle se maujood hai. Please pehle isse delete karein ya koi doosra episode number dein.</f>\n\n/cancel - <f>Cancel.</f>",
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
        
        # === Admin: Settings (Donate, Links, Delete Time) ===
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

        # === Admin: Bot Messages Menu ===
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
        "admin_post_gen_select_anime": "<f>Kaunsa <b>Series/Movie</b> select karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_post_gen_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_post_gen_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_post_gen_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_post_gen_no_episode": "❌ <b><f>Error!</f></b> '{anime_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_post_gen_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Episode</b> select karein:</f>",
        "admin_post_gen_ask_shortlink": "✅ <b><f>Post Ready!</f></b>\n\n<f>Aapka original download link hai:</f>\n<code>{original_download_url}</code>\n\n<f>Please iska <b>shortened link</b> reply mein bhejein.</f>\n<f>(Agar link change nahi karna hai, toh upar waala link hi copy karke bhej dein.)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_post_gen_ask_chat": "✅ <b><f>Short Link Saved!</f></b>\n\n<f>Ab uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.</f>\n<f>(Example: @MyAnimeChannel ya -100123456789)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_post_gen_success": "✅ <b><f>Success!</f></b>\n<f>Post ko</f> '{chat_id}' <f>par bhej diya gaya hai.</f>",
        "admin_post_gen_error": "❌ <b><f>Error!</f></b>\n<f>Post</f> '{chat_id}' <f>par nahi bhej paya. Check karo ki bot uss channel me admin hai ya ID sahi hai.</f>\n<f>Error:</f> {e}",
        "admin_post_gen_invalid_state": "❌ <f>Error! Invalid state. Please start over.</f>",
        "admin_post_gen_error_general": "❌ <b><f>Error!</f></b> <f>Post generate nahi ho paya. Logs check karein.</f>",
        
        # === Admin: Generate Link ===
        "admin_menu_gen_link": "🔗 <b><f>Generate Download Link</f></b> 🔗\n\n<f>Aap kis cheez ka link generate karna chahte hain?</f>",
        "admin_gen_link_select_anime": "<f>Kaunsa <b>Series/Movie</b> select karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_gen_link_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_gen_link_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_gen_link_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Season</b> select karein:</f>",
        "admin_gen_link_no_episode": "❌ <b><f>Error!</f></b> '{anime_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_gen_link_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab <b>Episode</b> select karein:</f>",
        "admin_gen_link_success": "✅ <b><f>Link Generated!</f></b>\n\n<b><f>Target:</f></b> {title}\n<b><f>Link:</f></b>\n<code>{final_link}</code>\n\n<f>Is link ko copy karke kahin bhi paste karein.</f>",
        "admin_gen_link_error": "❌ <b><f>Error!</f></b> <f>Link generate nahi ho paya. Logs check karein.</f>",

        # === Admin: Delete Series/Movie ===
        "admin_del_anime_select": "<f>Kaunsa <b>Series/Movie</b> delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_anime_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_del_anime_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{anime_name}</b> <f>ko delete karne wale hain. Iske saare seasons aur episodes delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_anime_success": "✅ <b><f>Success!</f></b>\n<f>Series</f> '{anime_name}' <f>delete ho gaya hai.</f>",
        "admin_del_anime_error": "❌ <b><f>Error!</f></b> <f>Series/Movie delete nahi ho paya.</f>",
        
        # === Admin: Delete Season ===
        "admin_del_season_select_anime": "<f>Kaunse <b>Series</b> ka season delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_season_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_del_season_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_del_season_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> delete karna hai?</f>",
        "admin_del_season_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{anime_name}</b> <f>ka</f> <b>Season {season_name}</b> <f>delete karne wale hain. Iske saare episodes delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_season_success": "✅ <b><f>Success!</f></b>\n<f>Season</f> '{season_name}' <f>delete ho gaya hai.</f>",
        "admin_del_season_error": "❌ <b><f>Error!</f></b> <f>Season delete nahi ho paya.</f>",

        # === Admin: Delete Episode ===
        "admin_del_ep_select_anime": "<f>Kaunse <b>Series</b> ka episode delete karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_del_ep_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_del_ep_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_del_ep_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> delete karna hai?</f>",
        "admin_del_ep_no_episode": "❌ <b><f>Error!</f></b> '{anime_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_del_ep_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Episode</b> delete karna hai?</f>",
        "admin_del_ep_confirm": "⚠️ <b><f>FINAL WARNING</f></b> ⚠️\n\n<f>Aap</f> <b>{anime_name}</b> - <b>S{season_name}</b> - <b>Ep {ep_num}</b> <f>delete karne wale hain. Iske saare qualities delete ho jayenge.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_del_ep_success": "✅ <b><f>Success!</f></b>\n<f>Episode</f> '{ep_num}' <f>delete ho gaya hai.</f>",
        "admin_del_ep_error": "❌ <b><f>Error!</f></b> <f>Episode delete nahi ho paya.</f>",

        # === Admin: Update Photo ===
        "admin_menu_update_photo": "🖼️ <b><f>Photo Settings</f></b> 🖼️\n\n<f>Aap kaunsi photo change karna chahte hain?</f>",
        "admin_update_photo_select_anime": "<f>Kaunse <b>Series/Movie</b> ka poster update karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_update_photo_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_update_photo_select_target": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Aap iska <b>Main Poster</b> change karna chahte hain ya kisi <b>Season</b> ka?</f>",
        "admin_update_photo_get_poster": "<f>Aapne</f> <b>{target_name}</b> <f>select kiya hai.</f>\n\n<f>Ab naya <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_update_photo_invalid": "<f>Ye photo nahi hai. Please ek photo bhejo ya</f> /cancel <f>karo.</f>",
        "admin_update_photo_save_error": "<f>Ye photo nahi hai. Please ek photo bhejo.</f>",
        "admin_update_photo_save_success_main": "✅ <b><f>Success!</f></b>\n{anime_name} <f>ka <b>Main Poster</b> change ho gaya hai.</f>",
        "admin_update_photo_save_success_season": "✅ <b><f>Success!</f></b>\n{anime_name} - <b>Season {season_name}</b> <f>ka poster change ho gaya hai.</f>",
        "admin_update_photo_save_error_db": "❌ <b><f>Error!</f></b> <f>Poster update nahi ho paya.</f>",

        # === Admin: Edit Anime ===
        "admin_edit_anime_select": "<f>Kaunsa <b>Series/Movie</b> ka naam edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_anime_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_edit_anime_get_name": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Naam</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_anime_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya naam</f> '{new_name}' <f>pehle se maujood hai. Koi doosra naam dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_anime_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>Purana Naam:</f> <code>{old_name}</code>\n<f>Naya Naam:</f> <code>{new_name}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_anime_success": "✅ <b><f>Success!</f></b>\n<f>Anime</f> '{old_name}' <f>ka naam badal kar</f> '{new_name}' <f>ho gaya hai.</f>",
        "admin_edit_anime_error": "❌ <b><f>Error!</f></b> <f>Anime naam update nahi ho paya.</f>",
        
        # === Admin: Edit Season ===
        "admin_edit_season_select_anime": "<f>Kaunse <b>Series</b> ka season edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_season_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_edit_season_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_edit_season_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> ka naam edit karna hai?</f>",
        "admin_edit_season_get_name": "<f>Aapne</f> <b>{anime_name}</b> -> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Naam/Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_season_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya naam</f> '{new_name}' <f>is anime mein pehle se maujood hai. Koi doosra naam dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_season_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>Anime:</f> <code>{anime_name}</code>\n<f>Purana Season:</f> <code>{old_name}</code>\n<f>Naya Season:</f> <code>{new_name}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_season_success": "✅ <b><f>Success!</f></b>\n<f>Season</f> '{old_name}' <f>ka naam badal kar</f> '{new_name}' <f>ho gaya hai.</f>",
        "admin_edit_season_error": "❌ <b><f>Error!</f></b> <f>Season naam update nahi ho paya.</f>",

        # === Admin: Edit Episode ===
        "admin_edit_ep_select_anime": "<f>Kaunse <b>Series</b> ka episode edit karna hai?</f>\n\n<b><f>Recently Updated First</f></b> <f>(Sabse naya pehle):</f>\n<f>(Page {page})</f>",
        "admin_edit_ep_no_anime": "❌ <f>Error: Abhi koi Series/Movie add nahi hua hai.</f>",
        "admin_edit_ep_no_season": "❌ <b><f>Error!</f></b> '{anime_name}' <f>mein koi season nahi hai.</f>",
        "admin_edit_ep_select_season": "<f>Aapne</f> <b>{anime_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Season</b> select karna hai?</f>",
        "admin_edit_ep_no_episode": "❌ <b><f>Error!</f></b> '{anime_name}' - Season {season_name} <f>mein koi episode nahi hai.</f>",
        "admin_edit_ep_select_episode": "<f>Aapne</f> <b>Season {season_name}</b> <f>select kiya hai.</f>\n\n<f>Kaunsa <b>Episode</b> ka number edit karna hai?</f>",
        "admin_edit_ep_get_num": "<f>Aapne</f> <b>{anime_name}</b> -> <b>S{season_name}</b> -> <b>Ep {ep_num}</b> <f>select kiya hai.</f>\n\n<f>Ab iska <b>Naya Number</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_ep_save_exists": "⚠️ <b><f>Error!</f></b> <f>Naya number</f> '{new_num}' <f>is season mein pehle se maujood hai. Koi doosra number dein.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_edit_ep_confirm": "<b><f>Confirm Karo:</f></b>\n\n<f>Anime:</f> <code>{anime_name}</code>\n<f>Season:</f> <code>{season_name}</code>\n<f>Purana Episode:</f> <code>{old_num}</code>\n<f>Naya Episode:</f> <code>{new_num}</code>\n\n<b><f>Are you sure?</f></b>",
        "admin_edit_ep_success": "✅ <b><f>Success!</f></b>\n<f>Episode</f> '{old_num}' <f>ka number badal kar</f> '{new_num}' <f>ho gaya hai.</f>",
        "admin_edit_ep_error": "❌ <b><f>Error!</f></b> <f>Episode number update nahi ho paya.</f>",

        # === Admin: Admin Settings (Co-Admin, Custom Post) ===
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
        "admin_custom_post_start": "🚀 <b><f>Custom Post Generator</f></b>\n\n<f>Ab uss <b>Channel ka @username</b> ya <b>Group/Channel ki Chat ID</b> bhejo jahaan ye post karna hai.</f>\n<f>(Example: @MyAnimeChannel ya -100123456789)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_chat": "<f>Chat ID set! Ab post ka <b>Poster (Photo)</b> bhejo.</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_poster_error": "<f>Ye photo nahi hai. Please ek photo bhejo.</f>",
        "admin_custom_post_get_poster": "<f>Poster set! Ab post ka <b>Caption</b> (text) bhejo.</f>\n<f>(Aap</f> <code>&lt;f&gt;...&lt;/f&gt;</code> <f>tags use kar sakte hain)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_caption": "<f>Caption set! Ab custom button ka <b>Text</b> bhejo.</f>\n<f>(Example: 'Join Now')</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_get_btn_text": "<f>Button text set! Ab button ka <b>URL (Link)</b> bhejo.</f>\n<f>(Example: 'https://t.me/mychannel')</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_custom_post_confirm": "<b><f>--- PREVIEW ---</f></b>\n\n{caption}\n\n<b><f>Target:</f></b> <code>{chat_id}</code>",
        "admin_custom_post_success": "✅ <b><f>Success!</f></b>\n<f>Post ko</f> '{chat_id}' <f>par bhej diya gaya hai.</f>",
        "admin_custom_post_error": "❌ <b><f>Error!</f></b>\n<f>Post</f> '{chat_id}' <f>par nahi bhej paya.</f>\n<f>Error:</f> {e}",
        
        # === Admin: Bot Appearance Menu (NAYA) ===
        "admin_menu_appearance": "🎨 <b><f>Bot Appearance</f></b> 🎨\n\n<f>Bot ke messages ka look aur feel yahaan change karein.</f>\n\n<f>Current Font:</f> <b>{font}</b>\n<f>Current Style:</f> <b>{style}</b>",
        "admin_appearance_select_font": "<f>Kaunsa font select karna hai?</f>\n\n<f>Current:</f> <b>{font}</b>",
        "admin_appearance_select_style": "<f>Kaunsa style select karna hai?</f>\n\n<f>Current:</f> <b>{style}</b>",
        "admin_appearance_set_font_success": "✅ <b><f>Success!</f></b> <f>Font ko</f> <b>{font}</b> <f>par set kar diya gaya hai.</f>",
        "admin_appearance_set_style_success": "✅ <b><f>Success!</f></b> <f>Style ko</f> <b>{style}</b> <f>par set kar diya gaya hai.</f>",
        
        # === Admin: Merge Series (NAYA v33) ===
        "admin_menu_merge_anime": "🔄 <b><f>Merge Series</f></b> 🔄\n\n<f>Yeh feature do alag-alag Series entries ko ek mein combine kar dega.</f>\n<f>(Jaise 'Naruto S1' + 'Naruto S2' = 'Naruto S1' jisme ab S2 bhi hai)</f>",
        "admin_merge_anime_select_target": "1️⃣ <f>Pehle, <b>TARGET</b> Series select karein.</f>\n\n<f>(Yeh woh anime hai jiske ANDAR aap doosre seasons daalna chahte hain.)</f>\n<f>(Page {page})</f>",
        "admin_merge_anime_select_source": "2️⃣ <f>Ab, <b>SOURCE</b> Series select karein.</f>\n\n<f>(Yeh woh anime hai jisko delete karke iske saare seasons <b>{target_name}</b> mein move kar diye jayenge.)</f>\n<f>(Page {page})</f>",
        "admin_merge_anime_self_merge_error": "❌ <f>Error! Aap ek anime ko khud se merge nahi kar sakte. Koi doosra anime chunein.</f>",
        "admin_merge_anime_confirm": "⚠️ <b><f>FINAL CONFIRMATION</f></b> ⚠️\n\n<f>Aap <b>SOURCE</b> anime:</f>\n<code>{source_name}</code>\n<f>ke saare seasons ko <b>TARGET</b> anime:</f>\n<code>{target_name}</code>\n<f>mein move kar rahe hain.</f>\n\n<f>Total</f> <b>{count}</b> <f>seasons move honge.</f>\n<f>Source anime</f> (<code>{source_name}</code>) <f>delete ho jayega.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_merge_anime_success": "✅ <b><f>Success!</f></b>\n<f>Total</f> <b>{count}</b> <f>seasons ko</f> <code>{source_name}</code> <f>se</f> <code>{target_name}</code> <f>mein move kar diya gaya hai.</f>\n<f>Source anime delete ho gaya hai.</f>",
        "admin_merge_anime_error": "❌ <b><f>Error!</f></b> <f>Merge nahi ho paya. Dono anime check karein. Error:</f> {e}",
        
        # === Admin: User Stats (NAYA v34) ===
        "admin_stats_loading": "⏳ <f>Stats calculate kar raha hoon...</f>",
        "admin_stats_result": "📊 <b><f>User Statistics</f></b> 📊\n\n<f>Total Users:</f> <b>{total_users}</b>\n\n🥇 <b><f>Top 10 Active Users:</f></b>\n{top_users_list}",
        "admin_stats_no_users": "<f>Abhi bot par koi top users nahi hain.</f>",
        
        # === Admin: Broadcast (NAYA v34) ===
        "admin_broadcast_start": "📢 <b><f>Broadcast Message</f></b>\n\n<f>Ab woh message bhejo jo aap sabhi users ko bhejna chahte hain.</f>\n<f>(Text, Photo, Video, kuch bhi...)</f>\n\n/cancel - <f>Cancel.</f>",
        "admin_broadcast_confirm": "⚠️ <b><f>Confirm Karo</f></b> ⚠️\n\n<f>Aap yeh message sabhi</f> <b>{user_count}</b> <f>users ko bhej rahe hain.</f>\n\n<b><f>Are you sure?</f></b>",
        "admin_broadcast_sending": "⏳ <f>Broadcast shuru kar raha hoon... Total</f> <b>{user_count}</b> <f>users.</f>\n\n<f>Isme time lag sakta hai. Bot ko band na karein.</f>",
        "admin_broadcast_success": "✅ <b><f>Broadcast Complete!</f></b>\n\n<f>Sent to:</f> <b>{sent_count}</b> <f>users</f>\n<f>Failed for:</f> <b>{failed_count}</b> <f>users</f>",
        "admin_broadcast_error": "❌ <b><f>Broadcast Error!</f></b>\n<f>Error:</f> {e}",
    }
# --- Config Helper (MAJOR REFACTOR) ---
async def get_config():
    """Database se bot config fetch karega"""
    config = config_collection.find_one({"_id": "bot_config"})
    
    default_messages = await get_default_messages()

    if not config:
        default_config = {
            "_id": "bot_config", "donate_qr_id": None, 
            "links": {"backup": None, "download": None, "help": None}, # NAYA: Help link
            "user_menu_photo_id": None, # NAYA: User Menu Photo
            "delete_seconds": 300, 
            "messages": default_messages,
            "co_admins": [],
            "appearance": {"font": "default", "style": "normal"},
            "default_publish_chat": None
        }
        config_collection.insert_one(default_config)
        return default_config
    
    # --- Compatibility aur Migration ---
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
    if "default_publish_chat" not in config:
        config["default_publish_chat"] = None
        needs_update = True
    
    if "messages" not in config: 
        config["messages"] = {}
        needs_update = True
        
    if "links" not in config: # NAYA: Links check
        config["links"] = {"backup": None, "download": None, "help": None}
        needs_update = True
    elif "help" not in config["links"]: # NAYA: Help link check
        config["links"]["help"] = None
        needs_update = True

    # Check karo ki saare default messages config me hain ya nahi
    for key, value in default_messages.items():
        if key not in config["messages"]:
            config["messages"][key] = value
            needs_update = True
        else:
            # Force update agar purana message abhi bhi "Anime" bol raha hai (Series/Movie ke context mein)
            old_msg = config["messages"].get(key, "")
            if isinstance(old_msg, str) and ("Anime" in old_msg or "anime" in old_msg):
                # Sirf un keys ko update karo jo content type se related hain
                force_keys = [
                    "admin_post_gen_select_anime", "admin_post_gen_no_anime",
                    "admin_gen_link_select_anime", "admin_gen_link_no_anime",
                    "admin_del_anime_select", "admin_del_anime_no_anime", "admin_del_anime_success", "admin_del_anime_error",
                    "admin_del_ep_select_anime", "admin_add_ep_select_anime",
                    "admin_edit_anime_select", "admin_update_photo_select_anime",
                    "admin_add_season_select_anime", "admin_add_season_no_anime",
                    "admin_add_anime_start", "admin_add_anime_get_name", "admin_add_anime_save_exists",
                    "user_dl_anime_not_found", "admin_menu_add_content",
                    # post_gen_*_caption NOT here — admin custom caption kabhi overwrite mat karo
                ]
                if key in force_keys:
                    config["messages"][key] = value
                    needs_update = True
    
    # Purane messages remove karo
    messages_to_remove = [
        "user_sub_qr_error", "user_sub_qr_text", "user_sub_ss_prompt", "user_sub_ss_not_photo",
        "user_sub_ss_error", "sub_pending", "sub_approved", "sub_rejected", "user_sub_removed",
        "user_already_subscribed", "user_dl_unsubscribed_alert", "user_dl_unsubscribed_dm",
        "user_dl_checking_sub", "gen_link_caption_anime", "gen_link_caption_ep", "gen_link_caption_season",
        # NAYA v33: Purana merge feature hatao
        "admin_menu_merge_seasons", "admin_merge_select_anime", "admin_merge_no_anime",
        "admin_merge_no_seasons", "admin_merge_select_seasons", "admin_merge_min_2",
        "admin_merge_get_new_name", "admin_merge_name_exists", "admin_merge_confirm",
        "admin_merge_success", "admin_merge_error"
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
            "user_menu_photo_id": config.get("user_menu_photo_id"), # NAYA
            "delete_seconds": config.get("delete_seconds", 300),
            "co_admins": config.get("co_admins", []),
            "appearance": config.get("appearance", {"font": "default", "style": "normal"}),
            "links": config.get("links", {"backup": None, "download": None, "help": None}) # NAYA
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
# --- NAYA FIX: 2x2 Grid Helper
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

# NAYA (v10): Pagination Helper

def sanitize_telegram_html(text: str) -> str:
    """Fix broken HTML so Telegram accepts it. Keep blockquotes + bold."""
    if not text:
        return text or ""
    import re
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    
    # Fix common broken patterns from templates:
    # <b>LABEL: value  without closing </b> before next tag/newline
    # Close <b> that was opened for a label if </b> missing before : or end of short run
    # More reliable: walk and close open inline tags before block boundaries
    
    INLINE_OPENS = {
        '<b>': '</b>', '<i>': '</i>', '<u>': '</u>', '<s>': '</s>',
        '<code>': '</code>', '<strong>': '</strong>', '<em>': '</em>',
    }
    
    def _close_open_inline(t: str) -> str:
        """Before every </blockquote> and at EOF, close any open inline tags."""
        lower = t.lower()
        stack = []  # list of close tags needed
        out = []
        i = 0
        while i < len(t):
            matched = False
            # check open tags
            for ot, ct in INLINE_OPENS.items():
                if lower.startswith(ot, i):
                    stack.append(ct)
                    out.append(t[i:i+len(ot)])
                    i += len(ot)
                    matched = True
                    break
                if lower.startswith(ct, i):
                    # pop if matches
                    if stack and stack[-1] == ct:
                        stack.pop()
                    out.append(t[i:i+len(ct)])
                    i += len(ct)
                    matched = True
                    break
            if matched:
                continue
            if lower.startswith('</blockquote>', i):
                # close all open inline before blockquote ends
                while stack:
                    out.append(stack.pop())
                out.append(t[i:i+13])
                i += 13
                continue
            if lower.startswith('<blockquote', i):
                # close open inline before new block starts
                while stack:
                    out.append(stack.pop())
                # copy until >
                j = t.find('>', i)
                if j < 0:
                    out.append(t[i])
                    i += 1
                else:
                    out.append(t[i:j+1])
                    i = j + 1
                continue
            out.append(t[i])
            i += 1
        while stack:
            out.append(stack.pop())
        return ''.join(out)
    
    text = _close_open_inline(text)
    
    def _balance(t, open_pat, close_tag):
        opens = len(re.findall(open_pat, t, flags=re.I))
        closes = len(re.findall(re.escape(close_tag), t, flags=re.I))
        if opens > closes:
            t = t + (close_tag * (opens - closes))
        elif closes > opens:
            extra = closes - opens
            for _ in range(extra):
                idx = t.lower().rfind(close_tag.lower())
                if idx >= 0:
                    t = t[:idx] + t[idx+len(close_tag):]
        return t
    
    text = _balance(text, r"<b>", "</b>")
    text = _balance(text, r"<i>", "</i>")
    text = _balance(text, r"<code>", "</code>")
    text = _balance(text, r"<u>", "</u>")
    text = _balance(text, r"<s>", "</s>")
    text = _balance(text, r"<pre>", "</pre>")
    text = _balance(text, r"<blockquote[^>]*>", "</blockquote>")
    return text


async def build_paginated_keyboard(
    collection, 
    page: int, 
    page_callback_prefix: str, 
    item_callback_prefix: str,
    back_callback: str,
    filter_query: dict = None,
    exclude_items: list = None # NAYA v33
):
    if filter_query is None:
        filter_query = {}
    
    # NAYA v33: Exclude items from query
    if exclude_items:
        filter_query["name"] = {"$nin": exclude_items}
        
    skip = page * ITEMS_PER_PAGE
    total_items = collection.count_documents(filter_query)
    
    # Sort by last_modified if present, else name
    try:
        items = list(collection.find(filter_query).sort("last_modified", DESCENDING).skip(skip).limit(ITEMS_PER_PAGE))
    except Exception:
        items = list(collection.find(filter_query).skip(skip).limit(ITEMS_PER_PAGE))
    
    if not items and page == 0:
        return None, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]])

    buttons = []
    for item in items:
        if "name" in item:
            nm = str(item['name'])
            # 3 columns rakho, text pad karke button width badhao (misclick kam)
            label = f"   🎬 {nm}   "
            if len(label) > 64:
                label = label[:61] + "..."
            buttons.append(InlineKeyboardButton(label, callback_data=f"{item_callback_prefix}{item['name']}"))
        elif "first_name" in item:
            user_id = item['_id']
            first_name = item.get('first_name', f"ID: {user_id}")
            buttons.append(InlineKeyboardButton(first_name, callback_data=f"{item_callback_prefix}{user_id}"))

    keyboard = build_grid_keyboard(buttons, items_per_row=3)  # 3 columns, wider via padded text
    
    page_buttons = []
    if page > 0:
        page_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{page_callback_prefix}{page - 1}"))
    if (page + 1) * ITEMS_PER_PAGE < total_items:
        page_buttons.append(InlineKeyboardButton(f"Next ➡️ ({page+2})", callback_data=f"{page_callback_prefix}{page + 1}"))
    # Page indicator
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        
    if page_buttons:
        keyboard.append(page_buttons)
    if total_items > 0:
        total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        keyboard.append([InlineKeyboardButton(f"📄 {page+1}/{total_pages} ({total_items} items)", callback_data="noop")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_callback)])
    
    return items, InlineKeyboardMarkup(keyboard)
# --- Job Queue Callbacks ---
async def send_donate_thank_you(context: ContextTypes.DEFAULT_TYPE):
    """1 min baad thank you message bhejega"""
    job = context.job
    try:
        msg = await format_message(context, "donate_thanks")
        await context.bot.send_message(chat_id=job.chat_id, text=msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.warning(f"Thank you message bhejte waqt error: {e}")

# FIX: Naya Auto-Delete Function (asyncio)

async def admin_reply_temp(update: Update, text: str, seconds: int = 60, **kwargs):
    """Admin DM message - auto delete after 1 min, no timer shown"""
    try:
        if update.message:
            msg = await update.message.reply_text(text, **kwargs)
        elif update.callback_query:
            msg = await update.callback_query.message.reply_text(text, **kwargs)
        else:
            return None
        try:
            asyncio.create_task(delete_message_later(
                bot=update.get_bot() if hasattr(update, 'get_bot') else msg.get_bot(),
                chat_id=msg.chat_id,
                message_id=msg.message_id,
                seconds=seconds
            ))
        except Exception:
            pass
        return msg
    except Exception as e:
        logger.error(f"admin_reply_temp: {e}")
        return None

async def schedule_admin_msg_delete(bot, chat_id, message_id, seconds=60):
    try:
        track_dm_msg(chat_id, message_id)
        # Single msg delete as backup; bulk clear also scheduled at end of post flow
        asyncio.create_task(delete_message_later(bot, chat_id, message_id, seconds))
    except Exception:
        pass

async def delete_message_later(bot, chat_id: int, message_id: int, seconds: int):
    """asyncio.sleep ka use karke message delete karega"""
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Auto-deleted message {message_id} for user {chat_id} (asyncio.sleep)")
    except Exception as e:
        logger.warning(f"Message (asyncio.sleep) delete karne me error: {e}")

def track_dm_msg(user_id: int, message_id: int):
    """Session messages track — baad me bulk clean ke liye"""
    try:
        if not message_id:
            return
        db['user_session_msgs'].update_one(
            {"user_id": user_id},
            {"$addToSet": {"msg_ids": message_id}, "$set": {"updated_at": __import__("datetime").datetime.utcnow()}},
            upsert=True
        )
    except Exception as e:
        logger.debug(f"track_dm_msg: {e}")

async def clear_user_dm(bot, user_id: int, extra_ids=None):
    """User ke DM se bot ke tracked messages delete — chat clean lage"""
    try:
        doc = db['user_session_msgs'].find_one({"user_id": user_id}) or {}
        ids = list(doc.get("msg_ids") or [])
        if extra_ids:
            for mid in extra_ids:
                if mid and mid not in ids:
                    ids.append(mid)
        deleted = 0
        for mid in ids:
            try:
                await bot.delete_message(chat_id=user_id, message_id=mid)
                deleted += 1
            except Exception:
                pass
        db['user_session_msgs'].delete_one({"user_id": user_id})
        logger.info(f"clear_user_dm: user={user_id} deleted={deleted}/{len(ids)}")
    except Exception as e:
        logger.warning(f"clear_user_dm failed: {e}")

async def schedule_clear_user_dm(bot, user_id: int, seconds: int, extra_ids=None):
    """Promo/timer ke baad pura DM clean"""
    async def _job():
        try:
            await asyncio.sleep(max(1, int(seconds)))
            await clear_user_dm(bot, user_id, extra_ids=extra_ids)
        except Exception as e:
            logger.warning(f"schedule_clear_user_dm: {e}")
    try:
        asyncio.create_task(_job())
    except Exception as e:
        logger.warning(f"schedule_clear_user_dm create: {e}")

# NAYA: Anime ka timestamp update karne ke liye helper
async def _update_anime_timestamp(anime_name: str):
    """
    Jab bhi koi anime/season/ep add/edit/delete hoga,
    toh iska 'last_modified' timestamp update karega.
    """
    try:
        animes_collection.update_one(
            {"name": anime_name},
            {"$set": {"last_modified": datetime.now()}}
        )
        logger.info(f"'{anime_name}' ka timestamp update ho gaya.")
    except Exception as e:
        logger.error(f"'{anime_name}' ka timestamp update karne me error: {e}")
# --- Conversation States (v34) ---
(A_GET_NAME, A_GET_POSTER, A_GET_DESC, A_CONFIRM) = range(4) 
(S_GET_ANIME, S_GET_NUMBER, S_GET_POSTER, S_GET_DESC, S_CONFIRM, S_ASK_MORE) = range(4, 10) 
(E_GET_ANIME, E_GET_SEASON, E_GET_NUMBER, E_GET_480P, E_GET_720P, E_GET_1080P, E_GET_4K, E_ASK_MORE) = range(10, 18) 
(CD_GET_QR,) = range(18, 19) 
(CL_GET_LINK,) = range(20, 21) 
(PG_MENU, PG_GET_ANIME, PG_GET_SEASON, PG_GET_EPISODE, PG_GET_SHORT_LINK, PG_GET_CHAT) = range(23, 29) 
(DA_GET_ANIME, DA_CONFIRM) = range(29, 31) 
(DS_GET_ANIME, DS_GET_SEASON, DS_CONFIRM) = range(31, 34) 
(DE_GET_ANIME, DE_GET_SEASON, DE_GET_EPISODE, DE_CONFIRM) = range(34, 38) 
(M_GET_DONATE_THANKS, M_GET_FILE_WARNING) = range(40, 42) 
(CS_GET_DELETE_TIME, CS_GET_PROMO_DELETE, CS_GET_PREVIEW_DELETE) = range(45, 48) 
(UP_GET_ANIME, UP_GET_TARGET, UP_GET_POSTER) = range(48, 51) 
(CA_GET_ID, CA_CONFIRM) = range(51, 53) 
(CR_GET_ID, CR_CONFIRM) = range(53, 55) 
(CPOST_GET_CHAT, CPOST_GET_POSTER, CPOST_GET_CAPTION, CPOST_GET_BTN_TEXT, CPOST_GET_BTN_URL, CPOST_CONFIRM) = range(55, 61) 
(EA_GET_ANIME, EA_GET_NEW_NAME, EA_CONFIRM) = range(61, 64) 
(ES_GET_ANIME, ES_GET_SEASON, ES_GET_NEW_NAME, ES_CONFIRM) = range(64, 68) 
(EE_GET_ANIME, EE_GET_SEASON, EE_GET_EPISODE, EE_GET_NEW_NUM, EE_CONFIRM) = range(68, 73) 
(M_MENU_MAIN, M_MENU_DL, M_MENU_GEN, M_MENU_POSTGEN, M_GET_MSG, M_MENU_ADMIN) = range(73, 79) 
(GL_MENU, GL_GET_ANIME, GL_GET_SEASON, GL_GET_EPISODE) = range(79, 83) 
(AP_MENU, AP_SET_FONT, AP_SET_STYLE) = range(83, 86) 
(CS_GET_MENU_PHOTO,) = range(86, 87) 
(MA_GET_TARGET_ANIME, MA_GET_SOURCE_ANIME, MA_CONFIRM) = range(87, 90)
# NAYA v34: Broadcast States
(BC_GET_MESSAGE, BC_CONFIRM) = range(90, 92)

# NAYA: Movie Add States
(M_GET_NAME, M_GET_POSTER, M_GET_DESC, M_GET_480P, M_GET_720P, M_GET_1080P, M_GET_4K, M_CONFIRM) = range(92, 100)

# NAYA: Post Preview / Edit States
(PG_PREVIEW, PG_EDIT_MENU, PG_EDIT_TITLE, PG_EDIT_DESC, PG_EDIT_FOOTER) = range(100, 105)

# NAYA: Default Publish Chat
(DPC_GET_CHAT,) = range(104, 105)
(PROMO_GET_VALUE,) = range(105, 106)
(VERIFY_VIDEO,) = range(106, 107)
(PBTN_GET_TEXT,) = range(107, 108)
(REQ_GET_TEXT,) = range(108, 109)
(CHATS_REPLY, CHATS_BAN_ID) = range(109, 111)


# --- NAYA: Global Cancel Function ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the current conversation."""
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

# NAYA: 'Add Episode' flow ke liye special back/cancel
async def cancel_add_episode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add Episode flow ko cancel karke Add Content menu par bhejega."""
    if context.user_data:
        context.user_data.clear()
    
    await cancel(update, context) # Pehle normal cancel message dikhao
    await asyncio.sleep(0.1)
    
    if update.callback_query:
        await add_content_menu(update, context) # Phir Add Content menu dikhao
    
    return ConversationHandler.END

# NAYA: 'Add Season' flow ke liye special back/cancel
async def cancel_add_season(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Add Season flow ko cancel karke Add Content menu par bhejega."""
    if context.user_data:
        context.user_data.clear()
    
    await cancel(update, context) # Pehle normal cancel message dikhao
    await asyncio.sleep(0.1)
    
    if update.callback_query:
        await add_content_menu(update, context) # Phir Add Content menu dikhao
    
    return ConversationHandler.END

# --- Common Conversation Fallbacks ---
async def back_to_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

async def back_to_add_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if context.user_data:
        context.user_data.clear() # NAYA: State clear karo
    await add_content_menu(update, context)
    return ConversationHandler.END

async def back_to_manage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await manage_content_menu(update, context)
    return ConversationHandler.END

async def back_to_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await edit_content_menu(update, context)
    return ConversationHandler.END

async def back_to_sub_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_command(update, context, from_callback=True) 
    return ConversationHandler.END

async def back_to_donate_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await donate_settings_menu(update, context)
    return ConversationHandler.END

async def back_to_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await other_links_menu(update, context)
    return ConversationHandler.END

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_user_menu(update, context, from_callback=True) 
    return ConversationHandler.END
    
async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} ne /user dabaya.")
    # NAYA v34: User interaction track karo
    await increment_user_interaction(update.effective_user.id)
    await show_user_menu(update, context)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} ne /menu dabaya (Admin Panel).")
    await admin_command(update, context)
    
async def back_to_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await bot_messages_menu(update, context)
    return ConversationHandler.END

async def back_to_admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_settings_menu(update, context)
    return ConversationHandler.END

# NAYA: Appearance Menu Fallback
async def back_to_appearance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await appearance_menu_start(update, context)
    return AP_MENU

# NAYA: Update Photo Menu Fallback
async def back_to_update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await update_photo_menu(update, context)
    return ConversationHandler.END

# --- Admin Conversations (Add, Delete, etc.) ---
# --- Conversation: Add Anime ---
async def add_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_add_anime_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML) 
    return A_GET_NAME

async def get_anime_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_name'] = update.message.text
    text = await format_message(context, "admin_add_anime_get_name")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return A_GET_POSTER

async def get_anime_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_add_anime_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return A_GET_POSTER 
    context.user_data['anime_poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_anime_get_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return A_GET_DESC

async def get_anime_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_desc'] = update.message.text
    return await confirm_anime_details(update, context)

async def skip_anime_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['anime_desc'] = None 
    return await confirm_anime_details(update, context)

async def confirm_anime_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['anime_name']
    poster_id = context.user_data['anime_poster_id']
    desc = context.user_data['anime_desc']
    
    caption = await format_message(context, "admin_add_anime_confirm", {
        "name": name, 
        "description": desc if desc else ''
    })
    keyboard = [[InlineKeyboardButton("✅ Save", callback_data="save_anime")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    
    if update.message:
        try:
            await update.message.reply_photo(photo=poster_id, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Confirm anime details me error: {e}")
            text = await format_message(context, "admin_add_anime_confirm_error")
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return A_GET_DESC 
    return A_CONFIRM

async def save_anime_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    try:
        name = context.user_data['anime_name']
        if animes_collection.find_one({"name": name}):
            caption = await format_message(context, "admin_add_anime_save_exists", {"name": name})
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
            await asyncio.sleep(3)
            await add_content_menu(update, context)
            return ConversationHandler.END
        
        anime_document = {
            "name": name, 
            "type": "series",  # Series (old anime flow)
            "poster_id": context.user_data['anime_poster_id'], 
            "description": context.user_data['anime_desc'], 
            "seasons": {},
            "created_at": datetime.now(),
            "last_modified": datetime.now()
        }
        animes_collection.insert_one(anime_document)
        caption = await format_message(context, "admin_add_anime_save_success", {"name": name})
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
        await asyncio.sleep(3)
        await add_content_menu(update, context)
    except Exception as e:
        logger.error(f"Anime save karne me error: {e}")
        caption = await format_message(context, "admin_add_anime_save_error")
        await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML)
    context.user_data.clear() 
    return ConversationHandler.END

# ============================================
# ===       ADD MOVIE (Simple Flow)        ===
# ============================================
async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🎬 <b>Add Movie</b>\n\nMovie ka <b>Name</b> bhejo:"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return M_GET_NAME

async def get_movie_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['movie_name'] = update.message.text
    context.user_data['movie_qualities'] = {}
    text = "✅ Name saved.\n\nAb movie ka <b>Poster</b> (photo) bhejo:"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_POSTER

async def get_movie_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please ek photo (poster) bhejo.", parse_mode=ParseMode.HTML)
        return M_GET_POSTER
    context.user_data['movie_poster_id'] = update.message.photo[-1].file_id
    text = "✅ Poster saved.\n\nAb <b>Description / Synopsis</b> bhejo:\n(/skip to skip)"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_DESC

async def get_movie_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['movie_desc'] = update.message.text
    text = "✅ Description saved.\n\nAb <b>480p</b> video bhejo (ya /skip):"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_480P

async def skip_movie_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['movie_desc'] = None
    text = "Description skip.\n\nAb <b>480p</b> video bhejo (ya /skip):"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_480P

async def _save_movie_quality(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('video'):
        file_id = update.message.document.file_id
    if not file_id:
        if update.message.text and update.message.text.startswith('/'):
            return False
        await update.message.reply_text(f"❌ {quality} ke liye video file bhejo.", parse_mode=ParseMode.HTML)
        return False
    context.user_data['movie_qualities'][quality] = file_id
    await update.message.reply_text(f"✅ {quality} saved!", parse_mode=ParseMode.HTML)
    return True

async def get_movie_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_quality(update, context, "480p"):
        return M_GET_480P
    await update.message.reply_text("Ab <b>720p</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_720P

async def skip_movie_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("480p skip.\nAb <b>720p</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_720P

async def get_movie_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_quality(update, context, "720p"):
        return M_GET_720P
    await update.message.reply_text("Ab <b>1080p</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def skip_movie_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("720p skip.\nAb <b>1080p</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def get_movie_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_movie_quality(update, context, "1080p"):
        return M_GET_1080P
    await update.message.reply_text("Ab <b>4K</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_4K

async def skip_movie_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1080p skip.\nAb <b>4K</b> video bhejo (ya /skip):", parse_mode=ParseMode.HTML)
    return M_GET_4K

async def get_movie_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _save_movie_quality(update, context, "4K")
    return await confirm_movie_details(update, context)

async def skip_movie_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await confirm_movie_details(update, context)

async def confirm_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['movie_name']
    desc = context.user_data.get('movie_desc') or "No description"
    quals = list(context.user_data.get('movie_qualities', {}).keys())
    caption = f"🎬 <b>Confirm Movie</b>\n\n<b>Name:</b> {name}\n<b>Desc:</b> {desc}\n<b>Qualities:</b> {', '.join(quals) if quals else 'None'}\n\nSave karein?"
    keyboard = [
        [InlineKeyboardButton("✅ Save Movie", callback_data="save_movie")],
        [InlineKeyboardButton("⬅️ Cancel", callback_data="back_to_add_content")]
    ]
    poster = context.user_data.get('movie_poster_id')
    if poster and update.message:
        try:
            await update.message.reply_photo(photo=poster, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_CONFIRM

async def save_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        name = context.user_data['movie_name']
        if animes_collection.find_one({"name": name}):
            await query.edit_message_caption(caption=f"❌ '{name}' already exists!", parse_mode=ParseMode.HTML)
            await asyncio.sleep(2)
            await add_content_menu(update, context)
            return ConversationHandler.END

        movie_doc = {
            "name": name,
            "type": "movie",
            "poster_id": context.user_data['movie_poster_id'],
            "description": context.user_data.get('movie_desc'),
            "qualities": context.user_data.get('movie_qualities', {}),
            "seasons": {},  # empty for compatibility
            "created_at": datetime.now(),
            "last_modified": datetime.now()
        }
        animes_collection.insert_one(movie_doc)
        await query.edit_message_caption(caption=f"✅ Movie <b>{name}</b> successfully added!", parse_mode=ParseMode.HTML)
        await asyncio.sleep(2)
        await add_content_menu(update, context)
    except Exception as e:
        logger.error(f"Movie save error: {e}")
        await query.edit_message_caption(caption="❌ Error saving movie.", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END

# --- Conversation: Add Season ---
async def add_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await add_season_show_anime_list(update, context, page=0)

async def add_season_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("addseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 
    
    # Sirf Series (movies mein season nahi hota)
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="addseason_page_",
        item_callback_prefix="season_anime_",
        back_callback="back_to_add_content",
        filter_query={"$or": [{"type": "series"}, {"type": {"$exists": False}}]}
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_add_season_no_anime")
    else:
        text = await format_message(context, "admin_add_season_select_anime", {"page": page + 1})
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return S_GET_ANIME

async def get_anime_for_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("season_anime_", "")
    context.user_data['anime_name'] = anime_name
    
    # --- NAYA LOGIC (Last Season Check) START ---
    anime_doc = animes_collection.find_one({"name": anime_name})
    if not anime_doc:
        text = await format_message(context, "admin_add_season_get_number_error", {"anime_name": anime_name})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    seasons = anime_doc.get("seasons", {})
    season_keys = list(seasons.keys()) # Yahan _ keys filter karne ki zaroorat nahi
    
    if not season_keys:
        text = await format_message(context, "admin_add_season_get_anime_no_last", {
            "anime_name": anime_name
        })
    else:
        try:
            # Seasons ko numerically sort karo
            sorted_seasons = sorted(season_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_season_name = sorted_seasons[-1]
            text = await format_message(context, "admin_add_season_get_anime_with_last", {
                "anime_name": anime_name,
                "last_season_name": last_season_name
            })
        except Exception as e:
            logger.warning(f"Last season find karne me error: {e}")
            # Error hone par fallback
            text = await format_message(context, "admin_add_season_get_anime_no_last", {
                "anime_name": anime_name
            })
    # --- NAYA LOGIC END ---

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return S_GET_NUMBER

async def get_season_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    season_name = update.message.text
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    if not anime_doc:
            text = await format_message(context, "admin_add_season_get_number_error", {"anime_name": anime_name})
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
            
    if season_name in anime_doc.get("seasons", {}):
        text = await format_message(context, "admin_add_season_get_number_exists", {
            "anime_name": anime_name, 
            "season_name": season_name
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return S_GET_NUMBER

    text = await format_message(context, "admin_add_season_get_poster_prompt", {"season_name": season_name})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_POSTER

async def get_season_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_add_season_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return S_GET_POSTER
    context.user_data['season_poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_season_get_desc_prompt")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def skip_season_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_poster_id'] = None
    text = await format_message(context, "admin_add_season_skip_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def get_season_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_desc'] = update.message.text
    return await confirm_season_details(update, context)

async def skip_season_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['season_desc'] = None
    return await confirm_season_details(update, context)

async def confirm_season_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    season_poster_id = context.user_data.get('season_poster_id')
    season_desc = context.user_data.get('season_desc') 
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    poster_id_to_show = season_poster_id or anime_doc.get('poster_id')
    
    caption = await format_message(context, "admin_add_season_confirm", {
        "anime_name": anime_name,
        "season_name": season_name,
        "season_desc": season_desc or 'N/A'
    })
    keyboard = [[InlineKeyboardButton("✅ Haan, Save Karo", callback_data="save_season")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    
    await update.message.reply_photo(
        photo=poster_id_to_show,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode=ParseMode.HTML
    )
    return S_CONFIRM

async def save_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # "Save" button press ko acknowledge karo
    
    try:
        anime_name = context.user_data['anime_name']
        season_name = context.user_data['season_name']
        season_poster_id = context.user_data.get('season_poster_id')
        season_desc = context.user_data.get('season_desc') 
        
        season_data = {} 
        if season_poster_id:
            season_data["_poster_id"] = season_poster_id 
        if season_desc:
            season_data["_description"] = season_desc 
        
        # 1. Database update
        animes_collection.update_one(
            {"name": anime_name}, 
            {"$set": {
                f"seasons.{season_name}": season_data,
                "last_modified": datetime.now()
            }} 
        )
        
        # 2. "Yes/No" message format karo
        text = await format_message(context, "admin_add_season_ask_more", {
            "anime_name": anime_name,
            "season_name": season_name
        })
        keyboard = [
            [InlineKeyboardButton("✅ Yes (Add More)", callback_data="add_season_more_yes")],
            [InlineKeyboardButton("🚫 No (Back to Menu)", callback_data="add_season_more_no")]
        ]

        # 3. === NAYA FIX: Purana photo message delete karo ===
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Purana photo message delete nahi kar paya: {e}")
            # Agar delete fail ho, toh purana (buggy) tareeka try karo
            await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            try:
                await query.message.delete_reply_markup() 
                await query.edit_message_media(None)
            except: pass
            return S_ASK_MORE

        # 4. === NAYA FIX: Naya text message bhejo ===
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
        
        # 5. Agle state par jao
        return S_ASK_MORE 

    except Exception as e:
        logger.error(f"Season save karne me error: {e}")
        caption = await format_message(context, "admin_add_season_save_error")
        
        # Error aane par, purane photo message par hi error dikhao
        try:
            await query.edit_message_caption(caption=caption, parse_mode=ParseMode.HTML, reply_markup=None)
        except Exception as e2:
            logger.error(f"Error message bhi nahi dikha paya: {e2}")
            # Fallback
            await context.bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode=ParseMode.HTML)

        # Conversation ko end karo
        context.user_data.clear()
        await asyncio.sleep(3) 
        await add_content_menu(update, context) 
        return ConversationHandler.END

# NAYA: "Add More Seasons" flow
async def add_more_seasons_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User ne 'Yes (Add More)' dabaya. Agle season ka number maango.
    """
    query = update.callback_query
    await query.answer()
    
    last_season_name = context.user_data['season_name']
    anime_name = context.user_data['anime_name']
    
    text = await format_message(context, "admin_add_season_next_prompt", {
        "season_name": last_season_name,
        "anime_name": anime_name,
    })

    # Sirf 'season_name' aur related data ko context se clear karo
    context.user_data.pop('season_name', None)
    context.user_data.pop('season_poster_id', None)
    context.user_data.pop('season_desc', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return S_GET_NUMBER # Wapas season number maangne wale state par bhej do

async def add_more_seasons_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User ne 'No (Back to Menu)' dabaya. Conversation end karo.
    """
    query = update.callback_query
    await query.answer()
    
    # Poora context clear karo
    context.user_data.clear()
    
    # Wapas 'Add Content' menu par bhej do
    await add_content_menu(update, context)
    return ConversationHandler.END

# --- Conversation: Add Episode (Multi-Quality) ---
async def add_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await add_episode_show_anime_list(update, context, page=0)

async def add_episode_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("addep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 
        
    # Sirf Series
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="addep_page_",
        item_callback_prefix="ep_anime_",
        back_callback="back_to_add_content",
        filter_query={"$or": [{"type": "series"}, {"type": {"$exists": False}}]}
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_add_ep_no_anime")
    else:
        text = await format_message(context, "admin_add_ep_select_anime", {"page": page + 1}) # NAYA: Text DB se aayega

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return E_GET_ANIME

async def get_anime_for_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("ep_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    
    if not seasons:
        text = await format_message(context, "admin_add_ep_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1) 
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"addep_page_{current_page}")])
    
    text = await format_message(context, "admin_add_ep_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return E_GET_SEASON
async def get_season_for_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("ep_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']

    # NEW CODE
    # NAYA: Last episode number check karo
    anime_doc = animes_collection.find_one({"name": anime_name})
    episodes = anime_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_add_ep_get_season_no_last", {"season_name": season_name})
    else:
        # Last episode (numerically) find karo
        try:
            sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
            last_ep_num = sorted_eps[-1]
            text = await format_message(context, "admin_add_ep_get_season_with_last", {
                "season_name": season_name,
                "last_ep_num": last_ep_num
            })
        except Exception as e:
            logger.warning(f"Last episode find karne me error (shayad non-numeric): {e}")
            text = await format_message(context, "admin_add_ep_get_season_no_last", {"season_name": season_name})

    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return E_GET_NUMBER

async def _save_episode_file_helper(update: Update, context: ContextTypes.DEFAULT_TYPE, quality: str):
    file_id = None
    if update.message.video: file_id = update.message.video.file_id
    elif update.message.document and (update.message.document.mime_type and update.message.document.mime_type.startswith('video')): file_id = update.message.document.file_id
    
    if not file_id:
        if update.message.text and update.message.text.startswith('/'):
            return False 
        text = await format_message(context, "admin_add_ep_helper_invalid")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False 

    try:
        anime_name = context.user_data['anime_name']
        season_name = context.user_data['season_name']
        ep_num = context.user_data['ep_num']
        
        dot_notation_key = f"seasons.{season_name}.{ep_num}.{quality}"
        
        # NAYA: File save karne ke saath timestamp update karo
        animes_collection.update_one(
            {"name": anime_name},
            {"$set": {
                dot_notation_key: file_id,
                "last_modified": datetime.now()
            }}
        )
        logger.info(f"Naya episode save ho gaya: {anime_name} S{season_name} E{ep_num} {quality}")
        
        text = await format_message(context, "admin_add_ep_helper_success", {"quality": quality})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        logger.error(f"Episode file save karne me error: {e}")
        text = await format_message(context, "admin_add_ep_helper_error", {"quality": quality})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False

async def get_episode_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ep_num'] = update.message.text
    
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    ep_num = context.user_data['ep_num']
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    existing_eps = anime_doc.get("seasons", {}).get(season_name, {})
    if ep_num in existing_eps:
        text = await format_message(context, "admin_add_ep_get_number_exists", {
            "anime_name": anime_name,
            "season_name": season_name,
            "ep_num": ep_num
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return E_GET_NUMBER

    text = await format_message(context, "admin_add_ep_get_number", {"ep_num": ep_num})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_480P

async def get_480p_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_episode_file_helper(update, context, "480p"):
        return E_GET_480P 
    text = await format_message(context, "admin_add_ep_get_480p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_720P

async def skip_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_480p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_720P

async def get_720p_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_episode_file_helper(update, context, "720p"):
        return E_GET_720P 
    text = await format_message(context, "admin_add_ep_get_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_1080P

async def skip_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_1080P

async def get_1080p_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_episode_file_helper(update, context, "1080p"):
        return E_GET_1080P 
    text = await format_message(context, "admin_add_ep_get_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_4K

async def skip_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return E_GET_4K

async def get_4k_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _save_episode_file_helper(update, context, "4K"):
        text = await format_message(context, "admin_add_ep_get_4k_success")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        return E_GET_4K 
    
    return await ask_add_more_episodes(update, context) # NAYA

async def skip_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_ep_skip_4k")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    return await ask_add_more_episodes(update, context) # NAYA

# NAYA: "Add More Episodes" flow
async def ask_add_more_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ek episode save hone ke baad poochhega ki aur add karna hai ya nahi.
    """
    ep_num = context.user_data['ep_num']
    season_name = context.user_data['season_name']
    
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

async def add_more_episodes_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User ne 'Yes (Add More)' dabaya. Agle episode ka number maango.
    (FIXED IN v32)
    """
    query = update.callback_query
    await query.answer()
    
    last_ep_num = context.user_data['ep_num']
    season_name = context.user_data['season_name']
    
    # NAYA: Agle episode number ka suggestion
    try:
        next_ep_num = str(int(last_ep_num) + 1)
        text = await format_message(context, "admin_add_ep_next_prompt", {
            "ep_num": last_ep_num,
            "season_name": season_name,
            "next_ep_num": next_ep_num
        })
    except ValueError:
        # Agar pichla number 'Movie' ya 'OVA' jaisa tha
        text = await format_message(context, "admin_add_ep_next_prompt_no_suggestion", {
            "ep_num": last_ep_num,
            "season_name": season_name
        })

    # Sirf 'ep_num' ko context se clear karo, taaki naya set ho sake
    context.user_data.pop('ep_num', None)
    
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return E_GET_NUMBER # Wapas episode number maangne wale state par bhej do

async def add_more_episodes_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User ne 'No (Back to Menu)' dabaya. Conversation end karo.
    """
    query = update.callback_query
    await query.answer()
    
    # Poora context clear karo
    context.user_data.clear()
    
    # Wapas 'Add Content' menu par bhej do
    await add_content_menu(update, context)
    return ConversationHandler.END

# --- Conversation: Delete Series/Movie ---
async def delete_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_anime_show_anime_list(update, context, page=0)

async def delete_anime_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delanime_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="delanime_page_",
        item_callback_prefix="del_anime_",
        back_callback="back_to_manage"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_del_anime_no_anime")
    else:
        text = await format_message(context, "admin_del_anime_select", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DA_GET_ANIME

async def delete_anime_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("del_anime_", "")
    context.user_data['anime_name'] = anime_name
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {anime_name} ko Delete Karo", callback_data="del_anime_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    text = await format_message(context, "admin_del_anime_confirm", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DA_CONFIRM

async def delete_anime_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    anime_name = context.user_data['anime_name']
    try:
        animes_collection.delete_one({"name": anime_name})
        logger.info(f"Anime deleted: {anime_name}")
        text = await format_message(context, "admin_del_anime_success", {"anime_name": anime_name})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Anime delete karne me error: {e}")
        text = await format_message(context, "admin_del_anime_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# --- Conversation: Delete Season ---
async def delete_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_season_show_anime_list(update, context, page=0)

async def delete_season_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="delseason_page_",
        item_callback_prefix="del_season_anime_",
        back_callback="back_to_manage"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_del_season_no_anime")
    else:
        text = await format_message(context, "admin_del_season_select_anime", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DS_GET_ANIME

async def delete_season_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("del_season_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_del_season_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"del_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"delseason_page_{current_page}")])

    text = await format_message(context, "admin_del_season_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DS_GET_SEASON

async def delete_season_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("del_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']
    keyboard = [[InlineKeyboardButton(f"✅ Haan, Season {season_name} Delete Karo", callback_data="del_season_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    text = await format_message(context, "admin_del_season_confirm", {
        "anime_name": anime_name,
        "season_name": season_name
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DS_CONFIRM

async def delete_season_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    try:
        animes_collection.update_one(
            {"name": anime_name},
            {"$unset": {f"seasons.{season_name}": ""},
             "$set": {"last_modified": datetime.now()}} # NAYA: Timestamp
        )
        logger.info(f"Season deleted: {anime_name} - S{season_name}")
        text = await format_message(context, "admin_del_season_success", {"season_name": season_name})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Season delete karne me error: {e}")
        text = await format_message(context, "admin_del_season_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END

# --- Conversation: Delete Episode ---
async def delete_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_episode_show_anime_list(update, context, page=0)

async def delete_episode_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("delep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page 
        
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="delep_page_",
        item_callback_prefix="del_ep_anime_",
        back_callback="back_to_manage"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_del_ep_no_anime")
    else:
        text = await format_message(context, "admin_del_ep_select_anime", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DE_GET_ANIME

async def delete_episode_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("del_ep_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_del_ep_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"del_ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"delep_page_{current_page}")])

    text = await format_message(context, "admin_del_ep_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_GET_SEASON

async def delete_episode_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("del_ep_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']
    anime_doc = animes_collection.find_one({"name": anime_name})
    episodes = anime_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_del_ep_no_episode", {
            "anime_name": anime_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"del_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"del_ep_anime_{anime_name}")])

    text = await format_message(context, "admin_del_ep_select_episode", {"season_name": season_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_GET_EPISODE

async def delete_episode_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("del_ep_num_", "")
    context.user_data['ep_num'] = ep_num
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    keyboard = [[InlineKeyboardButton(f"✅ Haan, Ep {ep_num} Delete Karo", callback_data="del_ep_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    text = await format_message(context, "admin_del_ep_confirm", {
        "anime_name": anime_name,
        "season_name": season_name,
        "ep_num": ep_num
    })
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DE_CONFIRM

async def delete_episode_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Deleting...")
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    ep_num = context.user_data['ep_num']
    try:
        animes_collection.update_one(
            {"name": anime_name},
            {"$unset": {f"seasons.{season_name}.{ep_num}": ""},
             "$set": {"last_modified": datetime.now()}} # NAYA: Timestamp
        )
        logger.info(f"Episode deleted: {anime_name} - S{season_name} - E{ep_num}")
        text = await format_message(context, "admin_del_ep_success", {"ep_num": ep_num})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Episode delete karne me error: {e}")
        text = await format_message(context, "admin_del_ep_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(3)
    await manage_content_menu(update, context)
    return ConversationHandler.END
    
# --- Admin Panel: Sub-Menu Functions ---
async def add_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
        [InlineKeyboardButton("📺 Add Series", callback_data="admin_add_anime")],  # Series = existing anime flow
        [InlineKeyboardButton("➕ Add Season", callback_data="admin_add_season")],
        [InlineKeyboardButton("➕ Add Episode", callback_data="admin_add_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_add_content")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    
async def manage_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    user_id = update.effective_user.id
    if await is_co_admin_only(user_id):
        await deny_co_admin_feature(update, context, "Delete Content")
        return
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Series/Movie", callback_data="admin_del_anime")],
        [InlineKeyboardButton("🗑️ Delete Season", callback_data="admin_del_season")],
        [InlineKeyboardButton("🗑️ Delete Episode", callback_data="admin_del_episode")], 
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_manage_content")
    
    if from_message: 
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# NAYA v33: Edit Content Menu updated
async def edit_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_message: bool = False):
    query = update.callback_query
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Series/Movie Name", callback_data="admin_edit_anime")],
        [InlineKeyboardButton("✏️ Edit Season Name", callback_data="admin_edit_season")],
        [InlineKeyboardButton("✏️ Edit Episode Number", callback_data="admin_edit_episode")], 
        [InlineKeyboardButton("🔄 Merge Series", callback_data="admin_merge_anime")], # NAYA
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_edit_content")
    
    if from_message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    elif query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# --- Conversation: Edit Series/Movie Name ---
async def edit_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_anime_show_anime_list(update, context, page=0)

async def edit_anime_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editanime_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="editanime_page_",
        item_callback_prefix="edit_anime_",
        back_callback="back_to_edit_menu"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_edit_anime_no_anime")
    else:
        text = await format_message(context, "admin_edit_anime_select", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EA_GET_ANIME

async def edit_anime_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("edit_anime_", "")
    context.user_data['old_anime_name'] = anime_name
    text = await format_message(context, "admin_edit_anime_get_name", {"anime_name": anime_name})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EA_GET_NEW_NAME

async def edit_anime_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data['old_anime_name']
    
    if animes_collection.find_one({"name": new_name}):
        text = await format_message(context, "admin_edit_anime_save_exists", {"new_name": new_name})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EA_GET_NEW_NAME
    
    context.user_data['new_anime_name'] = new_name
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_name}' ko '{new_name}' Karo", callback_data="edit_anime_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    text = await format_message(context, "admin_edit_anime_confirm", {
        "old_name": old_name,
        "new_name": new_name
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EA_CONFIRM

async def edit_anime_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_name = context.user_data['old_anime_name']
    new_name = context.user_data['new_anime_name']
    try:
        animes_collection.update_one(
            {"name": old_name},
            {"$set": {
                "name": new_name,
                "last_modified": datetime.now() # NAYA: Timestamp
            }}
        )
        logger.info(f"Anime naam update ho gaya: {old_name} -> {new_name}")
        text = await format_message(context, "admin_edit_anime_success", {
            "old_name": old_name,
            "new_name": new_name
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Anime naam update karne me error: {e}")
        text = await format_message(context, "admin_edit_anime_error")
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# --- Conversation: Edit Season Name ---
async def edit_season_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_season_show_anime_list(update, context, page=0)

async def edit_season_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editseason_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page

    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="editseason_page_",
        item_callback_prefix="edit_season_anime_",
        back_callback="back_to_edit_menu"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_edit_season_no_anime")
    else:
        text = await format_message(context, "admin_edit_season_select_anime", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return ES_GET_ANIME

async def edit_season_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("edit_season_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_edit_season_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"edit_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"editseason_page_{current_page}")])

    text = await format_message(context, "admin_edit_season_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return ES_GET_SEASON
async def edit_season_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("edit_season_", "")
    context.user_data['old_season_name'] = season_name
    anime_name = context.user_data['anime_name']
    text = await format_message(context, "admin_edit_season_get_name", {
        "anime_name": anime_name,
        "season_name": season_name
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return ES_GET_NEW_NAME

async def edit_season_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    old_name = context.user_data['old_season_name']
    anime_name = context.user_data['anime_name']
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    if new_name in anime_doc.get("seasons", {}):
        text = await format_message(context, "admin_edit_season_save_exists", {"new_name": new_name})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return ES_GET_NEW_NAME
        
    context.user_data['new_season_name'] = new_name
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_name}' ko '{new_name}' Karo", callback_data="edit_season_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    text = await format_message(context, "admin_edit_season_confirm", {
        "anime_name": anime_name,
        "old_name": old_name,
        "new_name": new_name
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return ES_CONFIRM

async def edit_season_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_name = context.user_data['old_season_name']
    new_name = context.user_data['new_season_name']
    anime_name = context.user_data['anime_name']
    try:
        animes_collection.update_one(
            {"name": anime_name},
            {"$rename": {f"seasons.{old_name}": f"seasons.{new_name}"},
             "$set": {"last_modified": datetime.now()}} # NAYA: Timestamp
        )
        logger.info(f"Season naam update ho gaya: {anime_name} - {old_name} -> {new_name}")
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

# --- Conversation: Edit Episode Number ---
async def edit_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_episode_show_anime_list(update, context, page=0)

async def edit_episode_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("editep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page
        
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="editep_page_",
        item_callback_prefix="edit_ep_anime_",
        back_callback="back_to_edit_menu"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_edit_ep_no_anime")
    else:
        text = await format_message(context, "admin_edit_ep_select_anime", {"page": page + 1}) # NAYA: Text DB se

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EE_GET_ANIME

async def edit_episode_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("edit_ep_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_edit_ep_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"edit_ep_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"editep_page_{current_page}")])

    text = await format_message(context, "admin_edit_ep_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_GET_SEASON

async def edit_episode_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("edit_ep_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']
    anime_doc = animes_collection.find_one({"name": anime_name})
    episodes = anime_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_edit_ep_no_episode", {
            "anime_name": anime_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"edit_ep_num_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"edit_ep_anime_{anime_name}")])

    text = await format_message(context, "admin_edit_ep_select_episode", {"season_name": season_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_GET_EPISODE
    
async def edit_episode_get_new_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("edit_ep_num_", "")
    context.user_data['old_ep_num'] = ep_num
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    
    text = await format_message(context, "admin_edit_ep_get_num", {
        "anime_name": anime_name,
        "season_name": season_name,
        "ep_num": ep_num
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EE_GET_NEW_NUM

async def edit_episode_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_num = update.message.text
    old_num = context.user_data['old_ep_num']
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    if new_num in anime_doc.get("seasons", {}).get(season_name, {}):
        text = await format_message(context, "admin_edit_ep_save_exists", {"new_num": new_num})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EE_GET_NEW_NUM
        
    context.user_data['new_ep_num'] = new_num
    
    keyboard = [[InlineKeyboardButton(f"✅ Haan, '{old_num}' ko '{new_num}' Karo", callback_data="edit_ep_confirm_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    text = await format_message(context, "admin_edit_ep_confirm", {
        "anime_name": anime_name,
        "season_name": season_name,
        "old_num": old_num,
        "new_num": new_num
    })
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EE_CONFIRM

async def edit_episode_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Updating...")
    old_num = context.user_data['old_ep_num']
    new_num = context.user_data['new_ep_num']
    anime_name = context.user_data['anime_name']
    season_name = context.user_data['season_name']
    try:
        animes_collection.update_one(
            {"name": anime_name},
            {"$rename": {f"seasons.{season_name}.{old_num}": f"seasons.{season_name}.{new_num}"},
             "$set": {"last_modified": datetime.now()}} # NAYA: Timestamp
        )
        logger.info(f"Episode number update ho gaya: {anime_name} S{season_name} - {old_num} -> {new_num}")
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

# --- NAYA (v33): Conversation: Merge Series ---
async def merge_anime_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Start by selecting the TARGET anime
    return await merge_anime_select_target(update, context, page=0)

async def merge_anime_select_target(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("merge_target_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 
    
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="merge_target_page_",
        item_callback_prefix="merge_target_anime_",
        back_callback="back_to_edit_menu"
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_edit_anime_no_anime") # Re-use message
    else:
        text = await format_message(context, "admin_merge_anime_select_target", {"page": page + 1})
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return MA_GET_TARGET_ANIME

async def merge_anime_select_source(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("merge_target_anime_"):
        target_name = query.data.replace("merge_target_anime_", "")
        context.user_data['target_anime_name'] = target_name
        context.user_data['current_page'] = 0 # Reset page for source list
        page = 0
        await query.answer()
    elif query.data.startswith("merge_source_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    target_name = context.user_data['target_anime_name']
    
    # Exclude the target anime from the list of sources
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="merge_source_page_",
        item_callback_prefix="merge_source_anime_",
        back_callback="admin_merge_anime", # Back to selecting target
        exclude_items=[target_name] # NAYA: Exclude target
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_edit_anime_no_anime") # Re-use message
    else:
        text = await format_message(context, "admin_merge_anime_select_source", {
            "page": page + 1,
            "target_name": target_name
        })
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return MA_GET_SOURCE_ANIME

async def merge_anime_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    source_name = query.data.replace("merge_source_anime_", "")
    target_name = context.user_data['target_anime_name']
    
    if source_name == target_name:
        text = await format_message(context, "admin_merge_anime_self_merge_error")
        await query.answer(text, show_alert=True)
        return MA_GET_SOURCE_ANIME # Stay on the same step

    context.user_data['source_anime_name'] = source_name
    
    # Count seasons in source
    source_doc = animes_collection.find_one({"name": source_name})
    if not source_doc:
        await query.edit_message_text("Error: Source Series not found.")
        return ConversationHandler.END
        
    source_seasons = source_doc.get("seasons", {})
    season_count = len(source_seasons)
    
    context.user_data['source_seasons_to_merge'] = source_seasons
    
    keyboard = [
        [InlineKeyboardButton("✅ HAAN, MERGE KARO", callback_data="merge_anime_confirm_yes")],
        [InlineKeyboardButton("⬅️ Back to Edit Menu", callback_data="back_to_edit_menu")]
    ]
    
    text = await format_message(context, "admin_merge_anime_confirm", {
        "source_name": source_name,
        "target_name": target_name,
        "count": season_count
    })
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return MA_CONFIRM

async def merge_anime_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Merging...")
    
    try:
        target_name = context.user_data['target_anime_name']
        source_name = context.user_data['source_anime_name']
        source_seasons = context.user_data['source_seasons_to_merge']
        
        if not source_seasons:
            await query.edit_message_text("Source anime mein koi season nahi hai. Kuch merge nahi hua.")
            return ConversationHandler.END
            
        # Create $set query to add all seasons from source to target
        update_query = {}
        for season_name, season_data in source_seasons.items():
            update_query[f"seasons.{season_name}"] = season_data
            
        # Update Target Anime
        animes_collection.update_one(
            {"name": target_name},
            {
                "$set": update_query,
                "$currentDate": {"last_modified": True}
            }
        )
        
        # Delete Source Anime
        animes_collection.delete_one({"name": source_name})
        
        logger.info(f"Anime Merged: '{source_name}' into '{target_name}'")
        text = await format_message(context, "admin_merge_anime_success", {
            "count": len(source_seasons),
            "source_name": source_name,
            "target_name": target_name
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Anime merge karne me error: {e}")
        text = await format_message(context, "admin_merge_anime_error", {"e": e})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(4)
    await edit_content_menu(update, context)
    return ConversationHandler.END

# --- Auto-Delete Settings Menu (all timers) ---

async def set_admin_preview_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = int(config.get("admin_preview_delete_seconds") or 30)
    await query.edit_message_text(
        f"👑 <b>Admin Preview Auto-Delete</b>\n\n"
        f"Abhi: <b>{current} seconds</b>\n\n"
        f"Naya time <b>seconds</b> mein bhejo (min 5).\n"
        f"Example: <code>30</code>\n\n/cancel - Cancel",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_auto_delete")]])
    )
    return CS_GET_PREVIEW_DELETE

async def handle_preview_delete_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        secs = int(update.message.text.strip())
        if secs < 5:
            await update.message.reply_text("Minimum 5 seconds. Dobara bhejo.")
            return CS_GET_PREVIEW_DELETE
        config_collection.update_one({"_id": "bot_config"}, {"$set": {"admin_preview_delete_seconds": secs}}, upsert=True)
        await update.message.reply_text(
            f"✅ Admin Preview delete time set to <b>{secs}s</b>.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Auto-Delete Menu", callback_data="admin_menu_auto_delete")]])
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Sirf number bhejo (seconds).")
        return CS_GET_PREVIEW_DELETE

async def set_promo_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promo (thank you) message auto-delete timer — conversation state"""
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = int(config.get("promo_thank_you_delete_seconds") or 120)
    await query.edit_message_text(
        f"📢 <b>Promo Message Auto-Delete</b>\n\n"
        f"Abhi: <b>{current} seconds</b> ({current // 60}m {current % 60}s)\n\n"
        f"Naya time <b>seconds</b> mein bhejo (min 10).\n"
        f"Example: <code>180</code> = 3 min\n\n/cancel - Cancel",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_auto_delete")]])
    )
    return CS_GET_PROMO_DELETE

async def handle_promo_delete_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save promo delete seconds from conversation"""
    try:
        secs = int(update.message.text.strip())
        if secs < 10:
            await update.message.reply_text("Minimum 10 seconds. Dobara bhejo.")
            return CS_GET_PROMO_DELETE
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$set": {"promo_thank_you_delete_seconds": secs}},
            upsert=True
        )
        m, s = divmod(secs, 60)
        await update.message.reply_text(
            f"✅ <b>Promo delete time set!</b>\n<code>{secs}s</code> ({m}m {s}s)",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Auto-Delete Menu", callback_data="admin_menu_auto_delete")]])
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Sirf number bhejo (seconds). Example: <code>120</code>", parse_mode=ParseMode.HTML)
        return CS_GET_PROMO_DELETE

async def auto_delete_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """All auto-delete timers in one place"""
    query = update.callback_query
    await query.answer()
    config = await get_config()
    file_secs = int(config.get("delete_seconds", 300))
    thank_secs = int(config.get("promo_thank_you_delete_seconds") or 120)
    admin_secs = int(config.get("admin_preview_delete_seconds") or 30)
    
    def _fmt(s):
        m, sec = divmod(int(s), 60)
        return f"{m}m {sec}s" if m else f"{sec}s"
    
    text = (
        "⏱️ <b>Auto-Delete Time Settings</b>\n\n"
        f"📁 <b>File Delete:</b> {_fmt(file_secs)} ({file_secs}s)\n"
        f"📢 <b>Promo Message:</b> {_fmt(thank_secs)} ({thank_secs}s)\n"
        f"👑 <b>Admin Preview Msgs:</b> {_fmt(admin_secs)} ({admin_secs}s)\n\n"
        "Kaunsa timer change karna hai?"
    )
    keyboard = [
        [InlineKeyboardButton(f"📁 File Delete Time ({_fmt(file_secs)})", callback_data="admin_set_delete_time")],
        [InlineKeyboardButton(f"📢 Promo Delete Time ({_fmt(thank_secs)})", callback_data="admin_set_promo_delete")],
        [InlineKeyboardButton(f"👑 Admin Preview Delete ({_fmt(admin_secs)})", callback_data="admin_set_preview_delete")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# --- Conversation: Set Auto-Delete Time ---
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
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_auto_delete")]]))
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

# --- Conversation: Set Donate QR ---
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
# --- Conversation: Set Links ---
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
    elif link_type == "verify_link":
        context.user_data['link_type'] = "verify"
        text = "✅ <b>Verify / How-to-Download Link</b> bhejo:\n(Video link, channel post, ya tutorial URL)\n\n/skip - Clear\n/cancel - Cancel"
        back_button = "back_to_links"
    elif link_type == "request_link":
        context.user_data['link_type'] = "request"
        text = "🎬 <b>Request a Movie Link</b> bhejo:\n(Google form / channel / bot link)\n\n/skip - Clear\n/cancel - Cancel"
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
# --- NAYA: Conversation: Set Custom Messages (PAGINATED) ---
async def set_msg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg_key = query.data.replace("msg_edit_", "")
    
    config = await get_config()
    current_msg = config.get("messages", {}).get(msg_key, "N/A")
    
    context.user_data['msg_key'] = msg_key
    
    # current_msg ko HTML se escape karo taaki <code> me sahi dikhe
    safe_current_msg = current_msg.replace('<', '&lt;').replace('>', '&gt;')
    
    text = await format_message(context, "admin_set_msg_start", {
        "msg_key": msg_key,
        "current_msg": safe_current_msg
    })
    
    if msg_key.startswith("user_dl_") or msg_key == "file_warning":
        back_cb = "msg_menu_dl"
    elif msg_key.startswith("post_gen_"):
        back_cb = "msg_menu_postgen"
    elif msg_key.startswith("admin_"): # NAYA
        back_cb = "msg_menu_admin"
    else:
        back_cb = "msg_menu_gen"
        
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_cb)]]))
    return M_GET_MSG

async def set_msg_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg_text = update.message.text or ''
        # Code-block se copy / entities unescape
        msg_text = (msg_text.replace('&lt;', '<').replace('&gt;', '>')
                   .replace('&amp;', '&').replace('&quot;', '"'))
        msg_text = msg_text.replace('\u200b', '').replace('\ufeff', '').strip()
        msg_key = context.user_data['msg_key']
        
        config_collection.update_one({"_id": "bot_config"}, {"$set": {f"messages.{msg_key}": msg_text}}, upsert=True)
        logger.info(f"{msg_key} message update ho gaya: {msg_text}")
        text = await format_message(context, "admin_set_msg_success", {"msg_key": msg_key})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
        # Clear only msg_key, stay in messages flow
        context.user_data.pop('msg_key', None)
        await update.message.reply_text("⬅️ Messages menu:", parse_mode=ParseMode.HTML)
        # Show main messages menu again
        keyboard = [
            [InlineKeyboardButton("📥 Download Flow Messages", callback_data="msg_menu_dl")],
            [InlineKeyboardButton("✍️ Post Generator Messages", callback_data="msg_menu_postgen")],
            [InlineKeyboardButton("👑 Admin Flow Messages", callback_data="msg_menu_admin")],
            [InlineKeyboardButton("⚙️ General Messages", callback_data="msg_menu_gen")],
            [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
        ]
        text = await format_message(context, "admin_menu_messages_main")
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return M_MENU_MAIN
    except Exception as e:
        logger.error(f"Message save karne me error: {e}")
        text = await format_message(context, "admin_set_msg_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return M_MENU_MAIN
    
# --- Conversation: Post Generator ---
async def post_gen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Post", callback_data="post_gen_movie")],
        [InlineKeyboardButton("📺 Complete Series Post", callback_data="post_gen_anime")],
        [InlineKeyboardButton("✍️ Season Post", callback_data="post_gen_season")],
        [InlineKeyboardButton("✍️ Episode Post", callback_data="post_gen_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_post_gen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_MENU

async def post_gen_select_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    post_type = query.data
    context.user_data['post_type'] = post_type
    
    return await post_gen_show_anime_list(update, context, page=0)

async def post_gen_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("postgen_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page 
    
    post_type = context.user_data.get('post_type', '')
    
    # Movies aur Series alag lists
    if post_type == 'post_gen_movie':
        filter_query = {"type": "movie"}
        list_label = "Movie"
    elif post_type in ('post_gen_anime', 'post_gen_season', 'post_gen_episode'):
        # Series only (type series OR no type field for old data)
        filter_query = {"$or": [{"type": "series"}, {"type": {"$exists": False}}]}
        list_label = "Series"
    else:
        filter_query = {}
        list_label = "Series/Movie"
        
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="postgen_page_",
        item_callback_prefix="post_anime_",
        back_callback="admin_post_gen",
        filter_query=filter_query
    )
    
    if not animes and page == 0:
        text = f"❌ Abhi koi <b>{list_label}</b> add nahi hua hai."
    else:
        text = f"Kaunsa <b>{list_label}</b> select karna hai?\n\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return PG_GET_ANIME

async def post_gen_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("post_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    
    if not anime_doc:
        await query.edit_message_text(f"❌ '{anime_name}' nahi mila.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    post_type = context.user_data.get('post_type')
    
    # Movie ya Complete Series Post → seedha caption banao
    if post_type in ('post_gen_anime', 'post_gen_movie'):
        context.user_data['season_name'] = None
        context.user_data['ep_num'] = None 
        return await generate_post_ask_chat(update, context)
        
    seasons = anime_doc.get("seasons", {}) or {}
    # Filter out metadata keys
    season_keys = [s for s in seasons.keys() if not str(s).startswith("_")]
    
    if not season_keys:
        text = await format_message(context, "admin_post_gen_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_post_gen")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_seasons = sorted(season_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', str(x))])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"post_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"postgen_page_{current_page}")])

    text = await format_message(context, "admin_post_gen_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_GET_SEASON

async def post_gen_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("post_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data.get('anime_name')
    
    if not anime_name:
        await query.edit_message_text("❌ Error: Content name missing. Start again.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    
    if context.user_data.get('post_type') == 'post_gen_season':
        context.user_data['ep_num'] = None 
        return await generate_post_ask_chat(update, context)
        
    anime_doc = animes_collection.find_one({"name": anime_name})
    if not anime_doc:
        await query.edit_message_text(f"❌ '{anime_name}' nahi mila.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    episodes = anime_doc.get("seasons", {}).get(season_name, {}) or {}
    episode_keys = [ep for ep in episodes.keys() if not str(ep).startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_post_gen_no_episode", {
            "anime_name": anime_name, 
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_post_gen")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', str(x))])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"post_ep_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"post_anime_{anime_name}")])

    text = await format_message(context, "admin_post_gen_select_episode", {"season_name": season_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_GET_EPISODE

async def post_gen_final_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ep_num = query.data.replace("post_ep_", "")
    context.user_data['ep_num'] = ep_num
    return await generate_post_ask_chat(update, context)

async def generate_post_ask_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        bot_username = (await context.bot.get_me()).username
        
        config = await get_config()
        anime_name = context.user_data.get('anime_name')
        if not anime_name:
            raise ValueError("Content name missing. Please start again.")
            
        season_name = context.user_data.get('season_name')
        ep_num = context.user_data.get('ep_num') 
        anime_doc = animes_collection.find_one({"name": anime_name})
        
        if not anime_doc:
            raise ValueError(f"'{anime_name}' database mein nahi mila.")
        
        anime_id = str(anime_doc['_id'])
        post_type = context.user_data.get('post_type')
        dl_callback_data = f"dl{anime_id}" 
        
        # Safe format: saare possible keys pass karo (DB custom template me series_name ho to bhi error na aaye)
        def _safe_caption_format(template, **kwargs):
            kwargs.setdefault('anime_name', kwargs.get('series_name') or kwargs.get('movie_name') or kwargs.get('name') or '')
            kwargs.setdefault('series_name', kwargs.get('anime_name', ''))
            kwargs.setdefault('movie_name', kwargs.get('anime_name', ''))
            kwargs.setdefault('name', kwargs.get('anime_name', ''))
            kwargs.setdefault('description', kwargs.get('description', '') or '')
            kwargs.setdefault('season_name', kwargs.get('season_name', '') or '')
            kwargs.setdefault('ep_num', kwargs.get('ep_num', '') or '')
            try:
                return template.format(**kwargs)
            except KeyError as ke:
                missing = str(ke).strip("'\"")
                kwargs[missing] = ''
                try:
                    return template.format(**kwargs)
                except Exception:
                    return template
        
        if post_type in ('post_gen_anime', 'post_gen_movie'):
            context.user_data['is_episode_post'] = False
            poster_id = anime_doc.get('poster_id')
            description = anime_doc.get('description', '') or ""
            
            caption_template = await format_message(context, "post_gen_anime_caption")
            caption = _safe_caption_format(caption_template, anime_name=anime_name, series_name=anime_name, movie_name=anime_name, description=description)
        
        elif not ep_num and season_name:
            context.user_data['is_episode_post'] = False
            dl_callback_data = f"dl{anime_id}__{season_name}" 
            
            season_data = anime_doc.get("seasons", {}).get(season_name, {})
            poster_id = season_data.get("_poster_id") or anime_doc.get('poster_id')
            description = season_data.get("_description") or anime_doc.get('description', '') or ""
            
            caption_template = await format_message(context, "post_gen_season_caption")
            caption = _safe_caption_format(caption_template, anime_name=anime_name, series_name=anime_name, season_name=season_name, description=description)
    
        elif ep_num:
            context.user_data['is_episode_post'] = True
            dl_callback_data = f"dl{anime_id}__{season_name}__{ep_num}" 
            
            caption_template = await format_message(context, "post_gen_episode_caption")
            caption = _safe_caption_format(caption_template, anime_name=anime_name, series_name=anime_name, season_name=season_name, ep_num=ep_num)
            poster_id = None 
        
        else:
            logger.warning(f"Post generator invalid state. type={post_type} season={season_name} ep={ep_num}")
            text = await format_message(context, "admin_post_gen_invalid_state")
            try:
                await query.edit_message_text(text, parse_mode=ParseMode.HTML)
            except Exception:
                await query.message.reply_text(text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        
        links = config.get('links', {})
        backup_url = links.get('backup') or "https://t.me/"
        help_url = links.get('help') or "https://t.me/"
        donate_url = f"https://t.me/{bot_username}?start=donate"
        
        original_download_url = f"https://t.me/{bot_username}?start={dl_callback_data}"
        
        btn_backup = InlineKeyboardButton("Backup", url=backup_url)
        btn_donate = InlineKeyboardButton("Donate", url=donate_url)
        btn_help = InlineKeyboardButton("🆘 Help", url=help_url)
        
        # Verify / How to Verify button
        t_verify = config.get("btn_text_verify") or "How to Verify"
        verify_url = links.get('verify') or config.get('verify_url')
        if verify_url:
            btn_verify = InlineKeyboardButton(t_verify, url=verify_url)
        else:
            btn_verify = InlineKeyboardButton(t_verify, callback_data="user_verify_howto")

        context.user_data['post_caption_raw'] = caption
        context.user_data['post_poster_id'] = poster_id 
        context.user_data['btn_backup'] = btn_backup
        context.user_data['btn_donate'] = btn_donate
        context.user_data['btn_help'] = btn_help
        context.user_data['btn_verify'] = btn_verify
        context.user_data['bot_username'] = bot_username
        context.user_data['original_download_url'] = original_download_url
        context.user_data['is_episode_post'] = context.user_data.get('is_episode_post', False) 
        
        # Pehle jaisa: original link dikhao, short link mango
        text = (
            f"✅ <b>Post Ready!</b>\n\n"
            f"Aapka <b>original download link</b>:\n"
            f"<code>{original_download_url}</code>\n\n"
            f"Ab iska <b>shortened link</b> reply mein bhejo.\n"
            f"(Agar short nahi karna: upar wala link copy karke bhej do, ya <code>skip</code> likho)\n\n"
            f"/cancel - Cancel"
        )
        try:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        except Exception as edit_err:
            logger.warning(f"edit_message_text failed: {edit_err}")
            await query.message.reply_text(text, parse_mode=ParseMode.HTML)
        
        return PG_GET_SHORT_LINK 
        
    except Exception as e:
        logger.error(f"Post generate karne me error: {e}", exc_info=True)
        try:
            await query.answer(f"Error: {str(e)[:80]}", show_alert=True)
        except Exception:
            pass
        error_text = f"❌ <b>Post generate nahi ho paya</b>\n\n<code>{str(e)}</code>"
        try:
            await query.edit_message_text(error_text, parse_mode=ParseMode.HTML)
        except Exception:
            try:
                await query.message.reply_text(error_text, parse_mode=ParseMode.HTML)
            except Exception:
                pass
        context.user_data.clear()
        return ConversationHandler.END
        
async def post_gen_get_short_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Original link ke baad short link save karke PREVIEW pe le jata hai"""
    try:
        raw = (update.message.text or "").strip()
        short_link_url = raw.strip("<> \t\n\r\"'")
        original = context.user_data.get('original_download_url') or ""
        
        # skip / empty -> original
        if not short_link_url or short_link_url.lower() in ("skip", "/skip", "-", "none"):
            short_link_url = original
        
        # auto https
        low = short_link_url.lower()
        if short_link_url and not low.startswith(("http://", "https://", "tg://")):
            if "." in short_link_url and " " not in short_link_url:
                short_link_url = "https://" + short_link_url.lstrip("/")
        
        if not short_link_url or not short_link_url.lower().startswith(("http://", "https://", "tg://")):
            await update.message.reply_text(
                "❌ Valid link bhejo.\n\n"
                f"Original:\n<code>{original}</code>\n\n"
                "Short link (https://...) paste karo, ya original copy karke bhejo.\n"
                "Skip ke liye: <code>skip</code>",
                parse_mode=ParseMode.HTML
            )
            return PG_GET_SHORT_LINK
        
        # Save short link
        context.user_data['short_link_url'] = short_link_url
        m = await update.message.reply_text(
            f"✅ <b>Short link set for this post only</b> (DB mein save nahi)\n\n<code>{short_link_url}</code>",
            parse_mode=ParseMode.HTML
        )
        await schedule_admin_msg_delete(context.bot, m.chat_id, m.message_id, 60)
        
        caption_raw = context.user_data.get('post_caption_raw') or ""
        poster_id = context.user_data.get('post_poster_id')
        is_episode_post = context.user_data.get('is_episode_post', False)
        
        config = await get_config()
        t_backup = config.get("btn_text_backup") or "Backup"
        t_verify = config.get("btn_text_verify") or "How to Verify"
        t_donate = config.get("btn_text_donate") or "Donate"
        t_request = config.get("btn_text_request") or "Request a Movie"
        t_download = config.get("btn_text_download") or "⬇️ DOWNLOAD"
        
        try:
            bot_uname = (await context.bot.get_me()).username
        except Exception:
            bot_uname = context.user_data.get('bot_username') or ""
        if not bot_uname:
            bot_uname = "bot"
        context.user_data['bot_username'] = bot_uname
        links = config.get("links", {}) or {}
        
        backup_url = links.get("backup") or f"https://t.me/{bot_uname}"
        donate_url = f"https://t.me/{bot_uname}?start=donate"
        verify_bot_url = f"https://t.me/{bot_uname}?start=verify"
        request_url = f"https://t.me/{bot_uname}?start=request"
        
        btn_map = {
            "backup": InlineKeyboardButton(t_backup, url=backup_url),
            "verify": InlineKeyboardButton(t_verify, url=verify_bot_url),
            "donate": InlineKeyboardButton(t_donate, url=donate_url),
            "request": InlineKeyboardButton(t_request, url=request_url),
            "download": InlineKeyboardButton(t_download, url=short_link_url),
        }
        show = {
            "backup": config.get("btn_show_backup", True),
            "verify": config.get("btn_show_verify", True),
            "donate": config.get("btn_show_donate", True),
            "request": config.get("btn_show_request", True),
            "download": config.get("btn_show_download", True),
        }
        layout = config.get("post_button_layout") or [
            ["backup", "verify"],
            ["donate", "request"],
            ["download"],
        ]
        keyboard = []
        for row_keys in layout:
            row = []
            for key in row_keys:
                if show.get(key, True) and key in btn_map:
                    row.append(btn_map[key])
            if row:
                keyboard.append(row)
        if not keyboard:
            keyboard = [[btn_map["download"]]]
        
        context.user_data['post_keyboard'] = InlineKeyboardMarkup(keyboard)
        
        # Use actual appearance settings from config (not hardcoded default)
        font_settings = config.get("appearance", {"font": "default", "style": "normal"})
        try:
            caption_formatted = await apply_font_formatting(caption_raw, font_settings)
        except Exception:
            caption_formatted = caption_raw
        
        context.user_data['post_caption_formatted'] = caption_formatted
        context.user_data['post_caption_raw'] = caption_raw
        
        # Parse 3 parts — smart: only treat first <b> as title if it matches anime_name
        # (warna custom templates jisme TYPE/IMDB etc bold hote hain, unko tod do mat)
        import re as _re
        anime_name = (context.user_data.get('anime_name') or '').strip()
        title_match = _re.search(r'<b>([^<]+)</b>', caption_formatted or "")
        extracted_title = title_match.group(1).strip() if title_match else ''
        
        # Sirf tab title extract karo jab extracted text anime_name se match kare
        # (TYPE / IMDB / STATUS jaise field labels ko title mat banao)
        is_real_title = False
        if extracted_title and anime_name:
            et = extracted_title.lower().strip()
            an = anime_name.lower().strip()
            if et == an or et in an or an in et:
                is_real_title = True
            # short code exact match (WFL == WFL)
            elif len(extracted_title) <= 15 and et.replace(' ', '') == an.replace(' ', ''):
                is_real_title = True
        
        # TYPE/IMDB style templates always complex (3 blockquotes)
        looks_complex = bool(
            caption_formatted and (
                'TYPE' in caption_formatted.upper() or
                'IMDB' in caption_formatted.upper() or
                'LANGUAGE' in caption_formatted.upper() or
                '<blockquote' in caption_formatted.lower()
            )
        )
        if is_real_title and title_match and not looks_complex:
            context.user_data['post_edit_title'] = extracted_title
            rest = caption_formatted[title_match.end():].strip().lstrip('\n')
            context.user_data['post_is_complex'] = False
        else:
            context.user_data['post_edit_title'] = anime_name or extracted_title or ''
            rest = caption_formatted or ""
            context.user_data['post_is_complex'] = True
        
        lines = rest.split('\n')
        footer_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if 'Download' in lines[i] or 'download' in lines[i] or 'Press On' in lines[i]:
                footer_idx = i
                break
        if footer_idx is not None:
            footer = '\n'.join(lines[footer_idx:]).strip()
            middle = '\n'.join(lines[:footer_idx]).strip()
        else:
            footer = ''
            middle = rest
        if middle:
            middle = _re.sub(r'\n{3,}', '\n\n', middle).strip()
        
        context.user_data['post_edit_footer'] = footer
        context.user_data['post_edit_middle'] = middle
        context.user_data['post_is_quoted'] = False
        # Original full caption bhi rakh lo (edit se pehle)
        context.user_data['post_caption_original'] = caption_formatted or ''
        
        try:
            caption_formatted = await _rebuild_post_caption(context)
        except Exception as e:
            logger.error(f"rebuild caption: {e}")
        context.user_data['post_caption_formatted'] = caption_formatted
        
        default_chat = config.get("default_publish_chat")
        preview_text = "👁️ <b>POST PREVIEW</b>\n\n" + (caption_formatted or "")
        preview_kb = [
            [InlineKeyboardButton("✅ Publish", callback_data="post_preview_publish")],
            [InlineKeyboardButton("✏️ Edit Title/Desc", callback_data="post_preview_edit")],
            [InlineKeyboardButton("📝 Toggle Quote", callback_data="post_preview_quote")],
        ]
        if default_chat:
            preview_kb.append([InlineKeyboardButton(f"📍 Default: {default_chat}", callback_data="noop")])
        preview_kb.append([InlineKeyboardButton("🔄 Change Chat ID", callback_data="post_preview_change_chat")])
        preview_kb.append([InlineKeyboardButton("❌ Cancel", callback_data="post_preview_cancel")])
        
        preview_text = sanitize_telegram_html(preview_text)
        context.user_data['post_caption_formatted'] = sanitize_telegram_html(caption_formatted or "")
        
        async def _send_preview(text_to_send):
            if is_episode_post or not poster_id:
                await update.message.reply_text(text_to_send, reply_markup=InlineKeyboardMarkup(preview_kb), parse_mode=ParseMode.HTML)
            else:
                try:
                    # Telegram caption limit 1024
                    cap = text_to_send if len(text_to_send) <= 1024 else text_to_send[:1000] + "..."
                    await update.message.reply_photo(photo=poster_id, caption=cap, reply_markup=InlineKeyboardMarkup(preview_kb), parse_mode=ParseMode.HTML)
                except Exception as pe:
                    logger.warning(f"preview photo failed: {pe}")
                    await update.message.reply_text(text_to_send, reply_markup=InlineKeyboardMarkup(preview_kb), parse_mode=ParseMode.HTML)
        
        try:
            await _send_preview(preview_text)
        except Exception as html_err:
            logger.warning(f"HTML preview failed, fallback plain: {html_err}")
            # Strip all tags for plain fallback
            import re as _re2
            plain = _re2.sub(r'<[^>]+>', '', preview_text)
            try:
                await update.message.reply_text(
                    plain,
                    reply_markup=InlineKeyboardMarkup(preview_kb)
                )
            except Exception as e2:
                await update.message.reply_text(
                    f"Preview error: {e2}\nShort link saved. Try Publish from menu or /cancel"
                )
        
        return PG_PREVIEW
        
    except Exception as e:
        logger.error(f"post_gen_get_short_link error: {e}", exc_info=True)
        err = str(e).replace("<", "").replace(">", "")
        await update.message.reply_text(
            f"❌ Short link / preview error:\n{err[:200]}\n\nLink phir se bhejo ya /cancel"
        )
        return PG_GET_SHORT_LINK

async def post_gen_send_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_raw = update.message.text.strip()
    is_episode_post = context.user_data.get('is_episode_post', False) 
    caption_text = sanitize_telegram_html(context.user_data.get('post_caption_formatted', '') or '')
    
    try:
        chat_id = int(chat_id_raw) if chat_id_raw.lstrip('-').isdigit() else chat_id_raw
        
        if is_episode_post or not context.user_data.get('post_poster_id'):
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data.get('post_keyboard')
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=context.user_data['post_poster_id'],
                caption=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data.get('post_keyboard')
            )

        text = await format_message(context, "admin_post_gen_success", {"chat_id": chat_id_raw})
        m = await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        await schedule_admin_msg_delete(context.bot, m.chat_id, m.message_id, 60)
    except Exception as e:
        logger.error(f"Post channel me bhejme me error: {e}")
        text = await format_message(context, "admin_post_gen_error", {"chat_id": chat_id_raw, "e": e})
        m = await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        await schedule_admin_msg_delete(context.bot, m.chat_id, m.message_id, 60)
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ===     POST PREVIEW + EDIT HANDLERS     ===
# ============================================
async def _safe_edit_preview(query, text, reply_markup=None, auto_delete_sec=None):
    """Photo ya text edit; admin DM msgs auto-delete (from config admin_preview_delete_seconds)"""
    if auto_delete_sec is None:
        try:
            cfg = config_collection.find_one({"_id": "bot_config"}) or {}
            auto_delete_sec = int(cfg.get("admin_preview_delete_seconds") or 30)
        except Exception:
            auto_delete_sec = 30
    msg = None
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            msg = query.message
        else:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            msg = query.message
    except Exception:
        try:
            msg = await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e2:
            logger.error(f"_safe_edit_preview failed: {e2}")
            return
    if msg and auto_delete_sec:
        try:
            await schedule_admin_msg_delete(query.get_bot(), msg.chat_id, msg.message_id, auto_delete_sec)
        except Exception:
            try:
                asyncio.create_task(delete_message_later(query.get_bot(), msg.chat_id, msg.message_id, auto_delete_sec))
            except Exception:
                pass

async def post_preview_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Fix broken HTML from description/title edits
    if context.user_data.get('post_caption_formatted'):
        context.user_data['post_caption_formatted'] = sanitize_telegram_html(context.user_data['post_caption_formatted'])
    config = await get_config()
    default_chat = config.get("default_publish_chat")
    
    if not default_chat:
        await _safe_edit_preview(query, "❌ Default Publish Chat set nahi hai.\n\nPehle <b>Admin Settings → Default Publish Chat</b> set karein, ya 'Change Chat ID' use karein.")
        return PG_PREVIEW
    
    is_episode_post = context.user_data.get('is_episode_post', False)
    caption_text = context.user_data.get('post_caption_formatted', '')
    
    try:
        chat_id = default_chat
        # agar number hai to int banao
        if str(chat_id).lstrip('-').isdigit():
            chat_id = int(chat_id)
            
        if is_episode_post or not context.user_data.get('post_poster_id'):
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data.get('post_keyboard')
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=context.user_data['post_poster_id'],
                caption=caption_text,
                parse_mode=ParseMode.HTML,
                reply_markup=context.user_data.get('post_keyboard')
            )
        cfg = await get_config()
        admin_clean_sec = int(cfg.get("admin_preview_delete_seconds") or 30)
        await _safe_edit_preview(query, f"✅ Post successfully published to <code>{default_chat}</code>!", auto_delete_sec=admin_clean_sec)
        # Admin DM: tracked post-related msgs + success — sab clear after timer
        try:
            if query.message:
                track_dm_msg(query.message.chat_id, query.message.message_id)
            await schedule_clear_user_dm(context.bot, query.from_user.id, admin_clean_sec)
        except Exception as e:
            logger.warning(f"admin DM clear schedule: {e}")
    except Exception as e:
        logger.error(f"Preview publish error: {e}", exc_info=True)
        await _safe_edit_preview(query, f"❌ Publish failed:\n<code>{e}</code>\n\nChat ID check karo ya bot ko channel/group mein admin banao.")
    context.user_data.clear()
    return ConversationHandler.END

async def post_preview_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("1️⃣ Edit Title", callback_data="post_edit_title")],
        [InlineKeyboardButton("2️⃣ Edit Description (middle)", callback_data="post_edit_desc")],
        [InlineKeyboardButton("3️⃣ Edit Download Line", callback_data="post_edit_footer")],
        [InlineKeyboardButton("⬅️ Back to Preview", callback_data="post_preview_back")]
    ]
    await _safe_edit_preview(query, 
        "✏️ <b>Temporary Edit</b> (sirf is post ke liye)\n\n"
        "1️⃣ <b>Title</b> – upar wala naam\n"
        "2️⃣ <b>Description</b> – TYPE / LANGUAGE / QUALITY wala block\n"
        "3️⃣ <b>Download Line</b> – neeche Press On Download\n\n"
        "Database mein original save rahega.",
        InlineKeyboardMarkup(keyboard))
    return PG_EDIT_MENU

def _get_preview_keyboard():
    return [
        [InlineKeyboardButton("✅ Publish", callback_data="post_preview_publish")],
        [InlineKeyboardButton("✏️ Edit Title/Desc", callback_data="post_preview_edit")],
        [InlineKeyboardButton("📝 Toggle Quote", callback_data="post_preview_quote")],
        [InlineKeyboardButton("🔄 Change Chat ID", callback_data="post_preview_change_chat")],
        [InlineKeyboardButton("❌ Cancel", callback_data="post_preview_cancel")]
    ]

async def _rebuild_post_caption(context):
    """Title + middle + footer — temporary only, no DB. Preserve fonts/bold/blockquote. No double title."""
    import re as _re
    title = context.user_data.get('post_edit_title', '') or ''
    middle = context.user_data.get('post_edit_middle', '') or ''
    footer = context.user_data.get('post_edit_footer', '') or ''
    is_quoted = context.user_data.get('post_is_quoted', False)
    is_complex = context.user_data.get('post_is_complex', False)
    
    # Complex templates — 3 clean blockquotes (Telegram-safe HTML)
    if is_complex:
        import re as _re2
        details = (middle or context.user_data.get('post_caption_original') or
                   context.user_data.get('post_caption_formatted', '') or '')
        # Strip any existing blockquote wrappers from details so we re-wrap cleanly
        details = _re2.sub(r'</?blockquote[^>]*>', '', details, flags=_re2.I).strip()
        # Remove leading title from details if present (title gets own block)
        if title:
            esc = _re2.escape(title)
            details = _re2.sub(
                rf'^(?:<b>)?\s*{esc}\s*(?:</b>)?\s*\n*',
                '',
                details,
                count=1,
                flags=_re2.I
            ).strip()
        # Clean footer of blockquote tags
        ft = (footer or '').strip()
        ft = _re2.sub(r'</?blockquote[^>]*>', '', ft, flags=_re2.I).strip()
        
        parts = []
        if title:
            # Title short — normal quote (not collapsed)
            parts.append(f"<blockquote><b>{title}</b></blockquote>")
        if details:
            # Details long — EXPANDABLE / collapsible quote
            parts.append(f"<blockquote expandable>{details}</blockquote>")
        if ft:
            # Press On Download — normal quote
            parts.append(f"<blockquote>{ft}</blockquote>")
        
        caption = "\n\n".join(parts) if parts else details
        # Light sanitize — balance only
        caption = sanitize_telegram_html(caption or "")
        context.user_data['post_caption_formatted'] = caption
        return caption
    
    # Sirf empty blockquotes clean; content blockquote MAT hatao
    if middle:
        middle = _re.sub(r'<blockquote[^>]*>\s*</blockquote>', '', middle).strip()
        context.user_data['post_edit_middle'] = middle
    
    has_blockquote = bool(middle and '<blockquote' in middle.lower())
    
    # Double title avoid: agar middle pehle se title se start hota hai to outer title skip
    title_already_in_middle = False
    if title and middle:
        esc = _re.escape(title)
        if _re.match(rf'^(?:\s*<blockquote[^>]*>\s*)?(?:<b>)?\s*{esc}\s*(?:</b>)?', middle, flags=_re.I):
            title_already_in_middle = True
    
    parts = []
    if title and not has_blockquote and not title_already_in_middle:
        parts.append(f"<b>{title}</b>")
    if middle:
        parts.append(middle)
    if footer:
        parts.append(footer)
    
    caption = "\n\n".join(parts) if parts else (context.user_data.get('post_caption_original') or context.user_data.get('post_caption_formatted', ''))
    
    # Toggle Quote: only wrap if no blockquote already present
    if is_quoted and caption and "<blockquote" not in caption.lower():
        caption = f"<blockquote>{caption}</blockquote>"
    
    caption = sanitize_telegram_html(caption or "")
    context.user_data['post_caption_formatted'] = caption
    return caption

async def post_preview_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    is_quoted = context.user_data.get('post_is_quoted', False)
    context.user_data['post_is_quoted'] = not is_quoted
    caption = await _rebuild_post_caption(context)
    await query.answer("Quote ON" if context.user_data['post_is_quoted'] else "Quote OFF", show_alert=False)
    await _safe_edit_preview(query, "👁️ <b>POST PREVIEW</b>\n\n" + caption, InlineKeyboardMarkup(_get_preview_keyboard()))
    return PG_PREVIEW

async def post_preview_change_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _safe_edit_preview(query, "🔄 Naya <b>Chat ID</b> ya <b>@username</b> bhejo:\n\n/cancel to cancel")
    return PG_GET_CHAT

async def post_preview_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await _safe_edit_preview(query, "❌ Post cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def post_preview_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    caption = context.user_data.get('post_caption_formatted', '')
    await _safe_edit_preview(query, "👁️ <b>POST PREVIEW</b>\n\n" + caption, InlineKeyboardMarkup(_get_preview_keyboard()))
    return PG_PREVIEW

async def post_edit_title_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = context.user_data.get('post_edit_title', '')
    msg = "1️⃣ <b>Edit Title</b>\n\nSirf naya title bhejo (HTML nahi chahiye):\n\n"
    if current:
        msg += f"Current: <code>{current}</code>\n\n"
    msg += "/cancel to cancel"
    await _safe_edit_preview(query, msg)
    return PG_EDIT_TITLE

async def post_edit_title_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_title = update.message.text.strip()
    import re as _re
    new_title = _re.sub(r'<[^>]+>', '', new_title).strip()
    old_title = context.user_data.get('post_edit_title', '') or ''
    context.user_data['post_edit_title'] = new_title
    
    # Middle + footer mein purana title replace
    for key in ('post_edit_middle', 'post_edit_footer'):
        part = context.user_data.get(key, '') or ''
        if old_title and old_title in part:
            part = part.replace(old_title, new_title)
            context.user_data[key] = part
    
    # Complex: title alag blockquote mein rebuild se aayega
    # Middle se purana title text hata do taaki details clean rahein
    middle = context.user_data.get('post_edit_middle', '') or ''
    if old_title and middle and old_title in middle:
        middle = middle.replace(old_title, '').strip()
        context.user_data['post_edit_middle'] = middle
    # new title sirf post_edit_title mein — rebuild 3-block structure banayega
    
    caption = await _rebuild_post_caption(context)
    caption = sanitize_telegram_html(caption or "")
    context.user_data['post_caption_formatted'] = caption
    
    await update.message.reply_text("✅ Title updated (sirf is post ke liye, DB mein nahi).", parse_mode=ParseMode.HTML)
    try:
        await update.message.reply_text(
            "👁️ <b>POST PREVIEW</b>\n\n" + caption,
            reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        logger.error(f"Title update preview BadRequest: {e}")
        # Fallback: send without broken tags
        safe_cap = _re.sub(r'<[^>]+>', '', caption)
        await update.message.reply_text(
            "👁️ <b>POST PREVIEW</b>\n\n" + safe_cap,
            reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()),
            parse_mode=ParseMode.HTML
        )
    return PG_PREVIEW

async def post_edit_desc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = context.user_data.get('post_edit_middle', '') or ''
    current = sanitize_telegram_html(current)  # show clean tags
    context.user_data['post_edit_middle'] = current
    # Show raw so user can keep blockquote tags
    msg = "2️⃣ <b>Edit Description (middle block)</b>\n\n"
    msg += "Neeche current text hai. Copy karke change karke bhejo.\n"
    msg += "Blockquote / bold tags rakh sakte ho.\n\n"
    if current:
        # Escape for display in code so tags visible
        shown = current.replace('<', '&lt;').replace('>', '&gt;')
        if len(shown) > 900:
            shown = shown[:900] + "..."
        msg += f"<b>Current (copy this):</b>\n<code>{shown}</code>\n\n"
    msg += "/cancel to cancel"
    await _safe_edit_preview(query, msg)
    return PG_EDIT_DESC

async def post_edit_desc_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_middle = update.message.text.strip()
    # User might paste escaped or raw - accept both
    new_middle = new_middle.replace('&lt;', '<').replace('&gt;', '>')
    context.user_data['post_edit_middle'] = new_middle
    caption = await _rebuild_post_caption(context)
    caption = sanitize_telegram_html(caption or "")
    context.user_data['post_caption_formatted'] = caption
    await update.message.reply_text("✅ Description updated (sirf is post ke liye, DB mein nahi).", parse_mode=ParseMode.HTML)
    try:
        await update.message.reply_text("👁️ <b>POST PREVIEW</b>\n\n" + caption, reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        logger.error(f"Desc update preview BadRequest: {e}")
        safe_cap = re.sub(r'<[^>]+>', '', caption)
        await update.message.reply_text("👁️ <b>POST PREVIEW</b>\n\n" + safe_cap, reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()), parse_mode=ParseMode.HTML)
    return PG_PREVIEW

async def post_edit_footer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    current = context.user_data.get('post_edit_footer', '') or ''
    msg = "3️⃣ <b>Edit Download Line</b>\n\n"
    msg += "Neeche wala line (Press On Download etc.)\n\n"
    if current:
        shown = current.replace('<', '&lt;').replace('>', '&gt;')
        msg += f"Current: <code>{shown}</code>\n\n"
    msg += "/cancel to cancel"
    await _safe_edit_preview(query, msg)
    return PG_EDIT_FOOTER

async def post_edit_footer_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_footer = update.message.text.strip()
    new_footer = new_footer.replace('&lt;', '<').replace('&gt;', '>')
    context.user_data['post_edit_footer'] = new_footer
    caption = await _rebuild_post_caption(context)
    caption = sanitize_telegram_html(caption or "")
    context.user_data['post_caption_formatted'] = caption
    await update.message.reply_text("✅ Download line updated.", parse_mode=ParseMode.HTML)
    try:
        await update.message.reply_text("👁️ <b>POST PREVIEW</b>\n\n" + caption, reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()), parse_mode=ParseMode.HTML)
    except BadRequest as e:
        logger.error(f"Footer update preview BadRequest: {e}")
        safe_cap = re.sub(r'<[^>]+>', '', caption)
        await update.message.reply_text("👁️ <b>POST PREVIEW</b>\n\n" + safe_cap, reply_markup=InlineKeyboardMarkup(_get_preview_keyboard()), parse_mode=ParseMode.HTML)
    return PG_PREVIEW

# --- NAYA: Conversation: Generate Link ---
async def gen_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Movie Link", callback_data="gen_link_movie")],
        [InlineKeyboardButton("🔗 Complete Series Link", callback_data="gen_link_anime")],
        [InlineKeyboardButton("🔗 Season Link", callback_data="gen_link_season")],
        [InlineKeyboardButton("🔗 Episode Link", callback_data="gen_link_episode")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_gen_link")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_MENU

async def gen_link_select_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    link_type = query.data
    context.user_data['link_type'] = link_type
    
    return await gen_link_show_anime_list(update, context, page=0)

async def gen_link_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("genlink_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    context.user_data['current_page'] = page
    link_type = context.user_data.get('link_type', '')
    
    if link_type == 'gen_link_movie':
        filter_query = {"type": "movie"}
        list_label = "Movie"
    else:
        # Series only
        filter_query = {"$or": [{"type": "series"}, {"type": {"$exists": False}}]}
        list_label = "Series"
        
    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="genlink_page_",
        item_callback_prefix="gen_link_anime_",
        back_callback="admin_gen_link",
        filter_query=filter_query
    )
    
    if not animes and page == 0:
        text = f"❌ Abhi koi <b>{list_label}</b> add nahi hua hai."
    else:
        text = f"Kaunsa <b>{list_label}</b> select karna hai?\n\n(Page {page + 1})"

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return GL_GET_ANIME

async def gen_link_select_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("gen_link_anime_", "")
    context.user_data['anime_name'] = anime_name
    
    if context.user_data['link_type'] in ('gen_link_anime', 'gen_link_movie'):
        context.user_data['season_name'] = None
        context.user_data['ep_num'] = None 
        return await gen_link_finish(update, context) 
    
    anime_doc = animes_collection.find_one({"name": anime_name})
    seasons = anime_doc.get("seasons", {})
    if not seasons:
        text = await format_message(context, "admin_gen_link_no_season", {"anime_name": anime_name})
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_gen_link")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"gen_link_season_{s}") for s in sorted_seasons]
    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"genlink_page_{current_page}")])

    text = await format_message(context, "admin_gen_link_select_season", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_GET_SEASON

async def gen_link_select_episode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season_name = query.data.replace("gen_link_season_", "")
    context.user_data['season_name'] = season_name
    anime_name = context.user_data['anime_name']
    
    if context.user_data['link_type'] == 'gen_link_season':
        context.user_data['ep_num'] = None 
        return await gen_link_finish(update, context) 
        
    anime_doc = animes_collection.find_one({"name": anime_name})
    episodes = anime_doc.get("seasons", {}).get(season_name, {})
    
    episode_keys = [ep for ep in episodes.keys() if not ep.startswith("_")]
    
    if not episode_keys:
        text = await format_message(context, "admin_gen_link_no_episode", {
            "anime_name": anime_name,
            "season_name": season_name
        })
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_gen_link")]]), parse_mode=ParseMode.HTML)
        return ConversationHandler.END
        
    sorted_eps = sorted(episode_keys, key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
    buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"gen_link_ep_{ep}") for ep in sorted_eps]
    keyboard = build_grid_keyboard(buttons, 2)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Seasons", callback_data=f"gen_link_anime_{anime_name}")])

    text = await format_message(context, "admin_gen_link_select_episode", {"season_name": season_name})
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
        
        anime_name = context.user_data['anime_name']
        season_name = context.user_data.get('season_name')
        ep_num = context.user_data.get('ep_num') 
        
        anime_doc = animes_collection.find_one({"name": anime_name})
        anime_id = str(anime_doc['_id'])
        
        link_type = context.user_data.get('link_type')
        
        dl_callback_data = f"dl{anime_id}" 
        title = anime_name
        
        if link_type == 'gen_link_season' and season_name:
            dl_callback_data = f"dl{anime_id}__{season_name}"
            title = f"{anime_name} - S{season_name}"
        elif link_type == 'gen_link_episode' and season_name and ep_num:
            dl_callback_data = f"dl{anime_id}__{season_name}__{ep_num}"
            title = f"{anime_name} - S{season_name} E{ep_num}"
        
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

# --- Conversation: Update Photo (NAYA: Sub-menu) ---
async def update_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await update_photo_show_anime_list(update, context, page=0)

async def update_photo_show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    query = update.callback_query
    
    if query.data.startswith("upphoto_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
        
    context.user_data['current_page'] = page 

    animes, keyboard = await build_paginated_keyboard(
        collection=animes_collection,
        page=page,
        page_callback_prefix="upphoto_page_",
        item_callback_prefix="upphoto_anime_",
        back_callback="back_to_update_photo_menu" # NAYA: Back to sub-menu
    )
    
    if not animes and page == 0:
        text = await format_message(context, "admin_update_photo_no_anime")
    else:
        text = await format_message(context, "admin_update_photo_select_anime", {"page": page + 1})

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return UP_GET_ANIME

async def update_photo_select_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    anime_name = query.data.replace("upphoto_anime_", "")
    context.user_data['anime_name'] = anime_name
    anime_doc = animes_collection.find_one({"name": anime_name})
    
    buttons = [InlineKeyboardButton(f"🖼️ Main Anime Poster", callback_data=f"upphoto_target_MAIN")]
    
    seasons = anime_doc.get("seasons", {})
    if seasons:
        sorted_seasons = sorted(seasons.keys(), key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])
        for s in sorted_seasons:
            buttons.append(InlineKeyboardButton(f"S{s} Poster", callback_data=f"upphoto_target_S__{s}"))

    keyboard = build_grid_keyboard(buttons, 1)
    
    current_page = context.user_data.get('current_page', 0)
    keyboard.append([InlineKeyboardButton("⬅️ Back to List", callback_data=f"upphoto_page_{current_page}")])
    
    text = await format_message(context, "admin_update_photo_select_target", {"anime_name": anime_name})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return UP_GET_TARGET

async def update_photo_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target = query.data.replace("upphoto_target_", "")
    context.user_data['target'] = target
    
    if target == "MAIN":
        target_name = "Main Anime Poster"
    else:
        season_name = target.replace("S__", "")
        context.user_data['season_name'] = season_name
        target_name = f"Season {season_name} Poster"

    text = await format_message(context, "admin_update_photo_get_poster", {"target_name": target_name})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return UP_GET_POSTER

async def update_photo_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_update_photo_invalid")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return UP_GET_POSTER 

async def update_photo_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_update_photo_save_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return UP_GET_POSTER
    
    poster_id = update.message.photo[-1].file_id
    anime_name = context.user_data['anime_name']
    target = context.user_data['target']
    
    try:
        update_query = {"$set": {"last_modified": datetime.now()}} # NAYA: Timestamp
        
        if target == "MAIN":
            update_query["$set"]["poster_id"] = poster_id
            animes_collection.update_one({"name": anime_name}, update_query)
            caption = await format_message(context, "admin_update_photo_save_success_main", {"anime_name": anime_name})
            logger.info(f"Main poster change ho gaya: {anime_name}")
        else:
            season_name = context.user_data['season_name']
            update_query["$set"][f"seasons.{season_name}._poster_id"] = poster_id
            animes_collection.update_one(
                {"name": anime_name}, 
                update_query
            )
            caption = await format_message(context, "admin_update_photo_save_success_season", {
                "anime_name": anime_name,
                "season_name": season_name
            })
            logger.info(f"Season poster change ho gaya: {anime_name} S{season_name}")

        await update.message.reply_photo(photo=poster_id, caption=caption, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Poster change karne me error: {e}")
        text = await format_message(context, "admin_update_photo_save_error_db")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_command(update, context, from_callback=False) 
    return ConversationHandler.END
# --- Conversation: Set Auto-Delete Time ---
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
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_auto_delete")]]))
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

# --- Conversation: Set Donate QR ---
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
# --- Conversation: Set Links ---
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
    elif link_type == "verify_link":
        context.user_data['link_type'] = "verify"
        text = "✅ <b>Verify / How-to-Download Link</b> bhejo:\n(Example: https://t.me/... or any URL)\n\n/skip - Clear\n/cancel - Cancel"
        back_button = "back_to_links"
    elif link_type == "request_link":
        context.user_data['link_type'] = "request"
        text = "🎬 <b>Request a Movie Link</b> bhejo:\n(Example: https://t.me/... or Google Form)\n\n/skip - Clear\n/cancel - Cancel"
        back_button = "back_to_links"
    else:
        text = "❌ Invalid link type."
        await query.answer(text, show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_button)]]))
    return CL_GET_LINK 

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_url = update.message.text.strip()
    link_type = context.user_data.get('link_type')
    if not link_type:
        await update.message.reply_text("❌ Error: link type missing. Try again.")
        return ConversationHandler.END
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"links.{link_type}": link_url}}, upsert=True)
    logger.info(f"{link_type} link update ho gaya: {link_url}")
    await update.message.reply_text(f"✅ <b>{link_type}</b> link saved:\n<code>{link_url}</code>", parse_mode=ParseMode.HTML)
    try:
        await other_links_menu(update, context)
    except Exception:
        pass
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
# --- NAYA: Conversation: Set Custom Messages (PAGINATED) ---
async def set_msg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg_key = query.data.replace("msg_edit_", "")
    
    config = await get_config()
    current_msg = config.get("messages", {}).get(msg_key, "N/A")
    
    context.user_data['msg_key'] = msg_key
    
    # current_msg ko HTML se escape karo taaki <code> me sahi dikhe
    safe_current_msg = current_msg.replace('<', '&lt;').replace('>', '&gt;')
    
    text = await format_message(context, "admin_set_msg_start", {
        "msg_key": msg_key,
        "current_msg": safe_current_msg
    })
    
    if msg_key.startswith("user_dl_") or msg_key == "file_warning":
        back_cb = "msg_menu_dl"
    elif msg_key.startswith("post_gen_"):
        back_cb = "msg_menu_postgen"
    elif msg_key.startswith("admin_"): # NAYA
        back_cb = "msg_menu_admin"
    else:
        back_cb = "msg_menu_gen"
        
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_cb)]]))
    return M_GET_MSG

async def set_msg_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg_text = update.message.text or ''
        # Code-block se copy / entities unescape
        msg_text = (msg_text.replace('&lt;', '<').replace('&gt;', '>')
                   .replace('&amp;', '&').replace('&quot;', '"'))
        msg_text = msg_text.replace('\u200b', '').replace('\ufeff', '').strip()
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
    
# --- Conversation: Admin Settings (Co-Admin, Custom Post, Broadcast) ---
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
    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Co-Admin Banao", callback_data="co_admin_add_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
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

    keyboard = [[InlineKeyboardButton(f"✅ Haan, {user_id} ko Remove Karo", callback_data="co_admin_rem_yes")], [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]
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
            text += f"- <code>{admin_id}</code>\n" # <pre> hata diya

    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]]))
    return ConversationHandler.END


# --- Conversation: Custom Post ---
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

    # NAYA: Caption ko format karo (default font me)
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

    # NAYA: Caption ko format karo (default font me)
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

# --- NAYA (v34): Conversation: Broadcast ---
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
    # Message ko context me store karo
    context.user_data['broadcast_message'] = update.message
    
    # User count fetch karo
    user_count = users_collection.count_documents({})
    context.user_data['user_count'] = user_count
    
    text = await format_message(context, "admin_broadcast_confirm", {"user_count": user_count})
    keyboard = [
        [InlineKeyboardButton(f"✅ Haan, {user_count} Users ko Bhejo", callback_data="broadcast_confirm_yes")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    
    # Message ko "preview" ki tarah forward karo
    try:
        await update.message.forward(chat_id=update.effective_chat.id)
    except Exception as e:
        logger.warning(f"Broadcast preview forward nahi kar paya: {e}")
        # Agar forward fail ho (jaise text), toh reply karo
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
    
    # Naya thread/task start karo broadcast ke liye taaki UI block na ho
    asyncio.create_task(send_broadcast_task(context, message_to_send, query.from_user.id))

    context.user_data.clear()
    await asyncio.sleep(3)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def send_broadcast_task(context: ContextTypes.DEFAULT_TYPE, message: Update.message, admin_user_id: int):
    """
    Asynchronously sabhi users ko message bhejega.
    """
    all_users = users_collection.find({}, {"_id": 1})
    sent_count = 0
    failed_count = 0
    
    for user in all_users:
        user_id = user["_id"]
        try:
            # Message ko copy karke bhejo
            await message.copy(chat_id=user_id)
            sent_count += 1
        except Forbidden:
            logger.warning(f"Broadcast fail: User {user_id} ne bot ko block kiya.")
            failed_count += 1
        except Exception as e:
            logger.error(f"Broadcast fail: User {user_id} ko bhejte waqt error: {e}")
            failed_count += 1
        
        # Rate limit se bachne ke liye thoda pause
        await asyncio.sleep(0.1) # Har 100ms me ek message

    logger.info(f"Broadcast complete. Sent: {sent_count}, Failed: {failed_count}")
    
    # Admin ko report bhejo
    try:
        text = await format_message(context, "admin_broadcast_success", {
            "sent_count": sent_count,
            "failed_count": failed_count
        })
        await context.bot.send_message(chat_id=admin_user_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Admin ko broadcast report bhejte waqt error: {e}")


# --- NAYA: Conversation: Bot Appearance ---
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
    
    # NAYA: sans_serif_regular add kiya
    fonts = ["default", "small_caps", "sans_serif", "sans_serif_regular", "script", "monospace", "serif"]
    buttons = []
    for font in fonts:
        prefix = "✅ " if font == current_font else ""
        buttons.append(InlineKeyboardButton(f"{prefix}{font.title().replace('_', ' ')}", callback_data=f"app_font_{font}"))
        
    keyboard = build_grid_keyboard(buttons, 2)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_appearance")])
    
    text = await format_message(context, "admin_appearance_select_font", {"font": current_font.title().replace('_', ' ')})
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
    
    text = await format_message(context, "admin_appearance_set_font_success", {"font": font.title().replace('_', ' ')})
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
    
    text = await format_message(context, "admin_appearance_select_style", {"style": current_style.title()})
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
    
    text = await format_message(context, "admin_appearance_set_style_success", {"style": style.title()})
    await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    
    await appearance_menu_start(update, context)
    return AP_MENU

# --- Conversation: Set User Menu Photo ---
async def set_menu_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_set_menu_photo_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_to_update_photo_menu")]])) # NAYA
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


async def user_verify_howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify button - how to download video/link bhejo"""
    query = update.callback_query
    await query.answer()
    config = await get_config()
    verify_url = config.get('links', {}).get('verify')
    video_id = config.get('verify_video_id')
    
    if video_id:
        try:
            await context.bot.send_video(
                chat_id=query.from_user.id,
                video=video_id,
                caption="✅ <b>How to Download / Verify</b>\n\nIs video ko dekho aur steps follow karo.",
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            logger.error(f"Verify video send failed: {e}")
    
    if verify_url:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=f"✅ <b>How to Download / Verify</b>\n\n👉 {verify_url}",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.answer("Verify guide abhi set nahi hai. Admin se contact karo.", show_alert=True)

async def set_verify_video_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎬 <b>Verify How-To Video</b>\n\nAb mujhe <b>video</b> bhejo (mp4) jo users ko How to Verify dikhega.\n\n/skip - Clear\n/cancel - Cancel",
        parse_mode=ParseMode.HTML
    )
    return VERIFY_VIDEO

async def set_verify_video_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video and not update.message.document:
        await update.message.reply_text("Please send a video file.")
        return VERIFY_VIDEO
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    if not file_id:
        await update.message.reply_text("❌ Please send a <b>video</b> (not text).", parse_mode=ParseMode.HTML)
        return VERIFY_VIDEO
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"verify_video_id": file_id}},
        upsert=True
    )
    await update.message.reply_text("✅ Verify how-to video save ho gaya!")
    context.user_data.clear()
    return ConversationHandler.END

async def set_verify_video_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config_collection.update_one({"_id": "bot_config"}, {"$unset": {"verify_video_id": ""}})
    await update.message.reply_text("✅ Verify video cleared.")
    return ConversationHandler.END


async def other_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    backup_status = "✅" if config.get('links', {}).get('backup') else "❌"
    download_status = "✅" if config.get('links', {}).get('download') else "❌"
    help_status = "✅" if config.get('links', {}).get('help') else "❌"
    verify_status = "✅" if config.get('links', {}).get('verify') or config.get('verify_video_id') else "❌"
    keyboard = [
        [InlineKeyboardButton(f"Set Backup Link {backup_status}", callback_data="admin_set_backup_link")],
        [InlineKeyboardButton(f"Set Download Link {download_status}", callback_data="admin_set_download_link")], 
        [InlineKeyboardButton(f"Set Help Link {help_status}", callback_data="admin_set_help_link")],
        [InlineKeyboardButton(f"✅ Set Verify Link {verify_status}", callback_data="admin_set_verify_link")],
        [InlineKeyboardButton("🎬 Set Verify How-To Video", callback_data="admin_set_verify_video")],
        [InlineKeyboardButton("🎬 Set Request Link", callback_data="admin_set_request_link")],
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

async def bot_messages_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if await is_co_admin_only(user_id):
        await deny_co_admin_feature(update, context, "Bot Messages")
        return ConversationHandler.END
    if query: await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📥 Download Flow Messages", callback_data="msg_menu_dl")],
        [InlineKeyboardButton("✍️ Post Generator Messages", callback_data="msg_menu_postgen")],
        [InlineKeyboardButton("👑 Admin Flow Messages", callback_data="msg_menu_admin")], # NAYA
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
        [InlineKeyboardButton("Edit Content Not Found", callback_data="msg_edit_user_dl_anime_not_found")],
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
        [InlineKeyboardButton("Edit Request Limit Msg", callback_data="msg_edit_user_request_limit")],
        [InlineKeyboardButton("Edit Request Prompt", callback_data="msg_edit_user_request_prompt")],
        [InlineKeyboardButton("Edit Request Received", callback_data="msg_edit_user_request_received")],
        [InlineKeyboardButton("Edit Request Admin Notify", callback_data="msg_edit_user_request_admin_notify")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")]
    ]
    text = await format_message(context, "admin_menu_messages_gen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_GEN

async def bot_messages_menu_postgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Edit Series/Movie Post Caption", callback_data="msg_edit_post_gen_anime_caption")], 
        [InlineKeyboardButton("Edit Season Post Caption", callback_data="msg_edit_post_gen_season_caption")],
        [InlineKeyboardButton("Edit Episode Post Caption", callback_data="msg_edit_post_gen_episode_caption")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")]
    ]
    text = await format_message(context, "admin_menu_messages_postgen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_POSTGEN

# NAYA: Admin Messages Menu
async def bot_messages_menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Simple list for all admin messages
    keys = await get_default_messages()
    admin_keys = sorted([k for k in keys.keys() if k.startswith("admin_")])
    
    buttons = [InlineKeyboardButton(k.replace("admin_", "").replace("_", " ").title(), callback_data=f"msg_edit_{k}") for k in admin_keys]
    keyboard = build_grid_keyboard(buttons, 1) # 1-column list
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_messages")])
    
    text = await format_message(context, "admin_menu_messages_admin")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_MENU_ADMIN

# NAYA: Admin Settings Menu

# ============================================
# ===     ADMIN CHATS (REQUESTS)           ===
# ============================================
async def admin_chats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    if await is_co_admin_only(update.effective_user.id):
        await deny_co_admin_feature(update, context, "Chats")
        return
    pending = db['movie_requests'].count_documents({"status": "pending"})
    replied = db['movie_requests'].count_documents({"status": "replied"})
    text = (
        f"💬 <b>Chats / Requests</b>\n\n"
        f"📩 Pending: <b>{pending}</b>\n"
        f"✅ Replied: <b>{replied}</b>\n\n"
        f"Choose section:"
    )
    keyboard = [
        [InlineKeyboardButton(f"📩 Requested ({pending})", callback_data="chats_pending_0")],
        [InlineKeyboardButton(f"✅ Replied ({replied})", callback_data="chats_replied_0")],
        [InlineKeyboardButton("🚫 Ban User (3 hours)", callback_data="chats_ban_start")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")],
    ]
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def chats_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # chats_pending_0 or chats_replied_0
    parts = data.split("_")
    status = "pending" if parts[1] == "pending" else "replied"
    page = int(parts[2]) if len(parts) > 2 else 0
    per = 8
    cursor = db['movie_requests'].find({"status": status}).sort("created_at", -1).skip(page * per).limit(per)
    items = list(cursor)
    total = db['movie_requests'].count_documents({"status": status})
    
    title = "📩 Requested" if status == "pending" else "✅ Replied"
    if not items:
        text = f"{title}\n\nNo items."
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_chats_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        return
    
    text = f"<b>{title}</b> (page {page + 1})\n\nSelect a request:"
    keyboard = []
    for doc in items:
        rid = str(doc["_id"])
        label = f"{doc.get('name', '?')[:12]}: {doc.get('text', '')[:30]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"chats_view_{rid}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"chats_{status}_{page-1}"))
    if (page + 1) * per < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"chats_{status}_{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_chats_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def chats_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from bson import ObjectId
    rid = query.data.replace("chats_view_", "")
    try:
        doc = db['movie_requests'].find_one({"_id": ObjectId(rid)})
    except Exception:
        doc = None
    if not doc:
        await query.answer("Not found", show_alert=True)
        return
    context.user_data["chat_reply_req_id"] = rid
    context.user_data["chat_reply_user_id"] = doc.get("user_id")
    text = (
        f"📩 <b>Request</b>\n\n"
        f"From: <b>{doc.get('name')}</b> (@{doc.get('username')})\n"
        f"ID: <code>{doc.get('user_id')}</code>\n"
        f"Status: <b>{doc.get('status')}</b>\n\n"
        f"<b>Text:</b>\n<code>{doc.get('text')}</code>\n"
    )
    if doc.get("admin_reply"):
        text += f"\n<b>Your reply:</b>\n{doc.get('admin_reply')}\n"
    keyboard = [
        [InlineKeyboardButton("💬 Reply to User", callback_data=f"chats_reply_{rid}")],
        [InlineKeyboardButton("🚫 Ban 3h", callback_data=f"chats_banuser_{doc.get('user_id')}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_chats_menu")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def chats_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rid = query.data.replace("chats_reply_", "")
    context.user_data["chat_reply_req_id"] = rid
    await query.edit_message_text(
        "💬 User ko reply bhejo (text):\n\n/cancel - Cancel",
        parse_mode=ParseMode.HTML
    )
    return CHATS_REPLY

async def chats_reply_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    from bson import ObjectId
    rid = context.user_data.get("chat_reply_req_id")
    reply = update.message.text.strip()
    if not rid:
        await update.message.reply_text("Error. Open Chats again.")
        return ConversationHandler.END
    try:
        doc = db['movie_requests'].find_one({"_id": ObjectId(rid)})
    except Exception:
        doc = None
    if not doc:
        await update.message.reply_text("Request not found.")
        return ConversationHandler.END
    uid = doc.get("user_id")
    try:
        await context.bot.send_message(
            chat_id=uid,
            text=f"💬 <b>Developer reply:</b>\n\n{reply}",
            parse_mode=ParseMode.HTML
        )
        db['movie_requests'].update_one(
            {"_id": ObjectId(rid)},
            {"$set": {"status": "replied", "admin_reply": reply, "replied_at": datetime.utcnow()}}
        )
        await update.message.reply_text("✅ Reply user ko bhej diya. (Chats → Replied)")
    except Exception as e:
        await update.message.reply_text(f"❌ Fail: {e}")
    context.user_data.pop("chat_reply_req_id", None)
    return ConversationHandler.END

async def chats_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from datetime import datetime, timedelta
    uid = int(query.data.replace("chats_banuser_", ""))
    until = datetime.utcnow() + timedelta(hours=3)
    db['request_bans'].update_one(
        {"user_id": uid},
        {"$set": {"user_id": uid, "until": until, "banned_at": datetime.utcnow()}},
        upsert=True
    )
    await query.answer("User banned 3 hours", show_alert=True)
    try:
        await context.bot.send_message(
            chat_id=uid,
            text="🚫 You are temporarily banned from requesting movies (3 hours)."
        )
    except Exception:
        pass

async def chats_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🚫 User ID bhejo jise 3 hours ke liye request se ban karna hai:\n\n/cancel - Cancel",
        parse_mode=ParseMode.HTML
    )
    return CHATS_BAN_ID

async def chats_ban_id_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime, timedelta
    try:
        uid = int(update.message.text.strip())
    except Exception:
        await update.message.reply_text("Invalid user ID. Numbers only.")
        return CHATS_BAN_ID
    until = datetime.utcnow() + timedelta(hours=3)
    db['request_bans'].update_one(
        {"user_id": uid},
        {"$set": {"user_id": uid, "until": until, "banned_at": datetime.utcnow()}},
        upsert=True
    )
    await update.message.reply_text(f"✅ User <code>{uid}</code> banned for 3 hours.", parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    if await is_co_admin_only(user_id):
        await deny_co_admin_feature(update, context, "Admin Settings")
        return
    if query: await query.answer()
    
    config = await get_config()
    default_chat = config.get("default_publish_chat") or "Not Set"
    promo1 = config.get("promo_channel_1") or "Not Set"
    promo2 = config.get("promo_channel_2") or "Not Set"
    keyboard = [
        [InlineKeyboardButton("➕ Add Co-Admin", callback_data="admin_add_co_admin")],
        [InlineKeyboardButton("🚫 Remove Co-Admin", callback_data="admin_remove_co_admin")],
        [InlineKeyboardButton("👥 List Co-Admins", callback_data="admin_list_co_admin")],
        [InlineKeyboardButton(f"📍 Default Publish Chat: {default_chat}", callback_data="admin_set_default_chat")],
        [InlineKeyboardButton("📢 Promo Channels (Thank You)", callback_data="admin_promo_channels")],
        [InlineKeyboardButton("🔘 Post Buttons Text", callback_data="admin_post_buttons")],
        [InlineKeyboardButton("🌐 Bot Language", callback_data="admin_set_language")],
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

# ============================================
# ===     DEFAULT PUBLISH CHAT SETTING     ===
# ============================================
async def set_default_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = config.get("default_publish_chat") or "Not Set"
    text = (
        f"📍 <b>Default Publish Chat</b>\n\n"
        f"Current: <code>{current}</code>\n\n"
        f"Ab naya <b>Channel/Group Chat ID</b> ya <b>@username</b> bhejo.\n"
        f"(Example: <code>-1001234567890</code> ya <code>@mychannel</code>)\n\n"
        f"/skip - Clear default\n"
        f"/cancel - Cancel"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return DPC_GET_CHAT

async def set_default_chat_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.text.strip()
    try:
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$set": {"default_publish_chat": chat_id}},
            upsert=True
        )
        await update.message.reply_text(f"✅ Default Publish Chat set to:\n<code>{chat_id}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Default chat set error: {e}")
        await update.message.reply_text("❌ Error setting default chat.", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END

async def set_default_chat_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$unset": {"default_publish_chat": ""}}
        )
        await update.message.reply_text("✅ Default Publish Chat cleared.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END


# ============================================
# ===     PROMO CHANNELS + THANK YOU       ===
# ============================================

# ============================================
# ===     BOT LANGUAGE SETTING             ===
# ============================================
LANG_LABELS = {
    "hinglish": "Hinglish",
    "hindi": "हिंदी",
    "english": "English",
    "bengali": "বাংলা",
    "arabic": "العربية"
}


# ============================================
# ===     POST BUTTONS TEXT EDITOR         ===
# ============================================
async def post_buttons_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    t_backup = config.get("btn_text_backup") or "Backup"
    t_verify = config.get("btn_text_verify") or "How to Verify"
    t_donate = config.get("btn_text_donate") or "Donate"
    t_request = config.get("btn_text_request") or "Request a Movie"
    t_download = config.get("btn_text_download") or "⬇️ DOWNLOAD"
    verify_link = config.get("links", {}).get("verify") or "Not Set"
    request_link = config.get("links", {}).get("request") or "Not Set"
    has_video = "✅" if config.get("verify_video_id") else "❌"
    
    text = (
        f"🔘 <b>Post Buttons</b>\n\n"
        f"Layout:\n"
        f"<code>[ {t_backup} ] [ {t_verify} ]</code>\n"
        f"<code>[ {t_donate} ] [ {t_request} ]</code>\n"
        f"<code>[ {t_download} ]</code>\n\n"
        f"<b>How to Verify:</b> Video {has_video} | Link: <code>{verify_link}</code>\n"
        f"<b>Request Link:</b> <code>{request_link}</code>\n\n"
        f"Button text / links / video set karo."
    )
    def _on(flag, default=True):
        return "✅" if config.get(flag, default) else "❌"
    keyboard = [
        [InlineKeyboardButton(f"{_on('btn_show_backup')} Backup ON/OFF", callback_data="ptoggle_backup")],
        [InlineKeyboardButton(f"{_on('btn_show_verify')} Verify ON/OFF", callback_data="ptoggle_verify")],
        [InlineKeyboardButton(f"{_on('btn_show_donate')} Donate ON/OFF", callback_data="ptoggle_donate")],
        [InlineKeyboardButton(f"{_on('btn_show_request')} Request ON/OFF", callback_data="ptoggle_request")],
        [InlineKeyboardButton(f"{_on('btn_show_download')} Download ON/OFF", callback_data="ptoggle_download")],
        [InlineKeyboardButton(f"✏️ Backup: {t_backup[:15]}", callback_data="pbtn_backup")],
        [InlineKeyboardButton(f"✏️ How to Verify: {t_verify[:15]}", callback_data="pbtn_verify")],
        [InlineKeyboardButton(f"✏️ Donate: {t_donate[:15]}", callback_data="pbtn_donate")],
        [InlineKeyboardButton(f"✏️ Request: {t_request[:15]}", callback_data="pbtn_request")],
        [InlineKeyboardButton(f"✏️ Download: {t_download[:15]}", callback_data="pbtn_download")],
        [InlineKeyboardButton("✏️ Refresh Timer Button Text", callback_data="pbtn_refresh")],
        [InlineKeyboardButton("🔗 Set Verify Link", callback_data="admin_set_verify_link")],
        [InlineKeyboardButton("🎬 Set Verify How-To Video", callback_data="admin_set_verify_video")],
        [InlineKeyboardButton("🎬 Set Request Link", callback_data="admin_set_request_link")],
        [InlineKeyboardButton("↕️ Move Buttons Layout", callback_data="admin_btn_layout")],
        [InlineKeyboardButton("📞 Set Developer Contact (Co-Admin only)", callback_data="admin_set_dev_contact")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_admin_settings")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)



async def btn_layout_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current layout + move controls"""
    query = update.callback_query
    await query.answer()
    config = await get_config()
    layout = config.get("post_button_layout") or [
        ["backup", "verify"],
        ["donate", "request"],
        ["download"],
    ]
    # Flatten with positions
    names = {"backup": "Backup", "verify": "How to Verify", "donate": "Donate", "request": "Request", "download": "Download"}
    lines = ["↕️ <b>Button Layout</b>\n"]
    for ri, row in enumerate(layout):
        lines.append(f"<b>Row {ri+1}:</b> " + " | ".join(names.get(k, k) for k in row))
    lines.append("\nSelect button to move:")
    keyboard = []
    for ri, row in enumerate(layout):
        for ci, key in enumerate(row):
            keyboard.append([InlineKeyboardButton(
                f"📍 {names.get(key, key)} (R{ri+1})",
                callback_data=f"blayout_sel_{ri}_{ci}"
            )])
    keyboard.append([InlineKeyboardButton("🔄 Reset Default Layout", callback_data="blayout_reset")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_post_buttons")])
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def btn_layout_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")  # blayout_sel_r_c
    ri, ci = int(parts[2]), int(parts[3])
    context.user_data["blayout_ri"] = ri
    context.user_data["blayout_ci"] = ci
    config = await get_config()
    layout = config.get("post_button_layout") or [["backup", "verify"], ["donate", "request"], ["download"]]
    key = layout[ri][ci]
    names = {"backup": "Backup", "verify": "How to Verify", "donate": "Donate", "request": "Request", "download": "Download"}
    text = f"Moving: <b>{names.get(key, key)}</b>\n\nChoose action:"
    keyboard = [
        [InlineKeyboardButton("⬆️ Row Up", callback_data="blayout_act_up")],
        [InlineKeyboardButton("⬇️ Row Down", callback_data="blayout_act_down")],
        [InlineKeyboardButton("⬅️ Left", callback_data="blayout_act_left")],
        [InlineKeyboardButton("➡️ Right", callback_data="blayout_act_right")],
        [InlineKeyboardButton("🔀 New Row (alone)", callback_data="blayout_act_alone")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_btn_layout")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def btn_layout_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    act = query.data.replace("blayout_act_", "")
    config = await get_config()
    layout = [list(r) for r in (config.get("post_button_layout") or [["backup", "verify"], ["donate", "request"], ["download"]])]
    ri = context.user_data.get("blayout_ri", 0)
    ci = context.user_data.get("blayout_ci", 0)
    if ri >= len(layout) or ci >= len(layout[ri]):
        await btn_layout_menu(update, context)
        return
    key = layout[ri].pop(ci)
    if not layout[ri]:
        layout.pop(ri)
        if ri > 0:
            ri -= 1
    
    if act == "up":
        new_ri = max(0, ri - 1)
        if new_ri >= len(layout):
            layout.insert(0, [key])
        else:
            layout[new_ri].insert(min(ci, len(layout[new_ri])), key)
    elif act == "down":
        new_ri = min(len(layout), ri + 1)
        if new_ri >= len(layout):
            layout.append([key])
        else:
            layout[new_ri].insert(min(ci, len(layout[new_ri])), key)
    elif act == "left":
        # same row, earlier position
        if ri >= len(layout):
            layout.append([key])
        else:
            layout[ri].insert(max(0, ci - 1), key)
    elif act == "right":
        if ri >= len(layout):
            layout.append([key])
        else:
            layout[ri].insert(min(len(layout[ri]), ci + 1), key)
    elif act == "alone":
        # put on its own full-width row at same index
        layout.insert(min(ri + 1, len(layout)), [key])
    else:
        # fallback put back
        if ri < len(layout):
            layout[ri].insert(ci, key)
        else:
            layout.append([key])
    
    # clean empty rows
    layout = [r for r in layout if r]
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"post_button_layout": layout}}, upsert=True)
    await btn_layout_menu(update, context)

async def btn_layout_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Reset to default")
    default = [["backup", "verify"], ["donate", "request"], ["download"]]
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"post_button_layout": default}}, upsert=True)
    await btn_layout_menu(update, context)


async def post_btn_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key_map = {
        "ptoggle_backup": "btn_show_backup",
        "ptoggle_verify": "btn_show_verify",
        "ptoggle_donate": "btn_show_donate",
        "ptoggle_request": "btn_show_request",
        "ptoggle_download": "btn_show_download",
    }
    conf_key = key_map.get(query.data)
    if not conf_key:
        return
    config = await get_config()
    current = config.get(conf_key, True)
    config_collection.update_one({"_id": "bot_config"}, {"$set": {conf_key: not current}}, upsert=True)
    await post_buttons_menu(update, context)

async def set_dev_contact_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📞 <b>Developer Contact</b>\\n\\nTelegram username or link bhejo:\\n(Example: @username or https://t.me/username)\\n\\n/cancel - Cancel",
        parse_mode=ParseMode.HTML
    )
    return PBTN_GET_TEXT

async def post_btn_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # pbtn_backup / pbtn_verify / etc
    key_map = {
        "pbtn_backup": ("btn_text_backup", "Backup"),
        "pbtn_verify": ("btn_text_verify", "How to Verify"),
        "pbtn_donate": ("btn_text_donate", "Donate"),
        "pbtn_request": ("btn_text_request", "Request a Movie"),
        "pbtn_download": ("btn_text_download", "Download"),
        "pbtn_refresh": ("btn_text_refresh_timer", "Refresh Timer"),
    }
    conf_key, label = key_map.get(data, (None, None))
    if not conf_key:
        return ConversationHandler.END
    context.user_data['pbtn_key'] = conf_key
    await query.edit_message_text(
        f"✏️ <b>{label}</b> button ka naya text bhejo:\n\n/cancel - Cancel",
        parse_mode=ParseMode.HTML
    )
    return PBTN_GET_TEXT

async def post_btn_text_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.get('pbtn_key') or "developer_contact"
    text = update.message.text.strip()
    # If came from dev contact without pbtn_key
    if not context.user_data.get('pbtn_key') and key == "developer_contact":
        pass
    elif not context.user_data.get('pbtn_key'):
        # default from set_dev_contact_start
        key = "developer_contact"
    config_collection.update_one({"_id": "bot_config"}, {"$set": {key: text}}, upsert=True)
    await update.message.reply_text(f"✅ Saved:\n<code>{text}</code>", parse_mode=ParseMode.HTML)
    context.user_data.clear()
    return ConversationHandler.END

async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = config.get("bot_language", "hinglish")
    text = f"🌐 <b>Bot Language</b>\n\nCurrent: <b>{LANG_LABELS.get(current, current)}</b>\n\nSelect language (admin menus + key messages):"
    keyboard = [
        [InlineKeyboardButton(f"{'✅ ' if current=='hinglish' else ''}Hinglish", callback_data="lang_hinglish")],
        [InlineKeyboardButton(f"{'✅ ' if current=='hindi' else ''}हिंदी Hindi", callback_data="lang_hindi")],
        [InlineKeyboardButton(f"{'✅ ' if current=='english' else ''}English", callback_data="lang_english")],
        [InlineKeyboardButton(f"{'✅ ' if current=='bengali' else ''}বাংলা Bengali", callback_data="lang_bengali")],
        [InlineKeyboardButton(f"{'✅ ' if current=='arabic' else ''}العربية Arabic", callback_data="lang_arabic")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_admin_settings")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def language_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    config_collection.update_one(
        {"_id": "bot_config"},
        {"$set": {"bot_language": lang}},
        upsert=True
    )
    await query.edit_message_text(
        f"✅ Language set to <b>{LANG_LABELS.get(lang, lang)}</b>\n\nBot restart ke baad / full refresh se menus update honge.\nKey messages language ke hisaab se change honge.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_admin_settings")]])
    )

async def promo_channels_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    p1 = config.get("promo_channel_1") or "Not Set"
    p2 = config.get("promo_channel_2") or "Not Set"
    thank_msg = config.get("promo_thank_you_msg") or "🙏 Thank you for your time and consideration!"
    thank_secs = int(config.get("promo_thank_you_delete_seconds") or 120)
    text = (
        f"📢 <b>Promo Channels (After Download)</b>\n\n"
        f"Download complete hone ke baad user ko Thank You + 2 Join buttons.\n\n"
        f"<b>Channel 1:</b> <code>{p1}</code>\n"
        f"<b>Channel 2:</b> <code>{p2}</code>\n"
        f"<b>Message:</b> {thank_msg}\n"
        f"<b>Thank You delete timer:</b> {thank_secs}s\n\n"
        f"Links / timer set karo."
    )
    b1 = config.get("promo_btn1_text") or "Join Channel"
    b2 = config.get("promo_btn2_text") or "Join Channel 2"
    keyboard = [
        [InlineKeyboardButton("🔗 Set Channel 1 Link", callback_data="promo_set_1")],
        [InlineKeyboardButton("🔗 Set Channel 2 Link", callback_data="promo_set_2")],
        [InlineKeyboardButton(f"✏️ Button 1 Text: {b1[:20]}", callback_data="promo_set_btn1")],
        [InlineKeyboardButton(f"✏️ Button 2 Text: {b2[:20]}", callback_data="promo_set_btn2")],
        [InlineKeyboardButton("✏️ Edit Thank You Message", callback_data="promo_set_msg")],
        [InlineKeyboardButton(f"⏱️ Promo Delete Timer ({thank_secs}s)", callback_data="promo_set_timer")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu_admin_settings")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def promo_set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "promo_set_1":
        context.user_data['promo_setting'] = "promo_channel_1"
        text = "🔗 <b>Channel 1</b> ka link bhejo:\n(Example: https://t.me/mychannel)\n\n/skip - Clear\n/cancel - Cancel"
    elif data == "promo_set_2":
        context.user_data['promo_setting'] = "promo_channel_2"
        text = "🔗 <b>Channel 2</b> ka link bhejo:\n(Example: https://t.me/mychannel2)\n\n/skip - Clear\n/cancel - Cancel"
    elif data == "promo_set_btn1":
        context.user_data['promo_setting'] = "promo_btn1_text"
        text = "✏️ <b>Button 1</b> ka text bhejo:\n(Example: Join My Channel / Subscribe Now)\n\n/cancel - Cancel"
    elif data == "promo_set_btn2":
        context.user_data['promo_setting'] = "promo_btn2_text"
        text = "✏️ <b>Button 2</b> ka text bhejo:\n(Example: Join Channel 2 / More Content)\n\n/cancel - Cancel"
    elif data == "promo_set_timer":
        context.user_data['promo_setting'] = "promo_thank_you_delete_seconds"
        text = "⏱️ Promo message delete timer (seconds) bhejo:\nExample: <code>120</code> (2 min)\n\n/cancel - Cancel"
    else:
        context.user_data['promo_setting'] = "promo_thank_you_msg"
        text = "✏️ Thank You message bhejo:\n\n/cancel - Cancel"
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return PROMO_GET_VALUE

async def promo_set_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.get('promo_setting')
    value = update.message.text.strip()
    if not key:
        await update.message.reply_text("Error. /cancel and try again.")
        return ConversationHandler.END
    if key == "promo_thank_you_delete_seconds":
        try:
            value = int(value)
            if value < 10:
                await update.message.reply_text("Minimum 10 seconds.")
                return PROMO_GET_VALUE
        except Exception:
            await update.message.reply_text("Sirf number bhejo (seconds).")
            return PROMO_GET_VALUE
    if not key:
        await update.message.reply_text("Error. /cancel and try again.")
        return ConversationHandler.END
    try:
        config_collection.update_one(
            {"_id": "bot_config"},
            {"$set": {key: value}},
            upsert=True
        )
        await update.message.reply_text(f"✅ Saved!\n<code>{key}</code> = <code>{value}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    context.user_data.clear()
    return ConversationHandler.END

async def promo_set_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.get('promo_setting')
    if key and key != "promo_thank_you_msg":
        config_collection.update_one({"_id": "bot_config"}, {"$unset": {key: ""}})
        await update.message.reply_text(f"✅ {key} cleared.")
    context.user_data.clear()
    return ConversationHandler.END

async def send_promo_thank_you(bot, user_id: int):
    """Download ke baad thank you + join channel buttons + own delete timer"""
    try:
        config = config_collection.find_one({"_id": "bot_config"}) or {}
        msg = config.get("promo_thank_you_msg") or "🙏 <b>Thank you for your time and consideration!</b>"
        p1 = config.get("promo_channel_1")
        p2 = config.get("promo_channel_2")
        btn1_text = config.get("promo_btn1_text") or "📢 Join Channel"
        btn2_text = config.get("promo_btn2_text") or "📢 Join Channel 2"
        # Separate timer for thank you message (default 120s)
        thank_secs = int(config.get("promo_thank_you_delete_seconds") or 120)
        if thank_secs < 10:
            thank_secs = 10
        _h = thank_secs // 3600
        _m = (thank_secs % 3600) // 60
        _s = thank_secs % 60
        if _h > 0:
            time_str = f"{_h}h {_m}m {_s}s"
        elif _m > 0:
            time_str = f"{_m}m {_s}s"
        else:
            time_str = f"{_s}s"
        full_msg = f"{msg}\n\n⏳ <i>This message auto-deletes in <b>{time_str}</b></i>"
        
        from datetime import datetime, timedelta
        ty_deadline = datetime.utcnow() + timedelta(seconds=thank_secs)
        db['user_delete_timers'].update_one(
            {"user_id": user_id, "type": "thankyou"},
            {"$set": {"user_id": user_id, "type": "thankyou", "deadline": ty_deadline, "seconds": thank_secs}},
            upsert=True
        )
        
        keyboard = []
        row = []
        if p1:
            row.append(InlineKeyboardButton(btn1_text, url=p1))
        if p2:
            row.append(InlineKeyboardButton(btn2_text, url=p2))
        if row:
            keyboard.append(row)
        rtxt = config.get("btn_text_refresh_timer") or "🔄 Refresh Timer"
        keyboard.append([InlineKeyboardButton(rtxt, callback_data="thankyou_timer_refresh")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        try:
            sent = await bot.send_message(chat_id=user_id, text=full_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except BadRequest as e:
            logger.error(f"Promo HTML fail: {e}")
            import re as _re
            plain = _re.sub(r'<[^>]+>', '', full_msg or '')
            sent = await bot.send_message(chat_id=user_id, text=plain, reply_markup=reply_markup)
        track_dm_msg(user_id, sent.message_id)
        # Promo time khatam = SAARA bot DM clean (files + status + promo)
        try:
            await schedule_clear_user_dm(bot, user_id, thank_secs, extra_ids=[sent.message_id])
        except Exception as e:
            logger.error(f"Thank you clear schedule failed: {e}")
            try:
                asyncio.create_task(delete_message_later(
                    bot=bot, chat_id=user_id, message_id=sent.message_id, seconds=thank_secs
                ))
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Promo thank you send failed: {e}")


# NAYA (v32): Update Photo Sub-Menu
async def update_photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🖼️ Update Series/Season Photo", callback_data="admin_update_photo_content")],
        [InlineKeyboardButton("🖼️ Set User Menu Photo", callback_data="admin_set_menu_photo")],
        [InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_update_photo")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# NAYA (v34): User Statistics
async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    loading_text = await format_message(context, "admin_stats_loading")
    await query.edit_message_text(loading_text, parse_mode=ParseMode.HTML)
    
    try:
        # Total users
        total_users = users_collection.count_documents({})
        
        # Top 10 users
        top_users_cursor = users_collection.find(
            {"interaction_count": {"$gt": 0}}
        ).sort("interaction_count", DESCENDING).limit(10)
        
        top_users_list = []
        for i, user in enumerate(top_users_cursor):
            user_id = user["_id"]
            count = user["interaction_count"]
            name = user.get("full_name") or user.get("first_name", f"User {user_id}")
            # HTML escape user name
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

# --- User Handlers ---
async def handle_deep_link_donate(user: User, context: ContextTypes.DEFAULT_TYPE):
    """Deep link se /start=donate ko handle karega"""
    logger.info(f"User {user.id} ne Donate deep link use kiya.")
    # NAYA v34: User interaction track karo
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
        if "blocked" in str(e):
            logger.warning(f"User {user.id} ne bot ko block kiya hua hai.")


async def handle_deep_link_verify(user: User, context: ContextTypes.DEFAULT_TYPE):
    """How to Verify - video / link / not set"""
    logger.info(f"User {user.id} opened How to Verify")
    config = await get_config()
    video_id = config.get("verify_video_id")
    verify_url = config.get("links", {}).get("verify")
    caption = config.get("verify_post_caption") or "✅ <b>How to Verify / Download</b>\n\nFollow the guide below."
    
    markup = None
    if verify_url:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(config.get("btn_text_verify") or "How to Verify", url=verify_url)]])
    
    if video_id:
        try:
            await context.bot.send_video(
                chat_id=user.id,
                video=video_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=markup
            )
            return
        except Exception as e:
            logger.error(f"Verify video send failed: {e}")
    
    if verify_url:
        await context.bot.send_message(
            chat_id=user.id,
            text=caption + f"\n\n👉 <a href=\"{verify_url}\">Open Guide</a>",
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
            disable_web_page_preview=False
        )
        return
    
    await context.bot.send_message(
        chat_id=user.id,
        text="⚠️ <b>Admin has not set any verification file.</b>\n\nPlease contact admin or try again later.",
        parse_mode=ParseMode.HTML
    )


async def handle_deep_link_request(user: User, context: ContextTypes.DEFAULT_TYPE):
    """Deep link Request a Movie -> same as /request start"""
    allowed, remaining, limit_msg = await check_request_limit(user.id)
    if not allowed:
        msg = limit_msg
        try:
            if not ("Wait" in limit_msg or "wait" in limit_msg or "Cooldown" in limit_msg or "banned" in limit_msg):
                msg = await format_message(context, "user_request_limit")
        except Exception:
            msg = limit_msg
        await send_request_limit_msg(user, context, msg, user_id=user.id)
        return
    try:
        text = await format_message(context, "user_request_prompt", {"remaining": str(remaining)})
        text = sanitize_telegram_html(text or "")
    except Exception as e:
        logger.error(f"request prompt format: {e}")
        text = f"🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining today: <b>{remaining}/3</b>\n\n/cancel - Cancel"
    try:
        sent = await context.bot.send_message(
            chat_id=user.id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Type request below", callback_data="noop")]])
        )
        track_dm_msg(user.id, sent.message_id)
    except BadRequest as e:
        logger.error(f"request prompt HTML fail: {e}")
        import re as _re
        plain = _re.sub(r'<[^>]+>', '', text or '')
        sent = await context.bot.send_message(
            chat_id=user.id,
            text=plain or "Request a Movie — naam bhejo /cancel se cancel.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Type request below", callback_data="noop")]])
        )
        track_dm_msg(user.id, sent.message_id)
    context.user_data["awaiting_movie_request"] = True
    context.user_data["request_mode"] = True

async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /request - user movie request (3/day) """
    user = update.effective_user
    allowed, remaining, limit_msg = await check_request_limit(user.id)
    if not allowed:
        msg = limit_msg
        try:
            # Prefer live timer message over static
            if "Wait" in limit_msg or "wait" in limit_msg or "Cooldown" in limit_msg or "banned" in limit_msg:
                msg = limit_msg
            else:
                msg = await format_message(context, "user_request_limit")
        except Exception:
            msg = limit_msg
        await send_request_limit_msg(update, context, msg)
        return ConversationHandler.END
    try:
        text = await format_message(context, "user_request_prompt", {"remaining": str(remaining)})
        text = sanitize_telegram_html(text or "")
    except Exception as e:
        logger.error(f"request_command prompt: {e}")
        text = f"🎬 <b>Request a Movie</b>\n\nApni movie/series ka naam likh ke bhejo.\n\nRemaining: <b>{remaining}/3</b>"
    try:
        sent = await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        track_dm_msg(user.id, sent.message_id)
    except BadRequest as e:
        logger.error(f"request_command HTML fail: {e}")
        import re as _re
        plain = _re.sub(r'<[^>]+>', '', text or '')
        sent = await update.message.reply_text(plain or "Request a Movie — naam bhejo.")
        track_dm_msg(user.id, sent.message_id)
    context.user_data["awaiting_movie_request"] = True
    return REQ_GET_TEXT

async def request_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ne request text bheja"""
    if not context.user_data.get("awaiting_movie_request"):
        return ConversationHandler.END
    user = update.effective_user
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Please send movie/series name.")
        return REQ_GET_TEXT
    
    allowed, remaining, limit_msg = await check_request_limit(user.id)
    if not allowed:
        context.user_data["awaiting_movie_request"] = False
        msg = limit_msg
        try:
            if not ("Wait" in limit_msg or "Cooldown" in limit_msg or "banned" in limit_msg):
                msg = await format_message(context, "user_request_limit")
        except Exception:
            msg = limit_msg
        await send_request_limit_msg(update, context, msg)
        return ConversationHandler.END
    
    from datetime import datetime
    await log_movie_request(user.id)
    context.user_data["awaiting_movie_request"] = False
    
    uname = user.username or "no_username"
    name = user.full_name or user.first_name or "User"
    
    # Save to DB for Admin Chats panel
    req_doc = {
        "user_id": user.id,
        "name": name,
        "username": uname,
        "text": text,
        "status": "pending",  # pending | replied
        "admin_reply": None,
        "created_at": datetime.utcnow(),
        "replied_at": None,
    }
    ins = db['movie_requests'].insert_one(req_doc)
    req_id = str(ins.inserted_id)
    
    # Auto reply to user
    try:
        ok_msg = await format_message(context, "user_request_received")
    except Exception:
        ok_msg = "✅ <b>Request received!</b>\n\nDeveloper will update it shortly. Keep patience."
    await update.message.reply_text(ok_msg, parse_mode=ParseMode.HTML)
    
    # Light notify admin (once) - full list in Admin Settings → Chats
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📩 <b>New request</b> from {name}\n"
                f"<code>{text[:200]}</code>\n\n"
                f"Open <b>Admin Settings → Chats</b> to view / reply / ban."
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Admin notify failed: {e}")
    
    return ConversationHandler.END


async def request_text_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deep link / post button se request mode - conversation ke bahar"""
    # IMPORTANT: post generator short-link step ko mat churao
    if not context.user_data.get("awaiting_movie_request") and not context.user_data.get("request_mode"):
        return
    # Agar post gen short link state active lage (original link set + caption raw) to skip
    if context.user_data.get("original_download_url") and context.user_data.get("post_caption_raw") is not None:
        if not context.user_data.get("awaiting_movie_request"):
            return
    return await request_receive(update, context)

async def request_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_movie_request"] = False
    try:
        msg = await format_message(context, "user_request_cancelled")
    except Exception:
        msg = "❌ Request cancelled."
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END

async def admin_reply_to_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin replies to a request message -> forward reply to user"""
    if not update.message or not update.message.reply_to_message:
        return
    user = update.effective_user
    if user.id != ADMIN_ID:
        # co-admin optional? only main admin for now
        if not await is_main_admin(user.id):
            return
    
    reply_to = update.message.reply_to_message
    doc = db['request_reply_map'].find_one({"admin_msg_id": reply_to.message_id})
    if not doc:
        return  # not a request message
    
    target_user = doc.get("user_id")
    if not target_user:
        return
    
    reply_text = update.message.text or update.message.caption or ""
    try:
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=target_user,
                photo=update.message.photo[-1].file_id,
                caption=f"💬 <b>Developer reply:</b>\n\n{reply_text}" if reply_text else "💬 Developer sent a photo.",
                parse_mode=ParseMode.HTML
            )
        elif update.message.video:
            await context.bot.send_video(
                chat_id=target_user,
                video=update.message.video.file_id,
                caption=f"💬 <b>Developer reply:</b>\n\n{reply_text}" if reply_text else "",
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=target_user,
                text=f"💬 <b>Developer reply:</b>\n\n{reply_text}",
                parse_mode=ParseMode.HTML
            )
        await update.message.reply_text("✅ Reply sent to user.")
    except Exception as e:
        logger.error(f"Admin reply to user failed: {e}")
        await update.message.reply_text(f"❌ Failed to send: {e}")


async def handle_deep_link_download(user: User, context: ContextTypes.DEFAULT_TYPE, payload: str):
    """Deep link se /start=dl... ko handle karega"""
    logger.info(f"User {user.id} ne Download deep link use kiya: {payload}")
    
    # NAYA v34: User interaction track karo
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart /start command"""
    user = update.effective_user
    user_id, full_name = user.id, user.full_name # NAYA: Full name
    logger.info(f"User {user_id} ({full_name}) ne /start dabaya.")
    
    user_data = users_collection.find_one({"_id": user_id})
    if not user_data:
        users_collection.insert_one({
            "_id": user_id, 
            "first_name": user.first_name, 
            "full_name": full_name, 
            "username": user.username,
            "interaction_count": 1 # NAYA v34
        })
        logger.info(f"Naya user database me add kiya: {user_id}")
    else:
        users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {"first_name": user.first_name, "full_name": full_name, "username": user.username},
                "$inc": {"interaction_count": 1} # NAYA v34
            }
        )
    
    args = context.args
    if args:
        payload = " ".join(args) 
        logger.info(f"User {user_id} ne deep link use kiya: {payload}")
        
        payload_l = (payload or "").strip().lower()
        if payload.startswith("dl"):
            await handle_deep_link_download(user, context, payload)
            return
            
        elif payload_l == "donate":
            await handle_deep_link_donate(user, context)
            return
        
        elif payload_l == "verify":
            await handle_deep_link_verify(user, context)
            return
        
        elif payload_l == "request" or payload_l.startswith("request"):
            await handle_deep_link_request(user, context)
            return
    
    logger.info("Koi deep link nahi. Sirf welcome message bhej raha hoon.")
    if await is_co_admin(user_id):
        text = await format_message(context, "user_welcome_admin")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
            text = await format_message(context, "user_welcome_basic", {
                "full_name": full_name,
                "first_name": user.first_name # Compatibility ke liye add kiya
            }) # NAYA
            # Ensure the message uses /user, even if DB message is old
            text = text.replace("/subscription", "/user") 
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    
async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    """User ka main menu (/user) dikhayega, photo ke saath (agar set ho)"""
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
        "first_name": user.first_name # Compatibility
    })

    menu_photo_id = config.get("user_menu_photo_id")

    if from_callback:
        query = update.callback_query
        await query.answer()

        try:
            if menu_photo_id:
                # Admin ne photo set kiya hai
                if query.message.photo:
                    # Pehle se photo hai, caption edit karo
                    await query.edit_message_caption(caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    # Pehle text tha, delete karke photo bhejo
                    await query.message.delete()
                    await context.bot.send_photo(chat_id=user_id, photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                # Admin ne koi photo set nahi kiya (default)
                if query.message.photo:
                    # Pehle photo tha, delete karke text bhejo
                    await query.message.delete()
                    await context.bot.send_message(chat_id=user_id, text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    # Pehle bhi text tha, edit karo
                    await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Menu edit/reply nahi kar paya: {e}. Naya message bhej raha hoon.")
            try:
                # Fallback: Agar kuch bhi fail ho, naya message bhejo
                if menu_photo_id:
                    await context.bot.send_photo(chat_id=user_id, photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(chat_id=user_id, text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except Exception as e2:
                logger.error(f"Menu command (callback) me critical error: {e2}")
    else:
        # Jab user ne /user command type kiya
        try:
            if menu_photo_id:
                await update.message.reply_photo(photo=menu_photo_id, caption=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(text=menu_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Show user menu me error: {e}")

async def user_show_donate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/menu se Donate button ko handle karega (DM bhejega)"""
    query = update.callback_query
    # NAYA v34: User interaction track karo
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


# --- Admin Panel (v34 UPDATE) ---
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    """Admin panel ka main menu"""
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
        # Co-admin: no Delete, no Admin Settings, no Bot Messages
        keyboard = [
            [InlineKeyboardButton("➕ Add Content", callback_data="admin_menu_add_content")],
            [InlineKeyboardButton("✏️ Edit Content", callback_data="admin_menu_edit_content")], 
            [InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen")],
            [
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link") 
            ]
        ]
        admin_menu_text = await format_message(context, "admin_panel_co")
    
    else:
        # Main Admin Menu (NAYA v34 LAYOUT)
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
                InlineKeyboardButton("⏱️ Auto-Delete Time", callback_data="admin_menu_auto_delete") 
            ],
            [
                InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo"),
                InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link") 
            ],
            [
                # NAYA LAYOUT (2x2)
                InlineKeyboardButton("🎨 Bot Appearance", callback_data="admin_menu_appearance"),
                InlineKeyboardButton("📊 User Statistics", callback_data="admin_show_stats") # NAYA
            ],
             # NAYA LAYOUT (1x1)
            [InlineKeyboardButton("⚙ Bot Messages", callback_data="admin_menu_messages")],
             # NAYA LAYOUT (1x1)
            [InlineKeyboardButton("🛠️ Admin Settings", callback_data="admin_menu_admin_settings")],
            [InlineKeyboardButton("💬 Chats (Requests)", callback_data="admin_chats_menu")]
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

# --- User Download Handler (CallbackQuery) (v34 STATS UPDATE) ---
async def download_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback data 'dl' se shuru hone wale sabhi buttons ko handle karega.
    """
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    
    # NAYA v34: User interaction track karo
    await increment_user_interaction(user_id)
    
    config = await get_config() 
    
    is_deep_link = not hasattr(query.message, 'edit_message_caption')
    is_in_dm = False 
    
    checking_msg_id = None
    
    try:
        # Step 1: Click ko acknowledge karo
        if not is_deep_link:
            is_in_dm = query.message.chat.type == 'private'
            if not is_in_dm:
                alert_msg = await format_message(context, "user_dl_dm_alert")
                # Font-formatted text alert me nahi dikh sakta, isliye <f> tags remove karo
                alert_msg_plain = re.sub(r'<f>(.*?)</f>', r'\1', alert_msg, flags=re.DOTALL)
                await query.answer(alert_msg_plain, show_alert=True)
            else:
                await query.answer()
        
        # Step 2: "Fetching..." message bhejo
        try:
            checking_text = await format_message(context, "user_dl_fetching")
            sent_msg = await context.bot.send_message(chat_id=user_id, text=checking_text, parse_mode=ParseMode.HTML, read_timeout=10, write_timeout=10)
            checking_msg_id = sent_msg.message_id
        except Exception as e:
            logger.error(f"User {user_id} ko 'Fetching...' message nahi bhej paya. Shayad bot block hai? Error: {e}")
            if not is_deep_link and not is_in_dm:
                await query.answer("❌ Error! Bot ko DM mein /start karke unblock karein.", show_alert=True)
            return 

        parts = query.data.split('__')
        
        anime_key = parts[0]
        if anime_key.startswith("dl_"):
            anime_key = anime_key.replace("dl_", "") 
        elif anime_key.startswith("dl"):
            anime_key = anime_key.replace("dl", "")  
            
        season_name = parts[1] if len(parts) > 1 else None
        ep_num = parts[2] if len(parts) > 2 else None
        
        anime_doc = None
        anime_key = anime_key.strip()
        logger.info(f"Download lookup key: '{anime_key}'")
        
        # Try ObjectId
        try:
            if len(anime_key) == 24:
                anime_doc = animes_collection.find_one({"_id": ObjectId(anime_key)})
        except Exception as e:
            logger.warning(f"ObjectId lookup failed for '{anime_key}': {e}")
        
        # Try exact name
        if not anime_doc:
            anime_doc = animes_collection.find_one({"name": anime_key})
        
        # Try case-insensitive name
        if not anime_doc:
            anime_doc = animes_collection.find_one({"name": {"$regex": f"^{anime_key}$", "$options": "i"}})
        
        if not anime_doc:
            logger.error(f"Content '{anime_key}' na ID se mila na Name se.")
            msg = await format_message(context, "user_dl_anime_not_found")
            await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
            
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            return
            
        anime_name = anime_doc['name'] 
        anime_id_str = str(anime_doc['_id']) 
        
        delete_time = config.get("delete_seconds", 300) 

        # Case 3: Episode click hua hai -> Saare Files Bhejo
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

            qualities_dict = anime_doc.get("seasons", {}).get(season_name, {}).get(ep_num, {})
            if not qualities_dict:
                msg = await format_message(context, "user_dl_episodes_not_found")
                await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            # NAYA v33: Thumbnail ke liye Poster Get karo
            season_data = anime_doc.get("seasons", {}).get(season_name, {})
            poster_to_use = season_data.get("_poster_id") or anime_doc.get("poster_id")
            
            msg = await format_message(context, "user_dl_sending_files", {
                "anime_name": anime_name,
                "season_name": season_name,
                "ep_num": ep_num
            })
            
            sent_msg = await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
            msg_to_delete_id = sent_msg.message_id
            
            QUALITY_ORDER = ['480p', '720p', '1080p', '4K']
            available_qualities = qualities_dict.keys()
            sorted_q_list = [q for q in QUALITY_ORDER if q in available_qualities]
            extra_q = [q for q in available_qualities if q not in sorted_q_list]
            sorted_q_list.extend(extra_q)
            
            # Human readable remaining delete time
            _h = delete_time // 3600
            _m = (delete_time % 3600) // 60
            _s = delete_time % 60
            if _h > 0:
                time_str = f"{_h}h {_m}m {_s}s"
            elif _m > 0:
                time_str = f"{_m}m {_s}s"
            else:
                time_str = f"{_s}s"
            delete_minutes = max(1, delete_time // 60)
            try:
                warning_template = await format_message(context, "file_warning", {
                    "minutes": str(delete_minutes),
                    "time": time_str,
                    "seconds": str(delete_time),
                })
            except Exception:
                warning_template = f"⚠️ <b>Auto-delete in {time_str}</b>"
            # Remaining sirf neeche status message pe dikhega — file caption pe static Remaining mat lagao
            
            file_msg_ids = []  # for live remaining refresh on the file posts themselves
            for quality in sorted_q_list:
                file_id = qualities_dict.get(quality)
                if not file_id: continue
                
                sent_message = None 
                try:
                    # NAYA: Caption ko font ke saath format karo
                    caption_base = "🎬 <b>{anime_name}</b>\nS{season_name} - E{ep_num} ({quality})\n\n{warning_msg}"
                    
                    # FIX v32: Variables pehle replace karo
                    caption_with_vars = caption_base.format(
                        anime_name=anime_name,
                        season_name=season_name,
                        ep_num=ep_num,
                        quality=quality,
                        warning_msg=warning_template # Yeh pehle se formatted hai
                    )
                    
                    # File captions hamesha default font me honge
                    font_settings = {"font": "default", "style": "normal"}
                    caption = await apply_font_formatting(caption_with_vars, font_settings)

                    sent_message = await context.bot.send_video(
                        chat_id=user_id, 
                        video=file_id, 
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        thumbnail=poster_to_use  # NAYA v33: Thumbnail add karo
                    )
                except Exception as e:
                    logger.error(f"User {user_id} ko file bhejte waqt error: {e}")
                    error_msg_key = "user_dl_blocked_error" if "blocked" in str(e) else "user_dl_file_error"
                    msg = await format_message(context, error_msg_key, {"quality": quality})
                    await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML) 
                
                if sent_message:
                    file_msg_ids.append(sent_message.message_id)
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
            
            # Timer status message (refreshable) + store file msg ids for live Remaining on files
            try:
                from datetime import datetime, timedelta
                deadline = datetime.utcnow() + timedelta(seconds=delete_time)
                db['user_delete_timers'].update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "user_id": user_id,
                        "deadline": deadline,
                        "seconds": delete_time,
                        "file_msg_ids": file_msg_ids,
                        "anime_name": anime_name,
                        "season_name": season_name,
                        "ep_num": ep_num,
                    }},
                    upsert=True
                )
                _h, _m, _s = delete_time // 3600, (delete_time % 3600) // 60, delete_time % 60
                tstr = f"{_h}h {_m}m {_s}s" if _h else (f"{_m}m {_s}s" if _m else f"{_s}s")
                rtxt = (config_collection.find_one({"_id": "bot_config"}) or {}).get("btn_text_refresh_timer") or "🔄 Refresh Timer"
                timer_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏳ <b>Files auto-delete in:</b> <code>{tstr}</code>\n\nRefresh dabake remaining time dekho.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(rtxt, callback_data="file_timer_refresh")]])
                )
                asyncio.create_task(delete_message_later(
                    bot=context.bot, chat_id=user_id, message_id=timer_msg.message_id, seconds=delete_time
                ))
            except Exception as e:
                logger.error(f"Timer status msg failed: {e}")
            
            # Thank you + promo channels
            # Track all download-session messages for bulk clean on promo timeout
            try:
                for _mid in (file_msg_ids or []):
                    track_dm_msg(user_id, _mid)
                if msg_to_delete_id:
                    track_dm_msg(user_id, msg_to_delete_id)
                if locals().get("timer_msg") is not None:
                    track_dm_msg(user_id, timer_msg.message_id)
            except Exception as _te:
                logger.debug(f"track before promo: {_te}")
            await send_promo_thank_you(context.bot, user_id)
            return 
            
        sent_selection_message = None 

        # Case 2: Season click hua hai -> Episode Bhejo
        if season_name:
            episodes = anime_doc.get("seasons", {}).get(season_name, {})
            
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
            buttons = [InlineKeyboardButton(f"Episode {ep}", callback_data=f"dl{anime_id_str}__{season_name}__{ep}") for ep in sorted_eps] 
            keyboard = build_grid_keyboard(buttons, 2)
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"dl{anime_id_str}")]) 
            
            msg = await format_message(context, "user_dl_select_episode", {
                "anime_name": anime_name,
                "season_name": season_name
            })

            season_poster_id = anime_doc.get("seasons", {}).get(season_name, {}).get("_poster_id")
            poster_to_use = season_poster_id or anime_doc['poster_id'] 
            
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
            
        # Case 1: Sirf content click hua hai
        content_type = anime_doc.get("type", "series")  # default series for old data
        
        # === MOVIE: direct qualities ===
        if content_type == "movie":
            if checking_msg_id:
                try: await context.bot.delete_message(user_id, checking_msg_id)
                except Exception: pass
            
            qualities_dict = anime_doc.get("qualities", {})
            if not qualities_dict:
                msg = "❌ Is movie ke liye koi quality available nahi hai."
                await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
                return
            
            QUALITY_ORDER = ['480p', '720p', '1080p', '4K']
            available_qualities = list(qualities_dict.keys())
            sorted_q_list = [q for q in QUALITY_ORDER if q in available_qualities]
            extra_q = [q for q in available_qualities if q not in sorted_q_list]
            sorted_q_list.extend(extra_q)
            
            # Human readable remaining delete time
            _h = delete_time // 3600
            _m = (delete_time % 3600) // 60
            _s = delete_time % 60
            if _h > 0:
                time_str = f"{_h}h {_m}m {_s}s"
            elif _m > 0:
                time_str = f"{_m}m {_s}s"
            else:
                time_str = f"{_s}s"
            delete_minutes = max(1, delete_time // 60)
            try:
                warning_template = await format_message(context, "file_warning", {
                    "minutes": str(delete_minutes),
                    "time": time_str,
                    "seconds": str(delete_time),
                })
            except Exception:
                warning_template = f"⚠️ <b>Auto-delete in {time_str}</b>"
            # Remaining sirf neeche status message pe dikhega — file caption pe static Remaining mat lagao
            
            msg = f"🎬 <b>{anime_name}</b>\n\nQuality select karein ya files bhej raha hoon..."
            sent_msg = await context.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML)
            msg_to_delete_id = sent_msg.message_id
            
            poster_to_use = anime_doc.get("poster_id")
            
            file_msg_ids = []
            for quality in sorted_q_list:
                file_id = qualities_dict.get(quality)
                if not file_id: continue
                try:
                    caption_base = "🎬 <b>{anime_name}</b>\n({quality})\n\n{warning_msg}"
                    caption_with_vars = caption_base.format(
                        anime_name=anime_name,
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
                    if sent_message:
                        file_msg_ids.append(sent_message.message_id)
                        asyncio.create_task(delete_message_later(
                            bot=context.bot,
                            chat_id=user_id,
                            message_id=sent_message.message_id,
                            seconds=delete_time
                        ))
                except Exception as e:
                    logger.error(f"Movie file send error: {e}")
                    await context.bot.send_message(user_id, f"❌ {quality} bhejne me error.", parse_mode=ParseMode.HTML)
            
            if msg_to_delete_id:
                try:
                    asyncio.create_task(delete_message_later(
                        bot=context.bot,
                        chat_id=user_id,
                        message_id=msg_to_delete_id,
                        seconds=delete_time
                    ))
                except: pass
            
            # Timer status message (refreshable) + store file msg ids
            try:
                from datetime import datetime, timedelta
                deadline = datetime.utcnow() + timedelta(seconds=delete_time)
                db['user_delete_timers'].update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "user_id": user_id,
                        "deadline": deadline,
                        "seconds": delete_time,
                        "file_msg_ids": file_msg_ids,
                        "anime_name": anime_name,
                    }},
                    upsert=True
                )
                _h, _m, _s = delete_time // 3600, (delete_time % 3600) // 60, delete_time % 60
                tstr = f"{_h}h {_m}m {_s}s" if _h else (f"{_m}m {_s}s" if _m else f"{_s}s")
                rtxt = (config_collection.find_one({"_id": "bot_config"}) or {}).get("btn_text_refresh_timer") or "🔄 Refresh Timer"
                timer_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏳ <b>Files auto-delete in:</b> <code>{tstr}</code>\n\nRefresh dabake remaining time dekho.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(rtxt, callback_data="file_timer_refresh")]])
                )
                asyncio.create_task(delete_message_later(
                    bot=context.bot, chat_id=user_id, message_id=timer_msg.message_id, seconds=delete_time
                ))
            except Exception as e:
                logger.error(f"Timer status msg failed: {e}")
            
            # Thank you + promo channels
            # Track all download-session messages for bulk clean on promo timeout
            try:
                for _mid in (file_msg_ids or []):
                    track_dm_msg(user_id, _mid)
                if msg_to_delete_id:
                    track_dm_msg(user_id, msg_to_delete_id)
                if locals().get("timer_msg") is not None:
                    track_dm_msg(user_id, timer_msg.message_id)
            except Exception as _te:
                logger.debug(f"track before promo: {_te}")
            await send_promo_thank_you(context.bot, user_id)
            return
        
        # === SERIES: Season list ===
        seasons = anime_doc.get("seasons", {})
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
        buttons = [InlineKeyboardButton(f"Season {s}", callback_data=f"dl{anime_id_str}__{s}") for s in sorted_seasons] 
        keyboard = build_grid_keyboard(buttons, 1) 
        keyboard.append([InlineKeyboardButton("⬅️ Back to Bot Menu", callback_data="user_back_menu")])
        
        msg = await format_message(context, "user_dl_select_season", {"anime_name": anime_name})

        if checking_msg_id:
            try: await context.bot.delete_message(user_id, checking_msg_id)
            except Exception: pass
            
        if is_deep_link:
            sent_selection_message = await context.bot.send_photo(
                chat_id=user_id, 
                photo=anime_doc['poster_id'], 
                caption=msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        else: 
            if not query.message.photo:
                await query.message.delete() 
                sent_selection_message = await context.bot.send_photo(
                    chat_id=user_id,
                    photo=anime_doc['poster_id'], 
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
        

# --- Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error} \nUpdate: {update}", exc_info=True)

# ============================================
# ===    NAYA WEBHOOK AUR THREADING SETUP    ===
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
        # Use httpx for sync request in async thread setup
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

# --- NAYA Main Bot Function (FINAL v34) ---
def main():
    global bot_app
    PORT = int(os.environ.get("PORT", 8080))
    
    # NAYA: Default ParseMode set karo
    my_defaults = Defaults(parse_mode=ParseMode.HTML)
    bot_app = Application.builder().token(BOT_TOKEN).defaults(my_defaults).build()
    
    # --- Saare Handlers ---
    
    global_cancel_handler = CommandHandler("cancel", cancel)
    # NAYA: Add Episode ke liye special cancel handler
    add_ep_cancel_handler = CommandHandler("cancel", cancel_add_episode)
    add_season_cancel_handler = CommandHandler("cancel", cancel_add_season)
    
    global_fallbacks = [
        CommandHandler("start", cancel),
        CommandHandler("menu", cancel),
        CommandHandler("admin", cancel),
        global_cancel_handler 
    ]
    admin_menu_fallback = [CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$"), global_cancel_handler]
    add_content_fallback = [CallbackQueryHandler(back_to_add_content_menu, pattern="^back_to_add_content$"), global_cancel_handler]
    add_season_fallback = [CallbackQueryHandler(back_to_add_content_menu, pattern="^back_to_add_content$"), add_season_cancel_handler]
    add_episode_fallback = [CallbackQueryHandler(back_to_add_content_menu, pattern="^back_to_add_content$"), add_ep_cancel_handler]
    
    manage_fallback = [CallbackQueryHandler(back_to_manage_menu, pattern="^back_to_manage$"), global_cancel_handler]
    edit_fallback = [CallbackQueryHandler(back_to_edit_menu, pattern="^back_to_edit_menu$"), global_cancel_handler] 
    sub_settings_fallback = [CallbackQueryHandler(back_to_sub_settings_menu, pattern="^back_to_sub_settings$"), global_cancel_handler]
    donate_settings_fallback = [CallbackQueryHandler(back_to_donate_settings_menu, pattern="^back_to_donate_settings$"), global_cancel_handler]
    links_fallback = [CallbackQueryHandler(back_to_links_menu, pattern="^back_to_links$"), global_cancel_handler]
    user_menu_fallback = [CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"), global_cancel_handler]
    messages_fallback = [CallbackQueryHandler(back_to_messages_menu, pattern="^admin_menu_messages$"), global_cancel_handler]
    admin_settings_fallback = [CallbackQueryHandler(back_to_admin_settings_menu, pattern="^back_to_admin_settings$"), global_cancel_handler]
    gen_link_fallback = [CallbackQueryHandler(gen_link_menu, pattern="^admin_gen_link$"), global_cancel_handler]
    appearance_fallback = [CallbackQueryHandler(back_to_appearance_menu, pattern="^back_to_appearance$"), global_cancel_handler]
    update_photo_fallback = [CallbackQueryHandler(back_to_update_photo_menu, pattern="^back_to_update_photo_menu$"), global_cancel_handler]


    add_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_anime_start, pattern="^admin_add_anime$")], 
        states={
            A_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime_name)], 
            A_GET_POSTER: [MessageHandler(filters.PHOTO, get_anime_poster)], 
            A_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_anime_desc), CommandHandler("skip", skip_anime_desc)], 
            A_CONFIRM: [CallbackQueryHandler(save_anime_details, pattern="^save_anime$")]
        }, 
        fallbacks=global_fallbacks + add_content_fallback,
        allow_reentry=True 
    )
    
    # NAYA: Add Movie Conversation
    add_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_movie_start, pattern="^admin_add_movie$")],
        states={
            M_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_name)],
            M_GET_POSTER: [MessageHandler(filters.PHOTO, get_movie_poster)],
            M_GET_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_desc),
                CommandHandler("skip", skip_movie_desc)
            ],
            M_GET_480P: [
                MessageHandler(filters.ALL & ~filters.COMMAND, get_movie_480p),
                CommandHandler("skip", skip_movie_480p)
            ],
            M_GET_720P: [
                MessageHandler(filters.ALL & ~filters.COMMAND, get_movie_720p),
                CommandHandler("skip", skip_movie_720p)
            ],
            M_GET_1080P: [
                MessageHandler(filters.ALL & ~filters.COMMAND, get_movie_1080p),
                CommandHandler("skip", skip_movie_1080p)
            ],
            M_GET_4K: [
                MessageHandler(filters.ALL & ~filters.COMMAND, get_movie_4k),
                CommandHandler("skip", skip_movie_4k)
            ],
            M_CONFIRM: [CallbackQueryHandler(save_movie_details, pattern="^save_movie$")]
        },
        fallbacks=global_fallbacks + add_content_fallback,
        allow_reentry=True
    )
    
    add_season_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_season_start, pattern="^admin_add_season$")], 
        states={
            S_GET_ANIME: [
                CallbackQueryHandler(add_season_show_anime_list, pattern="^addseason_page_"),
                CallbackQueryHandler(get_anime_for_season, pattern="^season_anime_")
            ], 
            S_GET_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_season_number)], 
            S_GET_POSTER: [
                MessageHandler(filters.PHOTO, get_season_poster), 
                CommandHandler("skip", skip_season_poster)
            ],
            S_GET_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_season_desc),
                CommandHandler("skip", skip_season_desc)
            ],
            S_CONFIRM: [CallbackQueryHandler(save_season, pattern="^save_season$")],
            S_ASK_MORE: [ # NAYA State
                CallbackQueryHandler(add_more_seasons_yes, pattern="^add_season_more_yes$"),
                CallbackQueryHandler(add_more_seasons_no, pattern="^add_season_more_no$")
            ]
        }, 
        fallbacks=global_fallbacks + add_season_fallback,
        allow_reentry=True 
    )
    
    add_episode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_episode_start, pattern="^admin_add_episode$")], 
        states={
            E_GET_ANIME: [
                CallbackQueryHandler(add_episode_show_anime_list, pattern="^addep_page_"), 
                CallbackQueryHandler(get_anime_for_episode, pattern="^ep_anime_")
            ], 
            E_GET_SEASON: [
                CallbackQueryHandler(get_season_for_episode, pattern="^ep_season_"),
                CallbackQueryHandler(add_episode_show_anime_list, pattern="^addep_page_") 
            ], 
            E_GET_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_episode_number)],
            E_GET_480P: [MessageHandler(filters.ALL & ~filters.COMMAND, get_480p_file), CommandHandler("skip", skip_480p)],
            E_GET_720P: [MessageHandler(filters.ALL & ~filters.COMMAND, get_720p_file), CommandHandler("skip", skip_720p)],
            E_GET_1080P: [MessageHandler(filters.ALL & ~filters.COMMAND, get_1080p_file), CommandHandler("skip", skip_1080p)],
            E_GET_4K: [MessageHandler(filters.ALL & ~filters.COMMAND, get_4k_file), CommandHandler("skip", skip_4k)],
            E_ASK_MORE: [ # NAYA State
                CallbackQueryHandler(add_more_episodes_yes, pattern="^add_ep_more_yes$"),
                CallbackQueryHandler(add_more_episodes_no, pattern="^add_ep_more_no$")
            ]
        }, 
        fallbacks=global_fallbacks + add_episode_fallback,
        allow_reentry=True 
    )
    
    set_donate_qr_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_donate_qr_start, pattern="^admin_set_donate_qr$")], 
        states={CD_GET_QR: [MessageHandler(filters.PHOTO, set_donate_qr_save)]}, 
        fallbacks=global_fallbacks + donate_settings_fallback,
        allow_reentry=True 
    )
    set_links_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_links_start, pattern="^admin_set_backup_link$|^admin_set_download_link$|^admin_set_help_link$|^admin_set_verify_link$|^admin_set_request_link$")], # NAYA
        states={CL_GET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link), CommandHandler("skip", skip_link)]}, 
        fallbacks=global_fallbacks + links_fallback,
        allow_reentry=True 
    ) 
    post_gen_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(post_gen_menu, pattern="^admin_post_gen$")], 
        states={
            PG_MENU: [CallbackQueryHandler(post_gen_select_anime, pattern="^post_gen_season$|^post_gen_episode$|^post_gen_anime$|^post_gen_movie$")], 
            PG_GET_ANIME: [
                CallbackQueryHandler(post_gen_show_anime_list, pattern="^postgen_page_"),
                CallbackQueryHandler(post_gen_select_season, pattern="^post_anime_")
            ], 
            PG_GET_SEASON: [
                CallbackQueryHandler(post_gen_select_episode, pattern="^post_season_"),
                CallbackQueryHandler(post_gen_show_anime_list, pattern="^postgen_page_") 
            ], 
            PG_GET_EPISODE: [
                CallbackQueryHandler(post_gen_final_episode, pattern="^post_ep_"),
                CallbackQueryHandler(post_gen_select_season, pattern="^post_anime_") 
            ], 
            PG_GET_SHORT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_gen_get_short_link)],
            PG_GET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_gen_send_to_chat)],
            # NAYA Preview states
            PG_PREVIEW: [
                CallbackQueryHandler(post_preview_publish, pattern="^post_preview_publish$"),
                CallbackQueryHandler(post_preview_edit, pattern="^post_preview_edit$"),
                CallbackQueryHandler(post_preview_quote, pattern="^post_preview_quote$"),
                CallbackQueryHandler(post_preview_change_chat, pattern="^post_preview_change_chat$"),
                CallbackQueryHandler(post_preview_cancel, pattern="^post_preview_cancel$"),
                CallbackQueryHandler(post_preview_back, pattern="^post_preview_back$"),
            ],
            PG_EDIT_MENU: [
                CallbackQueryHandler(post_edit_title_start, pattern="^post_edit_title$"),
                CallbackQueryHandler(post_edit_desc_start, pattern="^post_edit_desc$"),
                CallbackQueryHandler(post_edit_footer_start, pattern="^post_edit_footer$"),
                CallbackQueryHandler(post_preview_back, pattern="^post_preview_back$"),
            ],
            PG_EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_title_save)],
            PG_EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_desc_save)],
            PG_EDIT_FOOTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_footer_save)],
        }, 
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True 
    )
    del_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_anime_start, pattern="^admin_del_anime$")], 
        states={
            DA_GET_ANIME: [
                CallbackQueryHandler(delete_anime_show_anime_list, pattern="^delanime_page_"),
                CallbackQueryHandler(delete_anime_confirm, pattern="^del_anime_")
            ], 
            DA_CONFIRM: [CallbackQueryHandler(delete_anime_do, pattern="^del_anime_confirm_yes$")]
        }, 
        fallbacks=global_fallbacks + manage_fallback,
        allow_reentry=True 
    )
    del_season_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_season_start, pattern="^admin_del_season$")], 
        states={
            DS_GET_ANIME: [
                CallbackQueryHandler(delete_season_show_anime_list, pattern="^delseason_page_"),
                CallbackQueryHandler(delete_season_select, pattern="^del_season_anime_")
            ], 
            DS_GET_SEASON: [
                CallbackQueryHandler(delete_season_confirm, pattern="^del_season_"),
                CallbackQueryHandler(delete_season_show_anime_list, pattern="^delseason_page_") 
            ], 
            DS_CONFIRM: [CallbackQueryHandler(delete_season_do, pattern="^del_season_confirm_yes$")]
        }, 
        fallbacks=global_fallbacks + manage_fallback,
        allow_reentry=True 
    )
    del_episode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_episode_start, pattern="^admin_del_episode$")], 
        states={
            DE_GET_ANIME: [
                CallbackQueryHandler(delete_episode_show_anime_list, pattern="^delep_page_"),
                CallbackQueryHandler(delete_episode_select_season, pattern="^del_ep_anime_")
            ],
          DE_GET_SEASON: [
                CallbackQueryHandler(delete_episode_select_episode, pattern="^del_ep_season_"),
                CallbackQueryHandler(delete_episode_show_anime_list, pattern="^delep_page_") 
            ],
            DE_GET_EPISODE: [
                CallbackQueryHandler(delete_episode_confirm, pattern="^del_ep_num_"),
                CallbackQueryHandler(delete_episode_select_season, pattern="^del_ep_anime_") 
            ],
            DE_CONFIRM: [CallbackQueryHandler(delete_episode_do, pattern="^del_ep_confirm_yes$")]
        }, 
        fallbacks=global_fallbacks + manage_fallback,
        allow_reentry=True 
    )
    
    # NAYA (v32): Update Photo Conv (Updated Entry Point)
    update_photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_photo_start, pattern="^admin_update_photo_content$")],
        states={
            UP_GET_ANIME: [
                CallbackQueryHandler(update_photo_show_anime_list, pattern="^upphoto_page_"),
                CallbackQueryHandler(update_photo_select_target, pattern="^upphoto_anime_")
            ],
            UP_GET_TARGET: [
                CallbackQueryHandler(update_photo_get_poster, pattern="^upphoto_target_"),
                CallbackQueryHandler(update_photo_show_anime_list, pattern="^upphoto_page_") 
            ],
            UP_GET_POSTER: [
                MessageHandler(filters.PHOTO, update_photo_save),
                MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.PHOTO, update_photo_invalid_input)
            ]
        },
        fallbacks=global_fallbacks + update_photo_fallback, # NAYA
        allow_reentry=True
    )
    
    edit_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_anime_start, pattern="^admin_edit_anime$")],
        states={
            EA_GET_ANIME: [
                CallbackQueryHandler(edit_anime_show_anime_list, pattern="^editanime_page_"),
                CallbackQueryHandler(edit_anime_get_new_name, pattern="^edit_anime_")
            ],
            EA_GET_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_anime_save)],
            EA_CONFIRM: [CallbackQueryHandler(edit_anime_do, pattern="^edit_anime_confirm_yes$")]
        },
        fallbacks=global_fallbacks + edit_fallback,
        allow_reentry=True
    )
    edit_season_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_season_start, pattern="^admin_edit_season$")],
        states={
            ES_GET_ANIME: [
                CallbackQueryHandler(edit_season_show_anime_list, pattern="^editseason_page_"),
                CallbackQueryHandler(edit_season_select, pattern="^edit_season_anime_")
            ],
            ES_GET_SEASON: [
                CallbackQueryHandler(edit_season_get_new_name, pattern="^edit_season_"),
                CallbackQueryHandler(edit_season_show_anime_list, pattern="^editseason_page_") 
            ],
            ES_GET_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_season_save)],
            ES_CONFIRM: [CallbackQueryHandler(edit_season_do, pattern="^edit_season_confirm_yes$")]
        },
        fallbacks=global_fallbacks + edit_fallback,
        allow_reentry=True
    )
    edit_episode_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_episode_start, pattern="^admin_edit_episode$")],
        states={
            EE_GET_ANIME: [
                CallbackQueryHandler(edit_episode_show_anime_list, pattern="^editep_page_"),
                CallbackQueryHandler(edit_episode_select_season, pattern="^edit_ep_anime_")
            ],
            EE_GET_SEASON: [
                CallbackQueryHandler(edit_episode_select_episode, pattern="^edit_ep_season_"),
                CallbackQueryHandler(edit_episode_show_anime_list, pattern="^editep_page_") 
            ],
            EE_GET_EPISODE: [
                CallbackQueryHandler(edit_episode_get_new_num, pattern="^edit_ep_num_"),
                CallbackQueryHandler(edit_episode_select_season, pattern="^edit_ep_anime_") 
            ],
            EE_GET_NEW_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_episode_save)],
            EE_CONFIRM: [CallbackQueryHandler(edit_episode_do, pattern="^edit_ep_confirm_yes$")]
        },
        fallbacks=global_fallbacks + edit_fallback,
        allow_reentry=True
    )

    gen_link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(gen_link_menu, pattern="^admin_gen_link$")],
        states={
            GL_MENU: [CallbackQueryHandler(gen_link_select_anime, pattern="^gen_link_anime$|^gen_link_movie$|^gen_link_season$|^gen_link_episode$")],
            GL_GET_ANIME: [
                CallbackQueryHandler(gen_link_show_anime_list, pattern="^genlink_page_"),
                CallbackQueryHandler(gen_link_select_season, pattern="^gen_link_anime_")
            ],
            GL_GET_SEASON: [
                CallbackQueryHandler(gen_link_select_episode, pattern="^gen_link_season_"),
                CallbackQueryHandler(gen_link_show_anime_list, pattern="^genlink_page_") 
            ],
            GL_GET_EPISODE: [
                CallbackQueryHandler(gen_link_finish, pattern="^gen_link_ep_"),
                CallbackQueryHandler(gen_link_select_season, pattern="^gen_link_anime_") 
            ],
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    add_co_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(co_admin_add_start, pattern="^admin_add_co_admin$")],
        states={
            CA_GET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, co_admin_add_get_id)],
            CA_CONFIRM: [CallbackQueryHandler(co_admin_add_do, pattern="^co_admin_add_yes$")]
        },
        fallbacks=global_fallbacks + admin_settings_fallback,
        allow_reentry=True
    )
    remove_co_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(co_admin_remove_start, pattern="^admin_remove_co_admin$")],
        states={
            CR_GET_ID: [CallbackQueryHandler(co_admin_remove_confirm, pattern="^co_admin_rem_")],
            CR_CONFIRM: [CallbackQueryHandler(co_admin_remove_do, pattern="^co_admin_rem_yes$")]
        },
        fallbacks=global_fallbacks + admin_settings_fallback,
        allow_reentry=True
    )
    custom_post_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(custom_post_start, pattern="^admin_custom_post$")],
        states={
            CPOST_GET_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_post_get_chat)],
            CPOST_GET_POSTER: [MessageHandler(filters.PHOTO, custom_post_get_poster)],
            CPOST_GET_CAPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_post_get_caption)],
            CPOST_GET_BTN_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_post_get_btn_text)],
            CPOST_GET_BTN_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_post_get_btn_url)],
            CPOST_CONFIRM: [CallbackQueryHandler(custom_post_send, pattern="^cpost_send$")]
        },
        fallbacks=global_fallbacks + admin_settings_fallback,
        allow_reentry=True
    )
    # NAYA v34: Broadcast Conv
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^admin_broadcast_start$")],
        states={
            BC_GET_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_get_message)],
            BC_CONFIRM: [CallbackQueryHandler(broadcast_do_send, pattern="^broadcast_confirm_yes$")]
        },
        fallbacks=global_fallbacks + admin_settings_fallback,
        allow_reentry=True
    )
    
    set_delete_time_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(set_delete_time_start, pattern="^admin_set_delete_time$"),
            CallbackQueryHandler(set_promo_delete_start, pattern="^admin_set_promo_delete$"),
            CallbackQueryHandler(set_admin_preview_delete_start, pattern="^admin_set_preview_delete$"),
        ],
        states={
            CS_GET_DELETE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delete_time_save)],
            CS_GET_PROMO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promo_delete_save)],
            CS_GET_PREVIEW_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preview_delete_save)],
        },
        fallbacks=global_fallbacks + admin_menu_fallback, 
        allow_reentry=True 
    )
    set_messages_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
            CallbackQueryHandler(bot_messages_menu_dl, pattern="^msg_menu_dl$"),
            CallbackQueryHandler(bot_messages_menu_postgen, pattern="^msg_menu_postgen$"),
            CallbackQueryHandler(bot_messages_menu_gen, pattern="^msg_menu_gen$"),
            CallbackQueryHandler(bot_messages_menu_admin, pattern="^msg_menu_admin$"),
            CallbackQueryHandler(set_msg_start, pattern="^msg_edit_"),
        ],
        states={
            M_MENU_MAIN: [
                CallbackQueryHandler(bot_messages_menu_dl, pattern="^msg_menu_dl$"),
                CallbackQueryHandler(bot_messages_menu_postgen, pattern="^msg_menu_postgen$"),
                CallbackQueryHandler(bot_messages_menu_gen, pattern="^msg_menu_gen$"),
                CallbackQueryHandler(bot_messages_menu_admin, pattern="^msg_menu_admin$"),
            ],
            M_MENU_DL: [
                CallbackQueryHandler(set_msg_start, pattern="^msg_edit_"),
                CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
                CallbackQueryHandler(bot_messages_menu_dl, pattern="^msg_menu_dl$"),
            ],
            M_MENU_POSTGEN: [
                CallbackQueryHandler(set_msg_start, pattern="^msg_edit_"),
                CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
            ],
            M_MENU_GEN: [
                CallbackQueryHandler(set_msg_start, pattern="^msg_edit_"),
                CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
            ],
            M_MENU_ADMIN: [
                CallbackQueryHandler(set_msg_start, pattern="^msg_edit_"),
                CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
            ],
            M_GET_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_msg_save),
                CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
                CallbackQueryHandler(bot_messages_menu_dl, pattern="^msg_menu_dl$"),
                CallbackQueryHandler(bot_messages_menu_gen, pattern="^msg_menu_gen$"),
                CallbackQueryHandler(bot_messages_menu_admin, pattern="^msg_menu_admin$"),
                CallbackQueryHandler(bot_messages_menu_postgen, pattern="^msg_menu_postgen$"),
            ],
        },
        fallbacks=global_fallbacks + admin_menu_fallback + [
            CallbackQueryHandler(bot_messages_menu, pattern="^admin_menu_messages$"),
        ],
        allow_reentry=True
    )
    
    appearance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(appearance_menu_start, pattern="^admin_menu_appearance$")],
        states={
            AP_MENU: [
                CallbackQueryHandler(appearance_set_font, pattern="^app_set_font$"),
                CallbackQueryHandler(appearance_set_style, pattern="^app_set_style$")
            ],
            AP_SET_FONT: [
                CallbackQueryHandler(appearance_save_font, pattern="^app_font_"),
                CallbackQueryHandler(back_to_appearance_menu, pattern="^back_to_appearance$")
            ],
            AP_SET_STYLE: [
                CallbackQueryHandler(appearance_save_style, pattern="^app_style_"),
                CallbackQueryHandler(back_to_appearance_menu, pattern="^back_to_appearance$")
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback + appearance_fallback,
        allow_reentry=True
    )
    
    # NAYA: Default Publish Chat Conversation
    set_default_chat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_default_chat_start, pattern="^admin_set_default_chat$")],
        states={
            DPC_GET_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_default_chat_save),
                CommandHandler("skip", set_default_chat_clear)
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # NAYA: Promo Channels Conversation
    promo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(promo_set_start, pattern="^promo_set_1$|^promo_set_2$|^promo_set_msg$|^promo_set_btn1$|^promo_set_btn2$|^promo_set_timer$")
        ],
        states={
            PROMO_GET_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, promo_set_save),
                CommandHandler("skip", promo_set_clear)
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    
    # NAYA (v32): Set Menu Photo Conv (Updated Entry Point)
    set_menu_photo_conv = ConversationHandler(
       entry_points=[CallbackQueryHandler(set_menu_photo_start, pattern="^admin_set_menu_photo$")],
       states={
           CS_GET_MENU_PHOTO: [
               MessageHandler(filters.PHOTO, set_menu_photo_save),
               CommandHandler("skip", skip_menu_photo)
           ]
       },
       fallbacks=global_fallbacks + update_photo_fallback, # NAYA
       allow_reentry=True
    )
    
    # NAYA (v33): Merge Series Conv
    merge_anime_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(merge_anime_start, pattern="^admin_merge_anime$")],
        states={
            MA_GET_TARGET_ANIME: [
                CallbackQueryHandler(merge_anime_select_target, pattern="^merge_target_page_"),
                CallbackQueryHandler(merge_anime_select_source, pattern="^merge_target_anime_")
            ],
            MA_GET_SOURCE_ANIME: [
                CallbackQueryHandler(merge_anime_select_source, pattern="^merge_source_page_"),
                CallbackQueryHandler(merge_anime_confirm, pattern="^merge_source_anime_"),
                CallbackQueryHandler(merge_anime_select_target, pattern="^admin_merge_anime") # Back button
            ],
            MA_CONFIRM: [CallbackQueryHandler(merge_anime_do, pattern="^merge_anime_confirm_yes$")]
        },
        fallbacks=global_fallbacks + edit_fallback,
        allow_reentry=True
    )

    
    # --- Saare handlers ko bot_app me add karo ---
    # /request system
    bot_app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE & filters.REPLY,
        admin_reply_to_request
    ), group=2)
    bot_app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        request_text_fallback
    ), group=1)
    
    bot_app.add_handler(add_anime_conv)
    bot_app.add_handler(add_movie_conv)  # NAYA: Movie
    bot_app.add_handler(add_season_conv)
    bot_app.add_handler(add_episode_conv)
    bot_app.add_handler(set_donate_qr_conv)
    bot_app.add_handler(set_links_conv)
    bot_app.add_handler(post_gen_conv)
    bot_app.add_handler(del_anime_conv)
    bot_app.add_handler(del_season_conv)
    bot_app.add_handler(del_episode_conv)
    bot_app.add_handler(update_photo_conv) # NAYA: Updated handler
    bot_app.add_handler(edit_anime_conv)
    bot_app.add_handler(edit_season_conv)
    bot_app.add_handler(edit_episode_conv)
    bot_app.add_handler(gen_link_conv)
    bot_app.add_handler(add_co_admin_conv) 
    bot_app.add_handler(remove_co_admin_conv) 
    bot_app.add_handler(custom_post_conv)
    bot_app.add_handler(broadcast_conv) # NAYA v34
    bot_app.add_handler(CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$"))
    bot_app.add_handler(CallbackQueryHandler(auto_delete_settings_menu, pattern="^admin_menu_auto_delete$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_admin_settings_menu, pattern="^admin_menu_admin_settings$|^back_to_admin_settings$"))
    # Promo + Preview delete timers ab set_delete_time_conv ke andar handle hote hain

    bot_app.add_handler(set_delete_time_conv) 
    bot_app.add_handler(set_messages_conv) 
    bot_app.add_handler(appearance_conv)
    bot_app.add_handler(set_menu_photo_conv) # NAYA: Updated handler
    bot_app.add_handler(set_default_chat_conv)  # NAYA: Default Publish Chat
    bot_app.add_handler(promo_conv)  # NAYA: Promo channels
    bot_app.add_handler(CallbackQueryHandler(promo_channels_menu, pattern="^admin_promo_channels$"))
    bot_app.add_handler(CallbackQueryHandler(language_menu, pattern="^admin_set_language$"))
    bot_app.add_handler(CallbackQueryHandler(post_buttons_menu, pattern="^admin_post_buttons$"))
    bot_app.add_handler(CallbackQueryHandler(admin_chats_menu, pattern="^admin_chats_menu$"))
    bot_app.add_handler(CallbackQueryHandler(request_timer_refresh, pattern="^request_timer_refresh$"))
    bot_app.add_handler(CallbackQueryHandler(file_timer_refresh, pattern="^file_timer_refresh$"))
    bot_app.add_handler(CallbackQueryHandler(thankyou_timer_refresh, pattern="^thankyou_timer_refresh$"))
    bot_app.add_handler(CallbackQueryHandler(chats_list, pattern="^chats_(pending|replied)_"))
    bot_app.add_handler(CallbackQueryHandler(chats_view, pattern="^chats_view_"))
    bot_app.add_handler(CallbackQueryHandler(chats_ban_user, pattern="^chats_banuser_"))
    
    chats_reply_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(chats_reply_start, pattern="^chats_reply_"),
            CallbackQueryHandler(chats_ban_start, pattern="^chats_ban_start$"),
        ],
        states={
            CHATS_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, chats_reply_save)],
            CHATS_BAN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, chats_ban_id_save)],
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    bot_app.add_handler(chats_reply_conv)
    bot_app.add_handler(CallbackQueryHandler(post_btn_toggle, pattern="^ptoggle_"))
    bot_app.add_handler(CallbackQueryHandler(btn_layout_menu, pattern="^admin_btn_layout$"))
    bot_app.add_handler(CallbackQueryHandler(btn_layout_select, pattern="^blayout_sel_"))
    bot_app.add_handler(CallbackQueryHandler(btn_layout_action, pattern="^blayout_act_"))
    bot_app.add_handler(CallbackQueryHandler(btn_layout_reset, pattern="^blayout_reset$"))
    
    pbtn_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(post_btn_text_start, pattern="^pbtn_"),
            CallbackQueryHandler(set_dev_contact_start, pattern="^admin_set_dev_contact$"),
        ],
        states={
            PBTN_GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_btn_text_save)]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    bot_app.add_handler(pbtn_conv)
    bot_app.add_handler(CallbackQueryHandler(language_set, pattern="^lang_"))
    bot_app.add_handler(CallbackQueryHandler(user_verify_howto, pattern="^user_verify_howto$"))
        
    verify_video_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_verify_video_start, pattern="^admin_set_verify_video$")],
        states={
            VERIFY_VIDEO: [
                MessageHandler(filters.VIDEO | filters.ANIMATION | filters.Document.ALL, set_verify_video_save),
                CommandHandler("skip", set_verify_video_clear),
            ]
        },
        fallbacks=global_fallbacks + admin_menu_fallback,
        allow_reentry=True
    )
    bot_app.add_handler(verify_video_conv)
    bot_app.add_handler(merge_anime_conv) # NAYA: New feature (v33)

    # Standard commands
    bot_app.add_handler(CommandHandler("start", start_command))
    # /request system
    request_conv = ConversationHandler(
        entry_points=[CommandHandler("request", request_command)],
        states={
            REQ_GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_receive)],
        },
        fallbacks=[CommandHandler("cancel", request_cancel), CommandHandler("start", request_cancel)],
        allow_reentry=True
    )
    bot_app.add_handler(request_conv)
    # Admin reply to request (must be outside other convs, group=2)
    bot_app.add_handler(MessageHandler(
        filters.REPLY & filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.VIDEO),
        admin_reply_to_request
    ), group=2)
    bot_app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        request_text_fallback
    ), group=3)
 
    bot_app.add_handler(CommandHandler("user", user_command)) 
    bot_app.add_handler(CommandHandler("menu", menu_command)) 
    bot_app.add_handler(CommandHandler("admin", admin_command)) 

    # Admin menu navigation (non-conversation)
    bot_app.add_handler(CallbackQueryHandler(add_content_menu, pattern="^admin_menu_add_content$"))
    bot_app.add_handler(CallbackQueryHandler(manage_content_menu, pattern="^admin_menu_manage_content$"))
    bot_app.add_handler(CallbackQueryHandler(edit_content_menu, pattern="^admin_menu_edit_content$")) 
    bot_app.add_handler(CallbackQueryHandler(donate_settings_menu, pattern="^admin_menu_donate_settings$"))
    bot_app.add_handler(CallbackQueryHandler(other_links_menu, pattern="^admin_menu_other_links$"))
    bot_app.add_handler(CallbackQueryHandler(admin_settings_menu, pattern="^admin_menu_admin_settings$")) 
    bot_app.add_handler(CallbackQueryHandler(co_admin_list, pattern="^admin_list_co_admin$")) 
    bot_app.add_handler(CallbackQueryHandler(update_photo_menu, pattern="^admin_menu_update_photo$")) # NAYA
    bot_app.add_handler(CallbackQueryHandler(show_user_stats, pattern="^admin_show_stats$")) # NAYA v34

    # User menu navigation (non-conversation)
    bot_app.add_handler(CallbackQueryHandler(user_show_donate_menu, pattern="^user_show_donate_menu$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"))

# User Download Flow (Non-conversation)
    bot_app.add_handler(CallbackQueryHandler(download_button_handler, pattern="^dl"))

    # Error handler
    bot_app.add_error_handler(error_handler)

    # --- NAYA: Webhook setup ---
    logger.info("Starting Flask server for webhook...")
    
    # Start the bot in a separate thread
    bot_event_loop = asyncio.new_event_loop()
    bot_thread = threading.Thread(target=run_async_bot_tasks, args=(bot_event_loop, bot_app))
    bot_thread.start()
    
    # Start Flask app (Waitress)
    logger.info(f"Flask (Waitress) server {WEBHOOK_URL} port {PORT} par sun raha hai...")
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
