# ============================================
# ===       COMPLETE WORKING BOT (v51)     ===
# ===   Movies + Series + Stable Preview   ===
# ===   Default Channel + Real Blockquote  ===
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
    Application, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters, Defaults
)
from telegram.error import BadRequest, Forbidden
from flask import Flask, request
from waitress import serve

# ==================== FONT MAPS ====================
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
    'default_bold': {
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶',
        'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿',
        's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜',
        'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥',
        'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
}
FONT_MAPS['small_caps_bold'] = FONT_MAPS['small_caps']
FONT_MAPS['monospace_bold'] = FONT_MAPS.get('monospace', {})
FONT_MAPS['sans_serif_regular'] = FONT_MAPS['sans_serif']
FONT_MAPS['sans_serif_regular_bold'] = FONT_MAPS['sans_serif_bold']
FONT_MAPS['script'] = FONT_MAPS['default']
FONT_MAPS['script_bold'] = FONT_MAPS['default_bold']
FONT_MAPS['monospace'] = FONT_MAPS['default']
FONT_MAPS['serif'] = FONT_MAPS['sans_serif']
FONT_MAPS['serif_bold'] = FONT_MAPS['sans_serif_bold']

async def apply_font_formatting(raw_text: str, font_settings: dict) -> str:
    font = font_settings.get('font', 'default')
    style = font_settings.get('style', 'normal')
    
    if font == 'default' and style == 'normal':
        return raw_text.replace('<f>', '').replace('</f>', '')

    map_key = f"{font}_{style}" if style == 'bold' else font
    font_map = FONT_MAPS.get(map_key, {})
    
    if not font_map:
        return raw_text.replace('<f>', '').replace('</f>', '')

    def replace_chars(text_chunk):
        return "".join([font_map.get(char, char) for char in text_chunk])

    def process_tags(match):
        content = match.group(1)
        parts = re.split(r'(<[^>]+>)', content)
        processed = []
        for part in parts:
            if re.match(r'<[^>]+>', part):
                processed.append(part)
            else:
                processed.append(replace_chars(part))
        return "".join(processed)

    try:
        return re.sub(r'<f>(.*?)</f>', process_tags, raw_text, flags=re.DOTALL)
    except Exception:
        return raw_text.replace('<f>', '').replace('</f>', '')

# ==================== SETUP ====================
load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MONGO_URI = os.getenv("MONGO_URI")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
    
    if not all([BOT_TOKEN, MONGO_URI, ADMIN_ID, LOG_CHANNEL_ID, WEBHOOK_URL]):
        logger.error("Secrets missing!")
        exit()
except Exception as e:
    logger.error(f"Secrets error: {e}")
    exit()

# ==================== DATABASE ====================
try:
    client = MongoClient(MONGO_URI)
    db = client['MovieBotDB']
    users_collection = db['users']
    movies_collection = db['movies']
    config_collection = db['config']
    
    movies_collection.create_index([("name", ASCENDING)])
    movies_collection.create_index([("type", ASCENDING)])
    movies_collection.create_index([("last_modified", DESCENDING)])
    users_collection.create_index([("interaction_count", DESCENDING)])
    
    client.admin.command('ping')
    logger.info("MongoDB connected!")
except Exception as e:
    logger.error(f"MongoDB failed: {e}")
    exit()

ITEMS_PER_PAGE = 20

# ==================== HELPERS ====================
async def is_main_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def is_co_admin(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    config = await get_config()
    return user_id in config.get("co_admins", [])

async def increment_user_interaction(user_id: int):
    try:
        users_collection.update_one({"_id": user_id}, {"$inc": {"interaction_count": 1}})
    except:
        pass

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

async def build_paginated_keyboard(collection, page, page_callback_prefix, item_callback_prefix, back_callback, filter_query=None):
    if filter_query is None:
        filter_query = {}
    skip = page * ITEMS_PER_PAGE
    total = collection.count_documents(filter_query)
    items = list(collection.find(filter_query).sort("last_modified", DESCENDING).skip(skip).limit(ITEMS_PER_PAGE))
    
    if not items and page == 0:
        return None, InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]])
    
    buttons = []
    for item in items:
        prefix = "📺 " if item.get("type") == "series" else "🎬 "
        buttons.append(InlineKeyboardButton(f"{prefix}{item['name']}", callback_data=f"{item_callback_prefix}{item['name']}"))
    
    keyboard = build_grid_keyboard(buttons, 2)
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{page_callback_prefix}{page-1}"))
    if (page + 1) * ITEMS_PER_PAGE < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"{page_callback_prefix}{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_callback)])
    
    return items, InlineKeyboardMarkup(keyboard)

