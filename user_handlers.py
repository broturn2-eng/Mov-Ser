from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
# FIX: Imported 'content_col' directly to match database.py
from database import content_col, track_user, is_co_admin
from messages import format_message
from bson.objectid import ObjectId
from config import ADMIN_ID, logger
import asyncio

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await track_user(user.id, user.first_name, user.full_name, user.username)
    
    args = context.args
    # Agar user deep link se aaya hai (e.g., t.me/bot?start=dl_12345)
    if args and args[0].startswith("dl_"):
        await handle_deep_link(update, context, args[0].replace("dl_", ""))
        return

    # Normal Start Command
    if await is_co_admin(user.id, ADMIN_ID):
        text = await format_message("user_welcome_admin")
    else:
        text = await format_message("user_welcome_basic", {"full_name": user.full_name})
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE, item_id: str):
    user_id = update.effective_user.id
    try:
        # FIX: Using 'content_col' here instead of contents_collection
        doc = content_col.find_one({"_id": ObjectId(item_id)})
    except Exception:
        doc = None
        
    if not doc:
        msg = await format_message("user_dl_movie_not_found")
        await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML)
        return

    # Movie Logic
    if doc['content_type'] == 'movie':
        qualities = doc.get('files', {})
        kb = [[InlineKeyboardButton(q, callback_data=f"send_m_{item_id}_{q}")] for q in qualities]
        msg = await format_message("user_dl_select_quality", {"title": doc['title']})
        
        if doc.get('poster_id'):
            await context.bot.send_photo(chat_id=user_id, photo=doc['poster_id'], caption=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
            
    # Series Logic
    elif doc['content_type'] == 'series':
        seasons = doc.get('seasons', [])
        kb = [[InlineKeyboardButton(s['title'], callback_data=f"sel_s_{item_id}_{s['sid']}")] for s in seasons]
        msg = f"📺 <b>{doc['title']}</b>\n\nSelect a Season:"
        
        if doc.get('poster_id'):
            await context.bot.send_photo(chat_id=user_id, photo=doc['poster_id'], caption=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(kb))