# ==================== CONFIG + MESSAGES ====================
async def get_default_messages(lang="hinglish"):
    base = {
        "user_dl_dm_alert": "✅ <f>Check your DM with me!</f>",
        "user_dl_movie_not_found": "❌ <f>Content nahi mila.</f>",
        "user_dl_file_error": "❌ <f>{quality} file nahi bhej paya.</f>",
        "user_dl_blocked_error": "❌ <f>Aapne bot ko block kiya hua hai.</f>",
        "user_dl_qualities_not_found": "❌ <f>Koi quality available nahi.</f>",
        "user_dl_general_error": "❌ <f>Error! Dobara try karein.</f>",
        "user_dl_sending_file": "✅ <b>{movie_name}</b> | <b>{quality}</b>\n\n<f>File bhej raha hoon...</f>",
        "user_dl_select_quality": "<b>{movie_name}</b>\n\n<f>Quality select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {minutes} minute mein auto-delete ho jaayegi.</f></b>",
        "user_dl_fetching": "⏳ <f>Fetching...</f>",
        "user_menu_greeting": "<f>Salaam {full_name}! Ye raha aapka menu:</f>",
        "user_donate_qr_error": "❌ <f>Donation abhi set nahi hai.</f>",
        "user_donate_qr_text": "❤️ <b><f>Support Us!</f></b>\n\n<f>Agar aapko pasand aaya toh support kar sakte ho.</f>",
        "donate_thanks": "❤️ <f>Support ke liye shukriya!</f>",
        "user_not_admin": "<f>Aap admin nahi ho.</f>",
        "user_welcome_admin": "<f>Salaam Admin! /menu se panel kholo.</f>",
        "user_welcome_basic": "<f>Salaam {full_name}! /user se menu dekho.</f>",
        "admin_cancel": "<f>Operation cancel ho gaya.</f>",
        "admin_panel_main": "👑 <b><f>Admin Panel</f></b>\n<f>Control ready hai.</f>",
        "admin_panel_co": "👑 <b><f>Co-Admin Panel</f></b>",
        "admin_menu_add_content": "➕ <b><f>Add Content</f></b>\n\n<f>Kya add karna hai?</f>",
        "admin_add_movie_start": "<f>Movie ka <b>Naam</b> bhejo:</f>\n\n/cancel",
        "admin_add_movie_get_name": "<f>Ab <b>Poster</b> bhejo:</f>",
        "admin_add_movie_get_poster_error": "Photo bhejo.",
        "admin_add_movie_get_poster": "<f>Ab <b>Description</b> bhejo (ya /skip):</f>",
        "admin_add_movie_get_desc": "<f>Ab <b>480p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_skip_desc": "<f>Ab <b>480p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_get_480p": "<f>Ab <b>720p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_skip_480p": "<f>Ab <b>720p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_get_720p": "<f>Ab <b>1080p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_skip_720p": "<f>Ab <b>1080p</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_get_1080p": "<f>Ab <b>4K</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_skip_1080p": "<f>Ab <b>4K</b> file bhejo (ya /skip):</f>",
        "admin_add_movie_get_4k": "✅ <f>4K save.</f>",
        "admin_add_movie_skip_4k": "✅ <f>4K skip.</f>",
        "admin_add_movie_no_files_error": "⚠️ Kam se kam 1 file add karo.",
        "admin_add_movie_confirm": "<b>{name}</b>\n\n{description}\n\nFiles: <b>{file_count}</b>",
        "admin_add_movie_save_exists": "⚠️ '{name}' pehle se hai.",
        "admin_add_movie_save_success": "✅ '{name}' add ho gaya.",
        "admin_add_movie_save_error": "❌ Save nahi hua.",
        "admin_add_movie_helper_invalid": "Video file bhejo ya /skip.",
        "admin_add_movie_helper_success": "✅ <b>{quality}</b> save.",
        "admin_add_series_start": "<f>Series ka <b>Naam</b> bhejo:</f>\n\n/cancel",
        "admin_add_series_get_name": "<f>Ab <b>Poster</b> bhejo:</f>",
        "admin_add_series_get_poster": "<f>Ab <b>Description</b> bhejo (ya /skip):</f>",
        "admin_add_series_get_desc": "<f>Season 1 Episode 1 - 480p file bhejo:</f>",
        "admin_add_series_skip_desc": "<f>Season 1 Episode 1 - 480p file bhejo:</f>",
        "admin_add_series_confirm": "<b>{name}</b>\n\nSeasons: <b>{season_count}</b> | Episodes: <b>{episode_count}</b>",
        "admin_add_series_save_success": "✅ Series '{name}' add ho gayi.",
        "admin_menu_donate": "❤️ <b><f>Donation</f></b>",
        "admin_set_donate_qr_start": "<f>Donate QR photo bhejo:</f>",
        "admin_set_donate_qr_error": "Photo bhejo.",
        "admin_set_donate_qr_success": "✅ QR set ho gaya.",
        "admin_menu_links": "🔗 <b><f>Other Links</f></b>",
        "admin_set_link_backup": "<f>Backup Channel link bhejo:</f>\n/skip to remove",
        "admin_set_link_download": "<f>Global Download link bhejo:</f>\n/skip to remove",
        "admin_set_link_help": "<f>Help link bhejo:</f>\n/skip to remove",
        "admin_set_link_success": "✅ {link_type} link set.",
        "admin_set_link_skip": "✅ {link_type} link remove.",
        "admin_set_delete_time_start": "Current: <b>{current_minutes} min</b>\n\nNaya time (seconds) bhejo:",
        "admin_set_delete_time_success": "✅ Auto-delete ab <b>{seconds}s</b> ({minutes} min)",
        "admin_set_delete_time_nan": "Sirf number bhejo.",
        "admin_menu_messages_main": "⚙️ <b><f>Bot Messages</f></b>",
        "admin_set_msg_start": "Editing: <code>{msg_key}</code>\n\nCurrent:\n<code>{current_msg}</code>\n\nNaya message bhejo:",
        "admin_set_msg_success": "✅ '{msg_key}' update ho gaya.",
        "admin_menu_post_gen": "✍️ <b><f>Post Generator</f></b>",
        "admin_post_gen_select_movie": "Content select karo (Page {page}):",
        "admin_post_gen_no_movie": "❌ Koi content nahi hai.",
        "admin_post_gen_ask_shortlink": "✅ Ready!\n\nOriginal:\n<code>{original_download_url}</code>\n\nShort link bhejo (ya same copy karke bhej do):",
        "admin_post_gen_preview": "📋 <b>--- PREVIEW ---</b>\n\n{caption}\n\nTarget: <code>{chat_id}</code>",
        "admin_post_gen_success": "✅ Post '{chat_id}' par bhej diya.",
        "admin_post_gen_error": "❌ Post nahi bhej paya.\nError: {e}",
        "admin_menu_gen_link": "🔗 <b><f>Generate Link</f></b>",
        "admin_gen_link_select_movie": "Content select karo (Page {page}):",
        "admin_gen_link_no_movie": "❌ Koi content nahi.",
        "admin_gen_link_success": "✅ Link:\n<code>{final_link}</code>",
        "admin_del_movie_select": "Delete karne ke liye select karo (Page {page}):",
        "admin_del_movie_no_movie": "❌ Koi content nahi.",
        "admin_del_movie_confirm": "⚠️ <b>{movie_name}</b> delete karna hai?",
        "admin_del_movie_success": "✅ '{movie_name}' delete ho gaya.",
        "admin_del_movie_error": "❌ Delete nahi hua.",
        "admin_menu_update_photo": "🖼️ <b><f>Photo Settings</f></b>",
        "admin_update_photo_select_movie": "Poster update ke liye select (Page {page}):",
        "admin_update_photo_no_movie": "❌ Koi content nahi.",
        "admin_update_photo_get_poster": "<b>{target_name}</b> ka naya poster bhejo:",
        "admin_update_photo_invalid": "Photo bhejo.",
        "admin_update_photo_save_success_main": "✅ {movie_name} ka poster update.",
        "admin_edit_movie_select": "Naam edit ke liye select (Page {page}):",
        "admin_edit_movie_no_movie": "❌ Koi content nahi.",
        "admin_edit_movie_get_name": "<b>{movie_name}</b> ka naya naam bhejo:",
        "admin_edit_movie_save_exists": "⚠️ '{new_name}' pehle se hai.",
        "admin_edit_movie_confirm": "Purana: <code>{old_name}</code>\nNaya: <code>{new_name}</code>\n\nConfirm?",
        "admin_edit_movie_success": "✅ Naam '{old_name}' → '{new_name}'",
        "admin_menu_admin_settings": "🛠️ <b><f>Admin Settings</f></b>",
        "admin_co_admin_add_start": "Co-Admin ki User ID bhejo:",
        "admin_co_admin_add_confirm": "ID <code>{user_id}</code> ko Co-Admin banana hai?",
        "admin_co_admin_add_success": "✅ {user_id} ab Co-Admin hai.",
        "admin_co_admin_remove_no_co": "Koi Co-Admin nahi.",
        "admin_co_admin_remove_start": "Remove karne ke liye select karo:",
        "admin_co_admin_remove_confirm": "ID <code>{user_id}</code> remove karna hai?",
        "admin_co_admin_remove_success": "✅ {user_id} remove ho gaya.",
        "admin_co_admin_list_none": "Koi Co-Admin nahi.",
        "admin_co_admin_list_header": "<b>Co-Admins:</b>\n",
        "admin_custom_post_start": "Target Chat ID / @username bhejo:",
        "admin_custom_post_get_chat": "Ab Poster bhejo:",
        "admin_custom_post_get_poster_error": "Photo bhejo.",
        "admin_custom_post_get_poster": "Ab Caption bhejo:",
        "admin_custom_post_get_caption": "Button Text bhejo:",
        "admin_custom_post_get_btn_text": "Button URL bhejo:",
        "admin_custom_post_confirm": "--- PREVIEW ---\n\n{caption}\n\nTarget: <code>{chat_id}</code>",
        "admin_custom_post_success": "✅ Post bhej diya.",
        "admin_custom_post_error": "❌ Error: {e}",
        "admin_menu_appearance": "🎨 <b><f>Appearance</f></b>\n\nFont: <b>{font}</b>\nStyle: <b>{style}</b>\nQuote: <b>{quote}</b>",
        "admin_appearance_select_font": "Font select karo:\nCurrent: <b>{font}</b>",
        "admin_appearance_select_style": "Style select karo:\nCurrent: <b>{style}</b>",
        "admin_appearance_set_font_success": "✅ Font → <b>{font}</b>",
        "admin_appearance_set_style_success": "✅ Style → <b>{style}</b>",
        "admin_appearance_quote_toggle": "✅ Quote ab <b>{status}</b>",
        "admin_stats_loading": "⏳ Stats nikaal raha hoon...",
        "admin_stats_result": "📊 <b>Stats</b>\n\nTotal Users: <b>{total_users}</b>\n\nTop 10:\n{top_users_list}",
        "admin_stats_no_users": "Abhi koi active user nahi.",
        "admin_broadcast_start": "📢 Broadcast message bhejo (text/photo/video):",
        "admin_broadcast_confirm": "⚠️ {user_count} users ko bhejna hai?",
        "admin_broadcast_sending": "⏳ Broadcast shuru... {user_count} users",
        "admin_broadcast_success": "✅ Sent: {sent_count} | Failed: {failed_count}",
        "admin_default_channel_menu": "📢 <b>Default Channel</b>\n\nCurrent: <code>{current}</code>",
        "admin_default_channel_set_start": "Default Channel (@username ya ID) bhejo:",
        "admin_default_channel_success": "✅ Default Channel set: <code>{chat_id}</code>",
        "admin_default_channel_cleared": "✅ Default Channel clear.",
        "admin_language_menu": "🌐 <b>Language</b>\n\nCurrent: <b>{lang}</b>",
        "admin_language_set_success": "✅ Language → <b>{lang}</b>",
        "admin_post_edit_title": "Naya Title bhejo (sirf is post ke liye):",
        "admin_post_edit_desc": "Naya Description bhejo:",
        "admin_post_edit_genre": "Genre bhejo (comma separated):",
    }
    return base

async def get_config():
    config = config_collection.find_one({"_id": "bot_config"})
    if not config:
        default = {
            "_id": "bot_config",
            "donate_qr_id": None,
            "links": {"backup": "https://t.me/", "download": None, "help": "https://t.me/"},
            "user_menu_photo_id": None,
            "delete_seconds": 300,
            "messages": {},
            "co_admins": [],
            "appearance": {"font": "default", "style": "normal", "quote_enabled": False},
            "default_publish_chat": None,
            "language": "hinglish"
        }
        config_collection.insert_one(default)
        return default
    
    # Ensure keys
    updates = {}
    if "appearance" not in config:
        updates["appearance"] = {"font": "default", "style": "normal", "quote_enabled": False}
    if "default_publish_chat" not in config:
        updates["default_publish_chat"] = None
    if "language" not in config:
        updates["language"] = "hinglish"
    if "co_admins" not in config:
        updates["co_admins"] = []
    if "delete_seconds" not in config:
        updates["delete_seconds"] = 300
    if "links" not in config:
        updates["links"] = {"backup": "https://t.me/", "download": None, "help": "https://t.me/"}
    if "messages" not in config:
        updates["messages"] = {}
    
    if updates:
        config_collection.update_one({"_id": "bot_config"}, {"$set": updates})
        config.update(updates)
    
    # Fill missing messages
    lang = config.get("language", "hinglish")
    defaults = await get_default_messages(lang)
    msgs = config.get("messages", {})
    changed = False
    for k, v in defaults.items():
        if k not in msgs:
            msgs[k] = v
            changed = True
    if changed:
        config_collection.update_one({"_id": "bot_config"}, {"$set": {"messages": msgs}})
        config["messages"] = msgs
    
    return config

async def format_message(context, key, variables=None):
    config = await get_config()
    defaults = await get_default_messages(config.get("language", "hinglish"))
    raw = config.get("messages", {}).get(key, defaults.get(key, f"MISSING: {key}"))
    
    if variables:
        safe = {k: (str(v).replace('<','&lt;').replace('>','&gt;') if isinstance(v, str) else v) for k, v in variables.items()}
        try:
            raw = raw.format(**safe)
        except:
            pass
    
    # Real Telegram blockquote support
    appearance = config.get("appearance", {})
    if appearance.get("quote_enabled") and not raw.strip().startswith("<blockquote>"):
        raw = f"<blockquote>{raw}</blockquote>"
    
    font_settings = appearance
    return await apply_font_formatting(raw, font_settings)

async def delete_message_later(bot, chat_id, message_id, seconds):
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def send_donate_thank_you(context):
    try:
        msg = await format_message(context, "donate_thanks")
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg, parse_mode=ParseMode.HTML)
    except:
        pass
# ============================================================
# ===              CONVERSATION STATES                     ===
# ============================================================
(M_GET_NAME, M_GET_POSTER, M_GET_DESC, M_GET_480P, M_GET_720P, M_GET_1080P, M_GET_4K, M_CONFIRM) = range(8)
(S_GET_NAME, S_GET_POSTER, S_GET_DESC, S_GET_EPISODE, S_CONFIRM) = range(8, 13)
(DA_GET_MOVIE, DA_CONFIRM) = range(13, 15)
(EA_GET_MOVIE, EA_GET_NEW_NAME, EA_CONFIRM) = range(15, 18)
(PG_MENU, PG_GET_MOVIE, PG_GET_SHORT_LINK, PG_PREVIEW, PG_EDIT_TITLE, PG_EDIT_DESC, PG_EDIT_GENRE) = range(18, 25)
(GL_MENU, GL_GET_MOVIE) = range(25, 27)
(CD_GET_QR, CL_GET_LINK, CS_GET_DELETE_TIME) = range(27, 30)
(UP_GET_MOVIE, UP_GET_POSTER) = range(30, 32)
(CA_GET_ID, CA_CONFIRM, CR_GET_ID, CR_CONFIRM) = range(32, 36)
(CPOST_CHAT, CPOST_POSTER, CPOST_CAPTION, CPOST_BTN_TEXT, CPOST_BTN_URL, CPOST_CONFIRM) = range(36, 42)
(MM_MAIN, MM_DL, MM_GEN, MM_POSTGEN, MM_GET_MSG, MM_ADMIN) = range(42, 48)
(AP_MENU, AP_FONT, AP_STYLE) = range(48, 51)
(CS_MENU_PHOTO,) = range(51, 52)
(BC_GET_MSG, BC_CONFIRM) = range(52, 54)
(DC_SET_CHANNEL,) = range(54, 55)
(LANG_MENU,) = range(55, 56)
(ADD_EP_SELECT, ADD_EP_GET_FILE) = range(56, 58)

# ============================================================
# ===                    CANCEL + BACK                     ===
# ============================================================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if context.user_data:
        context.user_data.clear()
    reply_text = await format_message(context, "admin_cancel")
    try:
        if update.message:
            await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)
        elif update.callback_query:
            query = update.callback_query
            await query.answer("Canceled")
            try:
                await query.edit_message_text(reply_text, parse_mode=ParseMode.HTML)
            except:
                pass
    except:
        pass
    if await is_co_admin(user.id):
        await asyncio.sleep(0.3)
        await admin_command(update, context, from_callback=bool(update.callback_query))
    return ConversationHandler.END

async def back_to_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

async def back_to_add_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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

# ============================================================
# ===                    ADMIN COMMAND                     ===
# ============================================================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False):
    user_id = update.effective_user.id
    if not await is_co_admin(user_id):
        if not from_callback:
            text = await format_message(context, "user_not_admin")
            if update.message:
                await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            else:
                await update.callback_query.answer("Admin nahi ho.", show_alert=True)
        return

    if not await is_main_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🎬 Add Content", callback_data="admin_menu_add_content")],
            [InlineKeyboardButton("🗑️ Delete Content", callback_data="admin_del_movie")],
            [InlineKeyboardButton("✏️ Edit Content", callback_data="admin_edit_movie")],
            [InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen")],
            [InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")],
            [InlineKeyboardButton("🖼️ Photo Settings", callback_data="admin_menu_update_photo")],
            [InlineKeyboardButton("📊 User Stats", callback_data="admin_show_stats")],
        ]
        text = await format_message(context, "admin_panel_co")
    else:
        keyboard = [
            [InlineKeyboardButton("🎬 Add Content", callback_data="admin_menu_add_content")],
            [InlineKeyboardButton("🗑️ Delete", callback_data="admin_del_movie"),
             InlineKeyboardButton("✏️ Edit", callback_data="admin_edit_movie")],
            [InlineKeyboardButton("✍️ Post Generator", callback_data="admin_post_gen"),
             InlineKeyboardButton("🔗 Gen Link", callback_data="admin_gen_link")],
            [InlineKeyboardButton("🔗 Other Links", callback_data="admin_menu_other_links"),
             InlineKeyboardButton("❤️ Donation", callback_data="admin_menu_donate_settings")],
            [InlineKeyboardButton("⏱️ Auto-Delete", callback_data="admin_set_delete_time"),
             InlineKeyboardButton("🖼️ Photos", callback_data="admin_menu_update_photo")],
            [InlineKeyboardButton("🎨 Appearance", callback_data="admin_menu_appearance"),
             InlineKeyboardButton("📊 Stats", callback_data="admin_show_stats")],
            [InlineKeyboardButton("⚙ Messages", callback_data="admin_menu_messages")],
            [InlineKeyboardButton("🛠️ Admin Settings", callback_data="admin_menu_admin_settings")]
        ]
        text = await format_message(context, "admin_panel_main")

    reply_markup = InlineKeyboardMarkup(keyboard)

    if from_callback:
        query = update.callback_query
        try:
            if query.message.photo:
                await query.message.delete()
                await context.bot.send_message(query.from_user.id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            else:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            try:
                await context.bot.send_message(query.from_user.id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
            except:
                pass
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def add_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎬 Add Movie", callback_data="admin_add_movie")],
        [InlineKeyboardButton("📺 Add Series", callback_data="admin_add_series")],
        [InlineKeyboardButton("➕ Add Episode to Series", callback_data="admin_add_episode")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_add_content")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def manage_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🗑️ Delete Content", callback_data="admin_del_movie")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_manage_content") if "admin_menu_manage_content" in (await get_config()).get("messages", {}) else "🗑️ Delete Content"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def edit_content_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Name", callback_data="admin_edit_movie")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_edit_content") if "admin_menu_edit_content" in (await get_config()).get("messages", {}) else "✏️ Edit Content"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# ============================================================
# ===                    ADD MOVIE                         ===
# ============================================================
async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    context.user_data['qualities'] = {}
    text = await format_message(context, "admin_add_movie_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return M_GET_NAME

async def add_movie_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    text = await format_message(context, "admin_add_movie_get_name")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_POSTER

async def add_movie_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        text = await format_message(context, "admin_add_movie_get_poster_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return M_GET_POSTER
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_movie_get_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_DESC

async def add_movie_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    text = await format_message(context, "admin_add_movie_get_desc")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_480P

async def add_movie_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = None
    text = await format_message(context, "admin_add_movie_skip_desc")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_480P

async def _save_quality(update, context, quality):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith('video'):
        file_id = update.message.document.file_id
    if not file_id:
        text = await format_message(context, "admin_add_movie_helper_invalid")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return False
    context.user_data['qualities'][quality] = file_id
    text = await format_message(context, "admin_add_movie_helper_success", {"quality": quality})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return True

async def add_movie_get_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_quality(update, context, "480p"):
        return M_GET_480P
    text = await format_message(context, "admin_add_movie_get_480p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_720P

async def add_movie_skip_480p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_movie_skip_480p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_720P

async def add_movie_get_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_quality(update, context, "720p"):
        return M_GET_720P
    text = await format_message(context, "admin_add_movie_get_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def add_movie_skip_720p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_movie_skip_720p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_1080P

async def add_movie_get_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _save_quality(update, context, "1080p"):
        return M_GET_1080P
    text = await format_message(context, "admin_add_movie_get_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_4K

async def add_movie_skip_1080p(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = await format_message(context, "admin_add_movie_skip_1080p")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return M_GET_4K

async def add_movie_get_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _save_quality(update, context, "4K")
    return await add_movie_confirm(update, context)

async def add_movie_skip_4k(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await add_movie_confirm(update, context)

async def add_movie_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('qualities'):
        text = await format_message(context, "admin_add_movie_no_files_error")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return M_GET_480P

    name = context.user_data['name']
    desc = context.user_data.get('description') or "N/A"
    file_count = len(context.user_data['qualities'])
    caption = await format_message(context, "admin_add_movie_confirm", {
        "name": name, "description": desc, "file_count": file_count
    })
    keyboard = [[InlineKeyboardButton("✅ Save", callback_data="save_movie")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    try:
        await update.message.reply_photo(
            photo=context.user_data['poster_id'],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return M_CONFIRM

async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = context.user_data['name']
    if movies_collection.find_one({"name": name}):
        text = await format_message(context, "admin_add_movie_save_exists", {"name": name})
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(2)
        await add_content_menu(update, context)
        return ConversationHandler.END

    doc = {
        "name": name,
        "type": "movie",
        "poster_id": context.user_data['poster_id'],
        "description": context.user_data.get('description'),
        "qualities": context.user_data['qualities'],
        "created_at": datetime.now(),
        "last_modified": datetime.now()
    }
    movies_collection.insert_one(doc)
    text = await format_message(context, "admin_add_movie_save_success", {"name": name})
    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    except:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(2)
    await add_content_menu(update, context)
    return ConversationHandler.END

# ============================================================
# ===                    ADD SERIES                        ===
# ============================================================
async def add_series_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    context.user_data['seasons'] = {}
    context.user_data['current_season'] = 1
    context.user_data['current_episode'] = 1
    context.user_data['current_qualities'] = {}
    text = await format_message(context, "admin_add_series_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return S_GET_NAME

async def add_series_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    text = await format_message(context, "admin_add_series_get_name")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_POSTER

async def add_series_get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Photo bhejo.", parse_mode=ParseMode.HTML)
        return S_GET_POSTER
    context.user_data['poster_id'] = update.message.photo[-1].file_id
    text = await format_message(context, "admin_add_series_get_poster")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_DESC

async def add_series_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    text = await format_message(context, "admin_add_series_get_desc")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_EPISODE

async def add_series_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = None
    text = await format_message(context, "admin_add_series_skip_desc")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    return S_GET_EPISODE

async def add_series_get_episode_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and "video" in update.message.document.mime_type:
        file_id = update.message.document.file_id

    if not file_id:
        await update.message.reply_text("Video file bhejo ya /done /new_season type karo.", parse_mode=ParseMode.HTML)
        return S_GET_EPISODE

    current_q = context.user_data.setdefault('current_qualities', {})
    for q in ['480p', '720p', '1080p', '4K']:
        if q not in current_q:
            current_q[q] = file_id
            next_q = None
            found = False
            for qq in ['480p', '720p', '1080p', '4K']:
                if found:
                    next_q = qq
                    break
                if qq == q:
                    found = True
            if next_q:
                await update.message.reply_text(f"✅ {q} save.\nAb <b>{next_q}</b> bhejo ya /done", parse_mode=ParseMode.HTML)
            else:
                # episode complete
                season = context.user_data['current_season']
                episode = context.user_data['current_episode']
                if season not in context.user_data['seasons']:
                    context.user_data['seasons'][season] = {}
                context.user_data['seasons'][season][episode] = current_q.copy()
                context.user_data['current_qualities'] = {}
                context.user_data['current_episode'] += 1
                await update.message.reply_text(
                    f"✅ S{season}E{episode} complete!\n\nAgle episode ke liye file bhejo\nya /new_season\nya /done",
                    parse_mode=ParseMode.HTML
                )
            return S_GET_EPISODE
    return S_GET_EPISODE

async def add_series_new_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_season'] += 1
    context.user_data['current_episode'] = 1
    context.user_data['current_qualities'] = {}
    await update.message.reply_text(
        f"✅ Naya Season {context.user_data['current_season']} shuru.\nEpisode 1 - 480p file bhejo:",
        parse_mode=ParseMode.HTML
    )
    return S_GET_EPISODE

async def add_series_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('current_qualities'):
        season = context.user_data['current_season']
        episode = context.user_data['current_episode']
        if season not in context.user_data['seasons']:
            context.user_data['seasons'][season] = {}
        context.user_data['seasons'][season][episode] = context.user_data['current_qualities'].copy()

    if not context.user_data.get('seasons'):
        await update.message.reply_text("Kam se kam 1 episode add karo!", parse_mode=ParseMode.HTML)
        return S_GET_EPISODE

    return await add_series_confirm(update, context)

async def add_series_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['name']
    desc = context.user_data.get('description') or "N/A"
    season_count = len(context.user_data['seasons'])
    episode_count = sum(len(eps) for eps in context.user_data['seasons'].values())
    caption = await format_message(context, "admin_add_series_confirm", {
        "name": name, "description": desc,
        "season_count": season_count, "episode_count": episode_count
    })
    keyboard = [[InlineKeyboardButton("✅ Save Series", callback_data="save_series")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_add_content")]]
    try:
        await update.message.reply_photo(
            photo=context.user_data['poster_id'],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return S_CONFIRM

async def save_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = context.user_data['name']
    if movies_collection.find_one({"name": name}):
        text = await format_message(context, "admin_add_movie_save_exists", {"name": name})
        try:
            await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
        except:
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(2)
        await add_content_menu(update, context)
        return ConversationHandler.END

    seasons_list = []
    for s_num in sorted(context.user_data['seasons'].keys()):
        episodes = []
        for e_num in sorted(context.user_data['seasons'][s_num].keys()):
            episodes.append({
                "episode_number": e_num,
                "qualities": context.user_data['seasons'][s_num][e_num]
            })
        seasons_list.append({"season_number": s_num, "episodes": episodes})

    doc = {
        "name": name,
        "type": "series",
        "poster_id": context.user_data['poster_id'],
        "description": context.user_data.get('description'),
        "seasons": seasons_list,
        "created_at": datetime.now(),
        "last_modified": datetime.now()
    }
    movies_collection.insert_one(doc)
    text = await format_message(context, "admin_add_series_save_success", {"name": name})
    try:
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    except:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(2)
    await add_content_menu(update, context)
    return ConversationHandler.END

# ============================================================
# ===         ADD EPISODE TO EXISTING SERIES               ===
# ============================================================
async def add_episode_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    return await add_episode_show_list(update, context, page=0)

async def add_episode_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    if query.data.startswith("addep_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()

    items, keyboard = await build_paginated_keyboard(
        movies_collection, page, "addep_page_", "addep_series_",
        "back_to_add_content", filter_query={"type": "series"}
    )
    if not items and page == 0:
        await query.edit_message_text("❌ Koi Series nahi mili.", reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    await query.edit_message_text("Kaunsi Series mein episode add karna hai?", reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return ADD_EP_SELECT

async def add_episode_select_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    series_name = query.data.replace("addep_series_", "")
    context.user_data['series_name'] = series_name
    context.user_data['current_qualities'] = {}
    await query.edit_message_text(
        f"<b>{series_name}</b>\n\nNaye episode ki 480p file bhejo:\n(Baad mein 720p/1080p/4K bhej sakte ho)\n\n/done se finish",
        parse_mode=ParseMode.HTML
    )
    return ADD_EP_GET_FILE

async def add_episode_get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = None
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document and update.message.document.mime_type and "video" in (update.message.document.mime_type or ""):
        file_id = update.message.document.file_id

    if not file_id:
        await update.message.reply_text("Video file bhejo ya /done", parse_mode=ParseMode.HTML)
        return ADD_EP_GET_FILE

    current_q = context.user_data.setdefault('current_qualities', {})
    for q in ['480p', '720p', '1080p', '4K']:
        if q not in current_q:
            current_q[q] = file_id
            next_qs = [qq for qq in ['480p', '720p', '1080p', '4K'] if qq not in current_q]
            if next_qs:
                await update.message.reply_text(f"✅ {q} save.\nAb {next_qs[0]} bhejo ya /done", parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text("✅ Saari qualities mil gayi. /done type karo.", parse_mode=ParseMode.HTML)
            return ADD_EP_GET_FILE
    return ADD_EP_GET_FILE

async def add_episode_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    series_name = context.user_data.get('series_name')
    qualities = context.user_data.get('current_qualities', {})
    if not qualities:
        await update.message.reply_text("Kam se kam 1 quality add karo!", parse_mode=ParseMode.HTML)
        return ADD_EP_GET_FILE

    series = movies_collection.find_one({"name": series_name, "type": "series"})
    if not series:
        await update.message.reply_text("Series nahi mili.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    seasons = series.get("seasons", [])
    if not seasons:
        seasons = [{"season_number": 1, "episodes": []}]

    last_season = seasons[-1]
    last_ep_num = 0
    if last_season.get("episodes"):
        last_ep_num = max(ep["episode_number"] for ep in last_season["episodes"])

    new_ep = {"episode_number": last_ep_num + 1, "qualities": qualities}
    last_season["episodes"].append(new_ep)

    movies_collection.update_one(
        {"name": series_name},
        {"$set": {"seasons": seasons, "last_modified": datetime.now()}}
    )
    await update.message.reply_text(
        f"✅ {series_name} mein S{last_season['season_number']}E{new_ep['episode_number']} add ho gaya!",
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================
# ===                    DELETE / EDIT                     ===
# ============================================================
async def delete_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await delete_movie_show_list(update, context, 0)

async def delete_movie_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    if query.data.startswith("delmovie_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
    items, keyboard = await build_paginated_keyboard(
        movies_collection, page, "delmovie_page_", "del_movie_", "back_to_manage"
    )
    text = await format_message(context, "admin_del_movie_select", {"page": page+1}) if items else await format_message(context, "admin_del_movie_no_movie")
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return DA_GET_MOVIE

async def delete_movie_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace("del_movie_", "")
    context.user_data['movie_name'] = name
    text = await format_message(context, "admin_del_movie_confirm", {"movie_name": name})
    keyboard = [[InlineKeyboardButton("✅ Delete", callback_data="del_movie_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_manage")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return DA_CONFIRM

async def delete_movie_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = context.user_data['movie_name']
    movies_collection.delete_one({"name": name})
    text = await format_message(context, "admin_del_movie_success", {"movie_name": name})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(2)
    await manage_content_menu(update, context)
    return ConversationHandler.END

async def edit_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await edit_movie_show_list(update, context, 0)

async def edit_movie_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    if query.data.startswith("editmovie_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
    items, keyboard = await build_paginated_keyboard(
        movies_collection, page, "editmovie_page_", "edit_movie_", "back_to_edit_menu"
    )
    text = await format_message(context, "admin_edit_movie_select", {"page": page+1}) if items else await format_message(context, "admin_edit_movie_no_movie")
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return EA_GET_MOVIE

async def edit_movie_get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace("edit_movie_", "")
    context.user_data['old_movie_name'] = name
    text = await format_message(context, "admin_edit_movie_get_name", {"movie_name": name})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return EA_GET_NEW_NAME

async def edit_movie_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text.strip()
    old_name = context.user_data['old_movie_name']
    if movies_collection.find_one({"name": new_name}):
        text = await format_message(context, "admin_edit_movie_save_exists", {"new_name": new_name})
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return EA_GET_NEW_NAME
    context.user_data['new_movie_name'] = new_name
    text = await format_message(context, "admin_edit_movie_confirm", {"old_name": old_name, "new_name": new_name})
    keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="edit_movie_confirm_yes")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_edit_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return EA_CONFIRM

async def edit_movie_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    old = context.user_data['old_movie_name']
    new = context.user_data['new_movie_name']
    movies_collection.update_one({"name": old}, {"$set": {"name": new, "last_modified": datetime.now()}})
    text = await format_message(context, "admin_edit_movie_success", {"old_name": old, "new_name": new})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    context.user_data.clear()
    await asyncio.sleep(2)
    await edit_content_menu(update, context)
    return ConversationHandler.END
# ============================================================
# ===         FIXED POST GENERATOR (Preview + Publish)     ===
# ============================================================
async def post_gen_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("✍️ Create Post", callback_data="post_gen_movie")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_post_gen")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return PG_MENU

async def post_gen_select_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await post_gen_show_list(update, context, 0)

async def post_gen_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    if query.data.startswith("postgen_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
    items, keyboard = await build_paginated_keyboard(
        movies_collection, page, "postgen_page_", "post_movie_", "admin_post_gen"
    )
    text = await format_message(context, "admin_post_gen_select_movie", {"page": page+1}) if items else await format_message(context, "admin_post_gen_no_movie")
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return PG_GET_MOVIE

async def post_gen_ask_shortlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    movie_name = query.data.replace("post_movie_", "")
    context.user_data.clear()
    context.user_data['movie_name'] = movie_name

    try:
        bot_username = (await context.bot.get_me()).username
        movie_doc = movies_collection.find_one({"name": movie_name})
        if not movie_doc:
            await query.edit_message_text("❌ Content nahi mila.", parse_mode=ParseMode.HTML)
            return ConversationHandler.END

        movie_id = str(movie_doc['_id'])
        original_url = f"https://t.me/{bot_username}?start=dl{movie_id}"

        context.user_data['post_poster_id'] = movie_doc['poster_id']
        context.user_data['post_title'] = movie_name
        context.user_data['post_description'] = movie_doc.get('description') or ""
        context.user_data['post_genre'] = ""
        context.user_data['original_download_url'] = original_url
        context.user_data['content_type'] = movie_doc.get('type', 'movie')

        text = await format_message(context, "admin_post_gen_ask_shortlink", {
            "original_download_url": original_url
        })
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return PG_GET_SHORT_LINK
    except Exception as e:
        logger.error(f"Post gen error: {e}")
        await query.edit_message_text("❌ Error. Logs check karo.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

async def post_gen_get_short_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    short_link = update.message.text.strip()
    context.user_data['short_link'] = short_link

    # Build caption
    title = context.user_data.get('post_title', '')
    desc = context.user_data.get('post_description', '')
    genre = context.user_data.get('post_genre', '')

    caption = f"<b>{title}</b>\n\n"
    if genre:
        caption += f"<b>🎭 Genre:</b> {genre}\n\n"
    if desc:
        caption += f"<b>📖 Synopsis:</b>\n{desc}\n\n"
    caption += "Neeche Download button dabao!"

    context.user_data['post_caption_raw'] = caption

    config = await get_config()
    default_chat = config.get("default_publish_chat")

    if default_chat:
        context.user_data['target_chat'] = default_chat
        return await show_post_preview(update, context)
    else:
        await update.message.reply_text(
            "⚠️ Default Channel set nahi hai.\n\nAbhi temporary ke liye Chat ID / @username bhejo:",
            parse_mode=ParseMode.HTML
        )
        context.user_data['waiting_temp_chat'] = True
        return PG_PREVIEW

async def show_post_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption_raw = context.user_data.get('post_caption_raw', '')
    poster_id = context.user_data.get('post_poster_id')
    short_link = context.user_data.get('short_link')
    target = context.user_data.get('target_chat', 'Not set')

    config = await get_config()
    links = config.get('links', {})
    bot_username = (await context.bot.get_me()).username

    btn_download = InlineKeyboardButton("⬇️ Download", url=short_link)
    btn_backup = InlineKeyboardButton("Backup", url=links.get('backup') or "https://t.me/")
    btn_donate = InlineKeyboardButton("Donate", url=f"https://t.me/{bot_username}?start=donate")

    keyboard = [
        [btn_backup, btn_donate],
        [btn_download],
        [
            InlineKeyboardButton("✅ Publish Now", callback_data="post_publish"),
            InlineKeyboardButton("✏️ Edit", callback_data="post_edit_menu")
        ],
        [InlineKeyboardButton("🔄 Change Target", callback_data="post_change_target")],
        [InlineKeyboardButton("⬅️ Cancel", callback_data="admin_menu")]
    ]

    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    caption_formatted = await apply_font_formatting(caption_raw, font_settings)

    preview_text = await format_message(context, "admin_post_gen_preview", {
        "caption": caption_formatted,
        "chat_id": target
    })

    try:
        if update.callback_query:
            query = update.callback_query
            try:
                await query.edit_message_media(
                    media=InputMediaPhoto(media=poster_id, caption=preview_text, parse_mode=ParseMode.HTML),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except:
                await query.edit_message_text(preview_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_photo(
                photo=poster_id,
                caption=preview_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Preview error: {e}")
        if update.message:
            await update.message.reply_text(preview_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    return PG_PREVIEW

async def post_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📝 Edit Title", callback_data="post_edit_title")],
        [InlineKeyboardButton("📖 Edit Description", callback_data="post_edit_desc")],
        [InlineKeyboardButton("🎭 Add Genre", callback_data="post_edit_genre")],
        [InlineKeyboardButton("⬅️ Back to Preview", callback_data="post_back_preview")]
    ]
    await query.edit_message_caption(
        caption="✏️ <b>Edit Post</b>\n\nNote: Changes sirf is post ke liye hain. Database same rahega.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return PG_PREVIEW

async def post_edit_title_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_post_edit_title")
    await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    return PG_EDIT_TITLE

async def post_edit_title_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['post_title'] = update.message.text.strip()
    await rebuild_caption(context)
    await update.message.reply_text("✅ Title update (sirf is post ke liye).", parse_mode=ParseMode.HTML)
    return await show_post_preview(update, context)

async def post_edit_desc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_post_edit_desc")
    await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    return PG_EDIT_DESC

async def post_edit_desc_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['post_description'] = update.message.text.strip()
    await rebuild_caption(context)
    await update.message.reply_text("✅ Description update.", parse_mode=ParseMode.HTML)
    return await show_post_preview(update, context)

async def post_edit_genre_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_post_edit_genre")
    await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    return PG_EDIT_GENRE

async def post_edit_genre_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['post_genre'] = update.message.text.strip()
    await rebuild_caption(context)
    await update.message.reply_text("✅ Genre add ho gaya.", parse_mode=ParseMode.HTML)
    return await show_post_preview(update, context)

async def rebuild_caption(context):
    title = context.user_data.get('post_title', '')
    desc = context.user_data.get('post_description', '')
    genre = context.user_data.get('post_genre', '')
    caption = f"<b>{title}</b>\n\n"
    if genre:
        caption += f"<b>🎭 Genre:</b> {genre}\n\n"
    if desc:
        caption += f"<b>📖 Synopsis:</b>\n{desc}\n\n"
    caption += "Neeche Download button dabao!"
    context.user_data['post_caption_raw'] = caption

async def post_back_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await show_post_preview(update, context)

async def post_change_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_caption(
        caption="Naya Target Chat ID / @username bhejo:\n\n/cancel",
        parse_mode=ParseMode.HTML
    )
    context.user_data['waiting_temp_chat'] = True
    return PG_PREVIEW

async def post_temp_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_temp_chat'):
        chat_id = update.message.text.strip()
        context.user_data['target_chat'] = chat_id
        context.user_data['waiting_temp_chat'] = False
        await update.message.reply_text(f"✅ Target set: <code>{chat_id}</code>", parse_mode=ParseMode.HTML)
        return await show_post_preview(update, context)
    return PG_PREVIEW

async def post_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Publishing...")

    chat_id = context.user_data.get('target_chat')
    if not chat_id:
        await query.answer("Target chat set nahi hai!", show_alert=True)
        return PG_PREVIEW

    caption_raw = context.user_data.get('post_caption_raw', '')
    poster_id = context.user_data.get('post_poster_id')
    short_link = context.user_data.get('short_link')

    config = await get_config()
    links = config.get('links', {})
    bot_username = (await context.bot.get_me()).username

    keyboard = [
        [InlineKeyboardButton("Backup", url=links.get('backup') or "https://t.me/"),
         InlineKeyboardButton("Donate", url=f"https://t.me/{bot_username}?start=donate")],
        [InlineKeyboardButton("⬇️ Download", url=short_link)]
    ]

    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    caption = await apply_font_formatting(caption_raw, font_settings)

    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=poster_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        text = await format_message(context, "admin_post_gen_success", {"chat_id": chat_id})
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Publish error: {e}")
        text = await format_message(context, "admin_post_gen_error", {"chat_id": chat_id, "e": str(e)})
        await query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML)

    context.user_data.clear()
    await asyncio.sleep(2)
    await admin_command(update, context, from_callback=True)
    return ConversationHandler.END

# ============================================================
# ===              GENERATE LINK + OTHER MENUS             ===
# ============================================================
async def gen_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔗 Generate Link", callback_data="gen_link_movie")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_gen_link")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return GL_MENU

async def gen_link_select_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    return await gen_link_show_list(update, context, 0)

async def gen_link_show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    query = update.callback_query
    if query.data.startswith("genlink_page_"):
        page = int(query.data.split("_")[-1])
        await query.answer()
    items, keyboard = await build_paginated_keyboard(
        movies_collection, page, "genlink_page_", "gen_link_movie_", "admin_gen_link"
    )
    text = await format_message(context, "admin_gen_link_select_movie", {"page": page+1}) if items else await format_message(context, "admin_gen_link_no_movie")
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    return GL_GET_MOVIE

async def gen_link_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace("gen_link_movie_", "")
    try:
        bot_username = (await context.bot.get_me()).username
        doc = movies_collection.find_one({"name": name})
        link = f"https://t.me/{bot_username}?start=dl{str(doc['_id'])}"
        text = await format_message(context, "admin_gen_link_success", {"title": name, "final_link": link})
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]]))
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", parse_mode=ParseMode.HTML)
    return ConversationHandler.END

# ==================== DONATE / LINKS / DELETE TIME ====================
async def donate_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    status = "✅" if config.get('donate_qr_id') else "❌"
    keyboard = [
        [InlineKeyboardButton(f"Set Donate QR {status}", callback_data="admin_set_donate_qr")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_donate")
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def other_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    links = config.get('links', {})
    keyboard = [
        [InlineKeyboardButton(f"Backup {'✅' if links.get('backup') else '❌'}", callback_data="admin_set_backup_link")],
        [InlineKeyboardButton(f"Download {'✅' if links.get('download') else '❌'}", callback_data="admin_set_download_link")],
        [InlineKeyboardButton(f"Help {'✅' if links.get('help') else '❌'}", callback_data="admin_set_help_link")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_links")
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def set_donate_qr_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_set_donate_qr_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return CD_GET_QR

async def set_donate_qr_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Photo bhejo.", parse_mode=ParseMode.HTML)
        return CD_GET_QR
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"donate_qr_id": update.message.photo[-1].file_id}}, upsert=True)
    text = await format_message(context, "admin_set_donate_qr_success")
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await donate_settings_menu(update, context)
    return ConversationHandler.END

async def set_links_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if "backup" in data:
        context.user_data['link_type'] = "backup"
        text = await format_message(context, "admin_set_link_backup")
    elif "download" in data:
        context.user_data['link_type'] = "download"
        text = await format_message(context, "admin_set_link_download")
    else:
        context.user_data['link_type'] = "help"
        text = await format_message(context, "admin_set_link_help")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return CL_GET_LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_type = context.user_data['link_type']
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"links.{link_type}": update.message.text.strip()}}, upsert=True)
    text = await format_message(context, "admin_set_link_success", {"link_type": link_type})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await other_links_menu(update, context)
    return ConversationHandler.END

async def skip_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_type = context.user_data['link_type']
    config_collection.update_one({"_id": "bot_config"}, {"$set": {f"links.{link_type}": None}}, upsert=True)
    text = await format_message(context, "admin_set_link_skip", {"link_type": link_type})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await other_links_menu(update, context)
    return ConversationHandler.END

async def set_delete_time_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    sec = config.get("delete_seconds", 300)
    text = await format_message(context, "admin_set_delete_time_start", {
        "current_minutes": sec // 60, "current_seconds": sec
    })
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return CS_GET_DELETE_TIME

async def set_delete_time_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        seconds = int(update.message.text.strip())
        if seconds < 30:
            await update.message.reply_text("Minimum 30 seconds rakho.", parse_mode=ParseMode.HTML)
            return CS_GET_DELETE_TIME
        config_collection.update_one({"_id": "bot_config"}, {"$set": {"delete_seconds": seconds}}, upsert=True)
        text = await format_message(context, "admin_set_delete_time_success", {
            "seconds": seconds, "minutes": seconds // 60
        })
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        await admin_command(update, context, from_callback=False)
        return ConversationHandler.END
    except:
        text = await format_message(context, "admin_set_delete_time_nan")
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return CS_GET_DELETE_TIME

# ==================== DEFAULT CHANNEL + LANGUAGE ====================
async def admin_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    keyboard = [
        [InlineKeyboardButton("➕ Add Co-Admin", callback_data="admin_add_co_admin")],
        [InlineKeyboardButton("🚫 Remove Co-Admin", callback_data="admin_remove_co_admin")],
        [InlineKeyboardButton("👥 List Co-Admins", callback_data="admin_list_co_admin")],
        [InlineKeyboardButton("📢 Default Publish Channel", callback_data="admin_default_channel")],
        [InlineKeyboardButton("🌐 Bot Language", callback_data="admin_language_menu")],
        [InlineKeyboardButton("🚀 Custom Post", callback_data="admin_custom_post")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast_start")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_admin_settings")
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def default_channel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = config.get("default_publish_chat") or "Not set"
    keyboard = [
        [InlineKeyboardButton("✏️ Set Default", callback_data="admin_set_default_channel")],
        [InlineKeyboardButton("🗑️ Clear", callback_data="admin_clear_default_channel")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    text = await format_message(context, "admin_default_channel_menu", {"current": current})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def set_default_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = await format_message(context, "admin_default_channel_set_start")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return DC_SET_CHANNEL

async def set_default_channel_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.text.strip()
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"default_publish_chat": chat_id}}, upsert=True)
    text = await format_message(context, "admin_default_channel_success", {"chat_id": chat_id})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

async def clear_default_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"default_publish_chat": None}})
    text = await format_message(context, "admin_default_channel_cleared")
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(1.5)
    await admin_settings_menu(update, context)

async def language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    config = await get_config()
    current = config.get("language", "hinglish").title()
    keyboard = [
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hindi")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_english")],
        [InlineKeyboardButton("🇧🇩 Bengali", callback_data="lang_bengali")],
        [InlineKeyboardButton("🇮🇳 Hinglish", callback_data="lang_hinglish")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_settings")]
    ]
    text = await format_message(context, "admin_language_menu", {"lang": current})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return LANG_MENU

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.replace("lang_", "")
    await query.answer(f"Language → {lang}")
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"language": lang}}, upsert=True)
    # Refresh default messages for new language
    defaults = await get_default_messages(lang)
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"messages": defaults}})
    text = await format_message(context, "admin_language_set_success", {"lang": lang.title()})
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(1.5)
    await admin_settings_menu(update, context)
    return ConversationHandler.END

# ==================== APPEARANCE (Real Blockquote) ====================
async def appearance_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    config = await get_config()
    app = config.get("appearance", {})
    font = app.get("font", "default")
    style = app.get("style", "normal")
    quote = "ON" if app.get("quote_enabled") else "OFF"
    keyboard = [
        [InlineKeyboardButton(f"🖋️ Font: {font}", callback_data="app_set_font"),
         InlineKeyboardButton(f"✍️ Style: {style}", callback_data="app_set_style")],
        [InlineKeyboardButton(f"📌 Quote (blockquote): {quote}", callback_data="app_toggle_quote")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_menu")]
    ]
    text = await format_message(context, "admin_menu_appearance", {
        "font": font, "style": style, "quote": quote
    })
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_MENU

async def appearance_set_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fonts = ["default", "small_caps", "sans_serif", "sans_serif_bold"]
    buttons = [InlineKeyboardButton(f.title().replace("_", " "), callback_data=f"app_font_{f}") for f in fonts]
    keyboard = build_grid_keyboard(buttons, 2)
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_appearance")])
    text = await format_message(context, "admin_appearance_select_font", {"font": "current"})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_FONT

async def appearance_save_font(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    font = query.data.replace("app_font_", "")
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"appearance.font": font}}, upsert=True)
    await query.answer(f"Font → {font}")
    await appearance_menu_start(update, context)
    return AP_MENU

async def appearance_set_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("Normal", callback_data="app_style_normal"),
         InlineKeyboardButton("Bold", callback_data="app_style_bold")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_appearance")]
    ]
    text = await format_message(context, "admin_appearance_select_style", {"style": "current"})
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    return AP_STYLE

async def appearance_save_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    style = query.data.replace("app_style_", "")
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"appearance.style": style}}, upsert=True)
    await query.answer(f"Style → {style}")
    await appearance_menu_start(update, context)
    return AP_MENU

async def appearance_toggle_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    config = await get_config()
    current = config.get("appearance", {}).get("quote_enabled", False)
    new_val = not current
    config_collection.update_one({"_id": "bot_config"}, {"$set": {"appearance.quote_enabled": new_val}}, upsert=True)
    status = "ON" if new_val else "OFF"
    await query.answer(f"Quote {status}")
    text = await format_message(context, "admin_appearance_quote_toggle", {"status": status})
    await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    await appearance_menu_start(update, context)
    return AP_MENU

# ==================== USER SIDE + DOWNLOAD ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    full_name = user.full_name

    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"first_name": user.first_name, "full_name": full_name, "username": user.username},
         "$inc": {"interaction_count": 1}},
        upsert=True
    )

    args = context.args
    if args:
        payload = " ".join(args)
        if payload.startswith("dl"):
            await handle_deep_link_download(user, context, payload)
            return
        elif payload == "donate":
            await handle_deep_link_donate(user, context)
            return

    if await is_co_admin(user_id):
        text = await format_message(context, "user_welcome_admin")
    else:
        text = await format_message(context, "user_welcome_basic", {"full_name": full_name})
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await increment_user_interaction(update.effective_user.id)
    await show_user_menu(update, context)

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    user = update.effective_user
    config = await get_config()
    links = config.get('links', {})
    keyboard = [
        [InlineKeyboardButton("Backup", url=links.get('backup') or "https://t.me/"),
         InlineKeyboardButton("Donate", callback_data="user_show_donate_menu")],
        [InlineKeyboardButton("🆘 Help", url=links.get('help') or "https://t.me/")]
    ]
    text = await format_message(context, "user_menu_greeting", {"full_name": user.full_name})
    photo = config.get("user_menu_photo_id")

    if from_callback:
        query = update.callback_query
        await query.answer()
        try:
            if photo:
                await context.bot.send_photo(user.id, photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(user.id, text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except:
            pass
    else:
        if photo:
            await update.message.reply_photo(photo=photo, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def user_show_donate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await increment_user_interaction(query.from_user.id)
    config = await get_config()
    qr = config.get('donate_qr_id')
    if not qr:
        await query.answer(await format_message(context, "user_donate_qr_error"), show_alert=True)
        return
    text = await format_message(context, "user_donate_qr_text")
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="user_back_menu")]]
    try:
        await context.bot.send_photo(query.from_user.id, photo=qr, caption=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        await query.answer()
        context.job_queue.run_once(send_donate_thank_you, 60, chat_id=query.from_user.id)
    except Exception as e:
        await query.answer("Error", show_alert=True)

async def handle_deep_link_donate(user, context):
    await increment_user_interaction(user.id)
    config = await get_config()
    qr = config.get('donate_qr_id')
    if not qr:
        await context.bot.send_message(user.id, await format_message(context, "user_donate_qr_error"), parse_mode=ParseMode.HTML)
        return
    text = await format_message(context, "user_donate_qr_text")
    await context.bot.send_photo(user.id, photo=qr, caption=text, parse_mode=ParseMode.HTML)
    context.job_queue.run_once(send_donate_thank_you, 60, chat_id=user.id)

async def handle_deep_link_download(user, context, payload):
    await increment_user_interaction(user.id)
    class Dummy:
        def __init__(self, u, d):
            self.from_user = u
            self.data = d
            self.message = type('obj', (object,), {'chat': type('obj', (object,), {'id': u.id, 'type': 'private'})(), 'photo': None})()
        async def answer(self, *a, **k): pass
    class DummyUpdate:
        def __init__(self, u, d):
            self.callback_query = Dummy(u, d)
            self.effective_user = u
    try:
        await download_button_handler(DummyUpdate(user, payload), context)
    except Exception as e:
        logger.error(f"Deep link fail: {e}")

async def download_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    await increment_user_interaction(user_id)
    config = await get_config()

    try:
        await query.answer()
    except:
        pass

    checking = None
    try:
        checking = await context.bot.send_message(user_id, await format_message(context, "user_dl_fetching"), parse_mode=ParseMode.HTML)
    except:
        return

    parts = query.data.split("__")
    key = parts[0].replace("dl", "")
    quality = parts[1] if len(parts) > 1 else None

    try:
        doc = movies_collection.find_one({"_id": ObjectId(key)})
    except:
        doc = movies_collection.find_one({"name": key})

    if not doc:
        await context.bot.send_message(user_id, await format_message(context, "user_dl_movie_not_found"), parse_mode=ParseMode.HTML)
        if checking: await context.bot.delete_message(user_id, checking.message_id)
        return

    name = doc['name']
    mid = str(doc['_id'])
    delete_time = config.get("delete_seconds", 300)

    if quality:
        if checking: 
            try: await context.bot.delete_message(user_id, checking.message_id)
            except: pass

        file_id = None
        if doc.get("type") == "series":
            seasons = doc.get("seasons", [])
            if seasons and seasons[0].get("episodes"):
                file_id = seasons[0]["episodes"][0].get("qualities", {}).get(quality)
        else:
            file_id = doc.get("qualities", {}).get(quality)

        if not file_id:
            await context.bot.send_message(user_id, await format_message(context, "user_dl_file_error", {"quality": quality}), parse_mode=ParseMode.HTML)
            return

        warning = await format_message(context, "file_warning", {"minutes": max(1, delete_time//60)})
        caption = f"🎬 <b>{name}</b> ({quality})\n\n{warning}"
        caption = await apply_font_formatting(caption, config.get("appearance", {}))

        try:
            sent = await context.bot.send_video(user_id, video=file_id, caption=caption, parse_mode=ParseMode.HTML, thumbnail=doc.get("poster_id"))
            asyncio.create_task(delete_message_later(context.bot, user_id, sent.message_id, delete_time))
        except Exception as e:
            err = "user_dl_blocked_error" if "blocked" in str(e).lower() else "user_dl_file_error"
            await context.bot.send_message(user_id, await format_message(context, err, {"quality": quality}), parse_mode=ParseMode.HTML)
        return

    # Show qualities
    if doc.get("type") == "series":
        seasons = doc.get("seasons", [])
        qualities = seasons[0]["episodes"][0].get("qualities", {}) if seasons and seasons[0].get("episodes") else {}
    else:
        qualities = doc.get("qualities", {})

    if not qualities:
        if checking: await context.bot.delete_message(user_id, checking.message_id)
        await context.bot.send_message(user_id, await format_message(context, "user_dl_qualities_not_found"), parse_mode=ParseMode.HTML)
        return

    buttons = [InlineKeyboardButton(q, callback_data=f"dl{mid}__{q}") for q in ['480p', '720p', '1080p', '4K'] if q in qualities]
    keyboard = build_grid_keyboard(buttons, 2)
    keyboard.append([InlineKeyboardButton("⬅️ Menu", callback_data="user_back_menu")])
    msg = await format_message(context, "user_dl_select_quality", {"movie_name": name})

    if checking:
        try: await context.bot.delete_message(user_id, checking.message_id)
        except: pass

    try:
        sent = await context.bot.send_photo(user_id, photo=doc['poster_id'], caption=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        asyncio.create_task(delete_message_later(context.bot, user_id, sent.message_id, delete_time))
    except:
        pass

# ==================== MAIN + HANDLERS ====================
async def error_handler(update, context):
    logger.error(f"Error: {context.error}", exc_info=True)

app = Flask(__name__)
bot_app = None
bot_loop = None

@app.route('/')
def home():
    return "Bot is alive!", 200

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    global bot_app, bot_loop
    if request.is_json:
        update = Update.de_json(request.get_json(), bot_app.bot)
        asyncio.run_coroutine_threadsafe(bot_app.process_update(update), bot_loop)
        return "OK", 200
    return "Bad", 400

def run_async_bot_tasks(loop, application):
    global bot_loop
    bot_loop = loop
    asyncio.set_event_loop(loop)
    try:
        with httpx.Client() as client:
            client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/{BOT_TOKEN}")
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.start())
        logger.info("Bot started!")
        loop.run_forever()
    except Exception as e:
        logger.error(f"Bot fail: {e}")
    finally:
        loop.run_until_complete(application.stop())
        loop.close()

def main():
    global bot_app
    PORT = int(os.environ.get("PORT", 8080))
    bot_app = Application.builder().token(BOT_TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML)).build()

    global_cancel = CommandHandler("cancel", cancel)
    fallbacks = [CommandHandler("start", cancel), CommandHandler("menu", cancel), CommandHandler("admin", cancel), global_cancel]

    # Conversation Handlers (shortened registration for clarity)
    add_movie_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_movie_start, pattern="^admin_add_movie$")],
        states={
            M_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_get_name)],
            M_GET_POSTER: [MessageHandler(filters.PHOTO, add_movie_get_poster)],
            M_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_get_desc), CommandHandler("skip", add_movie_skip_desc)],
            M_GET_480P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_480p), CommandHandler("skip", add_movie_skip_480p)],
            M_GET_720P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_720p), CommandHandler("skip", add_movie_skip_720p)],
            M_GET_1080P: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_1080p), CommandHandler("skip", add_movie_skip_1080p)],
            M_GET_4K: [MessageHandler(filters.ALL & ~filters.COMMAND, add_movie_get_4k), CommandHandler("skip", add_movie_skip_4k)],
            M_CONFIRM: [CallbackQueryHandler(save_movie, pattern="^save_movie$")]
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_add_content, pattern="^back_to_add_content$")],
        allow_reentry=True
    )

    add_series_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_series_start, pattern="^admin_add_series$")],
        states={
            S_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_series_get_name)],
            S_GET_POSTER: [MessageHandler(filters.PHOTO, add_series_get_poster)],
            S_GET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_series_get_desc), CommandHandler("skip", add_series_skip_desc)],
            S_GET_EPISODE: [
                MessageHandler(filters.ALL & ~filters.COMMAND, add_series_get_episode_file),
                CommandHandler("new_season", add_series_new_season),
                CommandHandler("done", add_series_done)
            ],
            S_CONFIRM: [CallbackQueryHandler(save_series, pattern="^save_series$")]
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_add_content, pattern="^back_to_add_content$")],
        allow_reentry=True
    )

    add_ep_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_episode_start, pattern="^admin_add_episode$")],
        states={
            ADD_EP_SELECT: [
                CallbackQueryHandler(add_episode_show_list, pattern="^addep_page_"),
                CallbackQueryHandler(add_episode_select_series, pattern="^addep_series_")
            ],
            ADD_EP_GET_FILE: [
                MessageHandler(filters.ALL & ~filters.COMMAND, add_episode_get_file),
                CommandHandler("done", add_episode_done)
            ]
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_add_content, pattern="^back_to_add_content$")],
        allow_reentry=True
    )

    post_gen_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(post_gen_menu, pattern="^admin_post_gen$")],
        states={
            PG_MENU: [CallbackQueryHandler(post_gen_select_movie, pattern="^post_gen_movie$")],
            PG_GET_MOVIE: [
                CallbackQueryHandler(post_gen_show_list, pattern="^postgen_page_"),
                CallbackQueryHandler(post_gen_ask_shortlink, pattern="^post_movie_")
            ],
            PG_GET_SHORT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_gen_get_short_link)],
            PG_PREVIEW: [
                CallbackQueryHandler(post_publish, pattern="^post_publish$"),
                CallbackQueryHandler(post_edit_menu, pattern="^post_edit_menu$"),
                CallbackQueryHandler(post_edit_title_start, pattern="^post_edit_title$"),
                CallbackQueryHandler(post_edit_desc_start, pattern="^post_edit_desc$"),
                CallbackQueryHandler(post_edit_genre_start, pattern="^post_edit_genre$"),
                CallbackQueryHandler(post_back_preview, pattern="^post_back_preview$"),
                CallbackQueryHandler(post_change_target, pattern="^post_change_target$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, post_temp_chat_handler)
            ],
            PG_EDIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_title_save)],
            PG_EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_desc_save)],
            PG_EDIT_GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, post_edit_genre_save)],
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_admin_menu, pattern="^admin_menu$")],
        allow_reentry=True
    )

    # Register everything
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("user", user_command))
    bot_app.add_handler(CommandHandler("menu", admin_command))
    bot_app.add_handler(CommandHandler("admin", admin_command))

    bot_app.add_handler(CallbackQueryHandler(add_content_menu, pattern="^admin_menu_add_content$"))
    bot_app.add_handler(CallbackQueryHandler(manage_content_menu, pattern="^admin_menu_manage_content$"))
    bot_app.add_handler(CallbackQueryHandler(edit_content_menu, pattern="^admin_menu_edit_content$"))
    bot_app.add_handler(CallbackQueryHandler(donate_settings_menu, pattern="^admin_menu_donate_settings$"))
    bot_app.add_handler(CallbackQueryHandler(other_links_menu, pattern="^admin_menu_other_links$"))
    bot_app.add_handler(CallbackQueryHandler(admin_settings_menu, pattern="^admin_menu_admin_settings$"))
    bot_app.add_handler(CallbackQueryHandler(default_channel_menu, pattern="^admin_default_channel$"))
    bot_app.add_handler(CallbackQueryHandler(clear_default_channel, pattern="^admin_clear_default_channel$"))
    bot_app.add_handler(CallbackQueryHandler(appearance_menu_start, pattern="^admin_menu_appearance$"))
    bot_app.add_handler(CallbackQueryHandler(user_show_donate_menu, pattern="^user_show_donate_menu$"))
    bot_app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern="^user_back_menu$"))
    bot_app.add_handler(CallbackQueryHandler(download_button_handler, pattern="^dl"))

    bot_app.add_handler(add_movie_conv)
    bot_app.add_handler(add_series_conv)
    bot_app.add_handler(add_ep_conv)
    bot_app.add_handler(post_gen_conv)

    # Remaining simple handlers (delete, edit, gen link, etc.)
    delete_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(delete_movie_start, pattern="^admin_del_movie$")],
        states={
            DA_GET_MOVIE: [CallbackQueryHandler(delete_movie_show_list, pattern="^delmovie_page_"), CallbackQueryHandler(delete_movie_confirm, pattern="^del_movie_")],
            DA_CONFIRM: [CallbackQueryHandler(delete_movie_do, pattern="^del_movie_confirm_yes$")]
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_manage, pattern="^back_to_manage$")],
        allow_reentry=True
    )
    bot_app.add_handler(delete_conv)

    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_movie_start, pattern="^admin_edit_movie$")],
        states={
            EA_GET_MOVIE: [CallbackQueryHandler(edit_movie_show_list, pattern="^editmovie_page_"), CallbackQueryHandler(edit_movie_get_new_name, pattern="^edit_movie_")],
            EA_GET_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_movie_save)],
            EA_CONFIRM: [CallbackQueryHandler(edit_movie_do, pattern="^edit_movie_confirm_yes$")]
        },
        fallbacks=fallbacks + [CallbackQueryHandler(back_to_edit_menu, pattern="^back_to_edit_menu$")],
        allow_reentry=True
    )
    bot_app.add_handler(edit_conv)

    gen_link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(gen_link_menu, pattern="^admin_gen_link$")],
        states={
            GL_MENU: [CallbackQueryHandler(gen_link_select_movie, pattern="^gen_link_movie$")],
            GL_GET_MOVIE: [CallbackQueryHandler(gen_link_show_list, pattern="^genlink_page_"), CallbackQueryHandler(gen_link_finish, pattern="^gen_link_movie_")]
        },
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(gen_link_conv)

    set_donate_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_donate_qr_start, pattern="^admin_set_donate_qr$")],
        states={CD_GET_QR: [MessageHandler(filters.PHOTO, set_donate_qr_save)]},
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(set_donate_conv)

    set_links_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_links_start, pattern="^admin_set_")],
        states={CL_GET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link), CommandHandler("skip", skip_link)]},
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(set_links_conv)

    set_time_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_delete_time_start, pattern="^admin_set_delete_time$")],
        states={CS_GET_DELETE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_delete_time_save)]},
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(set_time_conv)

    default_ch_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(set_default_channel_start, pattern="^admin_set_default_channel$")],
        states={DC_SET_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_default_channel_save)]},
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(default_ch_conv)

    lang_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(language_menu, pattern="^admin_language_menu$")],
        states={LANG_MENU: [CallbackQueryHandler(set_language, pattern="^lang_")]},
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(lang_conv)

    appearance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(appearance_menu_start, pattern="^admin_menu_appearance$")],
        states={
            AP_MENU: [
                CallbackQueryHandler(appearance_set_font, pattern="^app_set_font$"),
                CallbackQueryHandler(appearance_set_style, pattern="^app_set_style$"),
                CallbackQueryHandler(appearance_toggle_quote, pattern="^app_toggle_quote$")
            ],
            AP_FONT: [CallbackQueryHandler(appearance_save_font, pattern="^app_font_"), CallbackQueryHandler(back_to_appearance, pattern="^back_to_appearance$")],
            AP_STYLE: [CallbackQueryHandler(appearance_save_style, pattern="^app_style_"), CallbackQueryHandler(back_to_appearance, pattern="^back_to_appearance$")]
        },
        fallbacks=fallbacks,
        allow_reentry=True
    )
    bot_app.add_handler(appearance_conv)

    bot_app.add_error_handler(error_handler)

    # Start
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=run_async_bot_tasks, args=(loop, bot_app))
    t.start()
    serve(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
