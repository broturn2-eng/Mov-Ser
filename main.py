"""Rights-managed Movies and Web-Series Telegram bot.

Use this bot only for media that you own or are authorized to distribute.
The application is deliberately a single deployable file: copy it with
requirements.txt and .env to a Python 3.11+ host, then run ``python main.py``.
"""

from __future__ import annotations

import asyncio
import html
import logging
import os
import re
import secrets
import signal
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable, Final

from dotenv import load_dotenv
from flask import Flask, Response, abort, request
from pymongo import ASCENDING, DESCENDING, AsyncMongoClient
from pymongo.errors import DuplicateKeyError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from waitress import serve


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)
LOG = logging.getLogger("movies-series-bot")

QUALITY_OPTIONS: Final[tuple[str, ...]] = ("480p", "720p", "1080p", "4K")
PAGE_SIZE: Final[int] = 8
DESCRIPTION_PREVIEW_LIMIT: Final[int] = 850
TELEGRAM_CAPTION_LIMIT: Final[int] = 1024


def now() -> datetime:
    return datetime.now(UTC)


def object_id(value: str):
    """Convert a callback id safely without importing Mongo internals everywhere."""
    from bson import ObjectId

    return ObjectId(value)


def compact_id() -> str:
    """8 chars keeps Telegram callback_data comfortably below 64 bytes."""
    return uuid.uuid4().hex[:8]


def normalized_title(value: str) -> str:
    return " ".join(value.casefold().split())


def clean_text(value: str, *, limit: int = 3000) -> str:
    value = " ".join(value.strip().split())
    return value[:limit]


def valid_url(value: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s]{3,2048}", value.strip(), re.IGNORECASE))


def h(value: Any) -> str:
    return html.escape(str(value), quote=False)


@dataclass(frozen=True, slots=True)
class Settings:
    token: str
    mongo_uri: str
    mongo_db: str
    admin_ids: frozenset[int]
    webhook_public_url: str
    webhook_path: str
    webhook_secret: str
    port: int

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        missing: list[str] = []
        for key in ("BOT_TOKEN", "MONGO_URI", "ADMIN_IDS", "WEBHOOK_PUBLIC_URL", "WEBHOOK_SECRET"):
            if not os.getenv(key):
                missing.append(key)
        # Accept the variable names used by the user's older bot as well.
        # Render exposes only variables saved for the active service/environment,
        # so supporting both names avoids a needless breaking deployment change.
        raw_admin_ids = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID")
        public_url_value = os.getenv("WEBHOOK_PUBLIC_URL") or os.getenv("WEBHOOK_URL")
        webhook_secret = os.getenv("WEBHOOK_SECRET")
        missing = [key for key, value in (("BOT_TOKEN", os.getenv("BOT_TOKEN")), ("MONGO_URI", os.getenv("MONGO_URI")), ("ADMIN_IDS or ADMIN_ID", raw_admin_ids), ("WEBHOOK_PUBLIC_URL or WEBHOOK_URL", public_url_value)) if not value]
        if missing:
            raise RuntimeError("Missing required .env values: " + ", ".join(missing))

        # It is still best to set WEBHOOK_SECRET in Render. A fresh random
        # secret remains safe for this deployment if it is omitted; Telegram is
        # configured with the same value immediately during startup.
        if not webhook_secret:
            webhook_secret = secrets.token_urlsafe(32)
            LOG.warning("WEBHOOK_SECRET is not set; using a new secret for this process. Set it in Render for stable configuration.")

        try:
            admins = frozenset(int(item.strip()) for item in os.environ["ADMIN_IDS"].split(",") if item.strip())
            admins = frozenset(int(item.strip()) for item in raw_admin_ids.split(",") if item.strip())
        except ValueError as exc:
            raise RuntimeError("ADMIN_IDS must be comma-separated numeric Telegram user IDs") from exc
            raise RuntimeError("ADMIN_IDS/ADMIN_ID must contain numeric Telegram user IDs") from exc
        if not admins:
            raise RuntimeError("At least one ADMIN_IDS value is required")

        public_url = os.environ["WEBHOOK_PUBLIC_URL"].rstrip("/")
        public_url = public_url_value.rstrip("/")
        if not public_url.startswith("https://"):
            raise RuntimeError("WEBHOOK_PUBLIC_URL must start with https://")

        return cls(
            token=os.environ["BOT_TOKEN"],
            mongo_uri=os.environ["MONGO_URI"],
            mongo_db=os.getenv("MONGO_DB", "MoviesSeriesBot"),
            admin_ids=admins,
            webhook_public_url=public_url,
            webhook_path=os.getenv("WEBHOOK_PATH", "telegram").strip("/"),
            webhook_secret=os.environ["WEBHOOK_SECRET"],
            port=int(os.getenv("PORT", "8080")),
        )


# Every string emitted by the bot comes through tr().  User-entered content is
# not translated and is escaped before it is rendered as Telegram HTML.
EN: Final[dict[str, str]] = {
    "welcome": "Welcome, {name}! Use the buttons below.",
    "private_only": "Please open this link in the bot's private chat.",
    "not_admin": "This action is for administrators only.",
    "cancelled": "Cancelled.",
    "admin": "Admin dashboard",
    "add_content": "Add content",
    "manage": "Manage content",
    "post_generator": "Create post",
    "settings": "Settings",
    "statistics": "Statistics",
    "broadcast": "Broadcast",
    "back": "Back",
    "cancel": "Cancel",
    "add_movie": "Add movie",
    "add_series": "Add web series",
    "add_season": "Add season",
    "add_episode": "Add episode",
    "delete_season": "Delete season",
    "delete_episode": "Delete episode",
    "movies": "Movies",
    "series": "Web series",
    "choose_item": "Choose an item (page {page}).",
    "no_items": "No items found.",
    "ask_title": "Send the title.",
    "ask_poster": "Send a poster photo, or use Skip.",
    "ask_description": "Send a description, or use Skip.",
    "skip": "Skip",
    "choose_quality": "Select a quality to upload. You may add more than one, then press Done.",
    "send_file": "Send the {quality} video or document now.",
    "file_saved": "{quality} file saved.",
    "done": "Done",
    "need_file": "Add at least one file before saving.",
    "confirm_content": "Check this content before saving:\n\n<b>{title}</b>\nType: {kind}\nFiles: {files}",
    "save": "Save",
    "saved": "Saved successfully.",
    "already_exists": "A {kind} with this title already exists.",
    "choose_series": "Choose a web series.",
    "choose_season": "Choose a season.",
    "ask_season_title": "Send the season title (for example: Season 1).",
    "ask_episode_title": "Send the episode title (for example: Episode 1).",
    "edit": "Edit",
    "edit_title": "Edit title",
    "edit_description": "Edit description",
    "delete": "Delete",
    "delete_confirm": "Delete <b>{title}</b>? This cannot be undone.",
    "yes_delete": "Yes, delete",
    "deleted": "Deleted.",
    "ask_new_title": "Send the new title. This changes the stored content.",
    "ask_new_description": "Send the new stored description, or /skip to clear it.",
    "updated": "Updated.",
    "generate_link": "Generate deep link",
    "original_link": "Original Telegram link:\n<code>{link}</code>\n\nSend the shortened HTTPS link.",
    "bad_link": "Send a valid http:// or https:// link.",
    "post_edit_menu": "Before posting, edit the temporary post draft if needed. These edits will <b>not</b> change MongoDB.",
    "ask_post_title": "Send the title only for this group post. MongoDB will not be changed.",
    "ask_post_description": "Send the description only for this group post. Long descriptions are sent as a collapsible quote. MongoDB will not be changed.",
    "set_destination": "Set group/channel",
    "ask_destination": "Send the destination @channelusername or numeric chat ID.",
    "preview": "Preview",
    "publish": "Publish",
    "destination_missing": "Set a destination before publishing.",
    "published": "Post published to {chat_id}.",
    "post_failed": "Could not publish the post. Verify the bot is admin there and the ID is correct.",
    "language": "Language",
    "select_language": "Choose the bot interface language.",
    "language_saved": "Language changed to {language}.",
    "autodelete": "Auto-delete time",
    "ask_delete_seconds": "Send automatic deletion time in seconds. Send 0 to disable it.",
    "delete_seconds_saved": "Auto-delete set to {seconds} seconds.",
    "coadmins": "Co-admins",
    "add_coadmin": "Add co-admin",
    "remove_coadmin": "Remove co-admin",
    "ask_coadmin": "Send the numeric Telegram user ID of the co-admin.",
    "coadmin_saved": "Co-admin access updated.",
    "broadcast_prompt": "Send the message to broadcast. It will be copied as-is after confirmation.",
    "broadcast_confirm": "Send this message to {count} users?",
    "broadcast_sent": "Broadcast finished: {sent} sent, {failed} failed/blocked.",
    "invalid_input": "That input is not valid for this step. Use /cancel to stop.",
    "content_not_found": "This content is no longer available.",
    "select_quality": "Select quality for <b>{title}</b>.",
    "sending": "Sending your file…",
    "no_quality": "No file is available for that selection.",
    "support": "Support",
    "download": "Download",
    "whole_series": "Whole series",
    "season_post": "Season post",
    "episode_post": "Episode post",
    "next": "Next",
    "previous": "Previous",
}

# Compact translations cover every UI key through English fallback for rare
# operational errors; normal menus/prompts/buttons are fully localized.
HI: Final[dict[str, str]] = {
    "welcome": "Namaste {name}! Neeche buttons use karein.", "private_only": "Is link ko bot ke private chat mein kholiye.",
    "not_admin": "Yeh action sirf admin ke liye hai.", "cancelled": "Cancel kar diya.", "admin": "Admin dashboard",
    "add_content": "Content add karein", "manage": "Content manage karein", "post_generator": "Post banayein", "settings": "Settings",
    "statistics": "Statistics", "broadcast": "Broadcast", "back": "Wapas", "cancel": "Cancel", "add_movie": "Movie add karein",
    "add_series": "Web series add karein", "add_season": "Season add karein", "add_episode": "Episode add karein",
    "delete_season": "Season delete karein", "delete_episode": "Episode delete karein", "movies": "Movies", "series": "Web series",
    "choose_item": "Item select karein (page {page}).", "no_items": "Koi item nahi mila.", "ask_title": "Title bhejiye.",
    "ask_poster": "Poster photo bhejiye, ya Skip karein.", "ask_description": "Description bhejiye, ya Skip karein.", "skip": "Skip",
    "choose_quality": "Quality select karke file bhejiye; fir Done dabaiye.", "send_file": "Ab {quality} video ya document bhejiye.",
    "file_saved": "{quality} file save ho gayi.", "done": "Done", "need_file": "Save se pehle kam se kam ek file add karein.",
    "saved": "Safalta se save ho gaya.", "edit": "Edit", "edit_title": "Title edit", "edit_description": "Description edit", "delete": "Delete",
    "yes_delete": "Haan, delete", "deleted": "Delete ho gaya.", "updated": "Update ho gaya.", "generate_link": "Deep link banayein",
    "bad_link": "Sahi http:// ya https:// link bhejiye.", "set_destination": "Group/channel set karein", "ask_destination": "@channel username ya numeric chat ID bhejiye.",
    "preview": "Preview", "publish": "Publish", "language": "Bhasha", "select_language": "Bot ki language select karein.",
    "language_saved": "Language {language} ho gayi.", "autodelete": "Auto-delete time", "ask_delete_seconds": "Auto-delete seconds bhejiye; band ke liye 0.",
    "delete_seconds_saved": "Auto-delete {seconds} seconds par set hai.", "coadmins": "Co-admins", "add_coadmin": "Co-admin add", "remove_coadmin": "Co-admin hataayein",
    "ask_coadmin": "Co-admin ki numeric Telegram ID bhejiye.", "broadcast_prompt": "Broadcast message bhejiye.", "invalid_input": "Yeh input sahi nahi hai. Rokne ke liye /cancel.",
    "content_not_found": "Yeh content ab available nahi hai.", "select_quality": "<b>{title}</b> ki quality select karein.", "sending": "File bhej raha hoon…",
    "no_quality": "Is selection ke liye file nahi hai.", "support": "Support", "download": "Download", "whole_series": "Puri series", "season_post": "Season post", "episode_post": "Episode post",
}

HINGLISH: Final[dict[str, str]] = {
    "welcome": "Salaam {name}! Neeche buttons use karo.", "private_only": "Is link ko bot ke private chat mein kholo.",
    "not_admin": "Yeh action sirf admin ke liye hai.", "cancelled": "Operation cancel ho gaya.", "admin": "Admin panel",
    "add_content": "Add content", "manage": "Manage content", "post_generator": "Post generator", "settings": "Settings", "statistics": "Stats", "broadcast": "Broadcast",
    "back": "Back", "cancel": "Cancel", "add_movie": "Add movie", "add_series": "Add web series", "add_season": "Add season", "add_episode": "Add episode",
    "delete_season": "Delete season", "delete_episode": "Delete episode", "movies": "Movies", "series": "Web series", "choose_item": "Item choose karo (page {page}).",
    "no_items": "Abhi koi item nahi hai.", "ask_title": "Title bhejo.", "ask_poster": "Poster photo bhejo, ya Skip karo.", "ask_description": "Description bhejo, ya Skip karo.",
    "skip": "Skip", "choose_quality": "Quality choose karke file bhejo, phir Done karo.", "send_file": "Ab {quality} video ya document bhejo.",
    "file_saved": "{quality} file save ho gayi.", "done": "Done", "need_file": "Save se pehle minimum ek file add karo.", "saved": "Successfully save ho gaya.",
    "edit": "Edit", "edit_title": "Edit title", "edit_description": "Edit description", "delete": "Delete", "yes_delete": "Haan delete", "deleted": "Delete ho gaya.",
    "updated": "Update ho gaya.", "generate_link": "Generate deep link", "bad_link": "Valid http:// ya https:// link bhejo.",
    "set_destination": "Set group/channel", "ask_destination": "@channel username ya numeric chat ID bhejo.", "preview": "Preview", "publish": "Publish", "language": "Language",
    "select_language": "Bot language choose karo.", "language_saved": "Language {language} set ho gayi.", "autodelete": "Auto-delete time", "ask_delete_seconds": "Seconds bhejo; disable ke liye 0.",
    "delete_seconds_saved": "Auto-delete {seconds} seconds set hai.", "coadmins": "Co-admins", "add_coadmin": "Add co-admin", "remove_coadmin": "Remove co-admin",
    "ask_coadmin": "Co-admin ki numeric Telegram user ID bhejo.", "broadcast_prompt": "Broadcast message bhejo.", "invalid_input": "Yeh input valid nahi hai. Stop ke liye /cancel.",
    "content_not_found": "Yeh content ab available nahi hai.", "select_quality": "<b>{title}</b> quality choose karo.", "sending": "Aapki file bhej raha hoon…", "no_quality": "Iske liye file available nahi hai.",
    "support": "Support", "download": "Download", "whole_series": "Full series", "season_post": "Season post", "episode_post": "Episode post",
}

BN: Final[dict[str, str]] = {
    "welcome": "স্বাগতম {name}! নিচের বোতাম ব্যবহার করুন।", "private_only": "লিঙ্কটি বটের ব্যক্তিগত চ্যাটে খুলুন।", "not_admin": "এই কাজটি শুধু অ্যাডমিনের জন্য।",
    "cancelled": "বাতিল করা হয়েছে।", "admin": "অ্যাডমিন ড্যাশবোর্ড", "add_content": "কনটেন্ট যোগ করুন", "manage": "কনটেন্ট ম্যানেজ করুন", "post_generator": "পোস্ট তৈরি করুন", "settings": "সেটিংস",
    "statistics": "পরিসংখ্যান", "broadcast": "ব্রডকাস্ট", "back": "ফিরে যান", "cancel": "বাতিল", "add_movie": "মুভি যোগ করুন", "add_series": "ওয়েব সিরিজ যোগ করুন", "add_season": "সিজন যোগ করুন", "add_episode": "এপিসোড যোগ করুন",
    "delete_season": "সিজন মুছুন", "delete_episode": "এপিসোড মুছুন", "movies": "মুভি", "series": "ওয়েব সিরিজ", "choose_item": "আইটেম বেছে নিন (পৃষ্ঠা {page})।", "no_items": "কোনও আইটেম পাওয়া যায়নি।",
    "ask_title": "শিরোনাম পাঠান।", "ask_poster": "পোস্টার ছবি পাঠান, অথবা Skip করুন।", "ask_description": "বিবরণ পাঠান, অথবা Skip করুন।", "skip": "Skip", "done": "শেষ", "edit": "সম্পাদনা", "delete": "মুছুন", "preview": "প্রিভিউ", "publish": "প্রকাশ করুন", "language": "ভাষা", "select_language": "বটের ভাষা বেছে নিন।", "support": "সাপোর্ট", "download": "ডাউনলোড",
}

AR: Final[dict[str, str]] = {
    "welcome": "مرحباً {name}! استخدم الأزرار أدناه.", "private_only": "افتح الرابط في المحادثة الخاصة مع البوت.", "not_admin": "هذا الإجراء للمشرفين فقط.", "cancelled": "تم الإلغاء.",
    "admin": "لوحة الإدارة", "add_content": "إضافة محتوى", "manage": "إدارة المحتوى", "post_generator": "إنشاء منشور", "settings": "الإعدادات", "statistics": "الإحصاءات", "broadcast": "بث", "back": "رجوع", "cancel": "إلغاء",
    "add_movie": "إضافة فيلم", "add_series": "إضافة مسلسل", "add_season": "إضافة موسم", "add_episode": "إضافة حلقة", "delete_season": "حذف الموسم", "delete_episode": "حذف الحلقة", "movies": "الأفلام", "series": "المسلسلات",
    "choose_item": "اختر عنصراً (صفحة {page}).", "no_items": "لا توجد عناصر.", "ask_title": "أرسل العنوان.", "ask_poster": "أرسل صورة الملصق أو اختر Skip.", "ask_description": "أرسل الوصف أو اختر Skip.", "skip": "تخطي", "done": "تم", "edit": "تعديل", "delete": "حذف", "preview": "معاينة", "publish": "نشر", "language": "اللغة", "select_language": "اختر لغة البوت.", "support": "دعم", "download": "تنزيل",
}

PACKS: Final[dict[str, dict[str, str]]] = {"en": EN, "hi": HI, "hinglish": HINGLISH, "bn": BN, "ar": AR}
LANGUAGE_NAMES: Final[dict[str, str]] = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish", "bn": "Bengali", "ar": "Arabic"}


def tr(language: str, key: str, **values: Any) -> str:
    template = PACKS.get(language, EN).get(key, EN.get(key, key))
    safe = {name: h(value) for name, value in values.items()}
    try:
        return template.format(**safe)
    except (KeyError, ValueError):
        LOG.warning("Bad translation template for key %s", key)
        return EN.get(key, key)


class Store:
    """Async MongoDB access, indexes and a tiny settings cache."""

    def __init__(self, settings: Settings) -> None:
        # Native asyncio driver: Motor is deprecated and ran Mongo work through
        # a thread pool.  Keep this client on the single PTB event loop only.
        self.client = AsyncMongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000, maxPoolSize=50)
        db = self.client[settings.mongo_db]
        self.contents = db.contents
        self.users = db.users
        self.config = db.config
        self.post_log = db.post_log
        self._cached_config: dict[str, Any] | None = None
        self._cache_at = 0.0
        self._config_lock = asyncio.Lock()

    async def initialize(self) -> None:
        await self.client.admin.command("ping")
        await self.contents.create_index([("content_type", ASCENDING), ("title_key", ASCENDING)], unique=True)
        await self.contents.create_index([("content_type", ASCENDING), ("updated_at", DESCENDING)])
        await self.contents.create_index([("title", "text"), ("description", "text")])
        await self.users.create_index([("last_seen", DESCENDING)])
        await self.post_log.create_index([("created_at", DESCENDING)])
        await self.config.update_one(
            {"_id": "bot"},
            {"$setOnInsert": {"language": "hinglish", "auto_delete_seconds": 0, "co_admins": [], "support_url": ""}},
            upsert=True,
        )
        LOG.info("MongoDB indexes are ready")

    async def get_config(self, *, fresh: bool = False) -> dict[str, Any]:
        if not fresh and self._cached_config and time.monotonic() - self._cache_at < 20:
            return self._cached_config
        async with self._config_lock:
            if not fresh and self._cached_config and time.monotonic() - self._cache_at < 20:
                return self._cached_config
            config = await self.config.find_one({"_id": "bot"}) or {}
            self._cached_config = config
            self._cache_at = time.monotonic()
            return config

    async def update_config(self, values: dict[str, Any]) -> None:
        await self.config.update_one({"_id": "bot"}, {"$set": values}, upsert=True)
        self._cached_config = None

    async def touch_user(self, update: Update) -> None:
        user = update.effective_user
        if not user:
            return
        await self.users.update_one(
            {"_id": user.id},
            {"$set": {"name": user.full_name[:256], "username": user.username, "last_seen": now()}, "$setOnInsert": {"first_seen": now()}},
            upsert=True,
        )

    async def add_content(self, draft: dict[str, Any]) -> str:
        title = draft["title"]
        document = {
            "content_type": draft["content_type"],
            "title": title,
            "title_key": normalized_title(title),
            "description": draft.get("description", ""),
            "poster_file_id": draft.get("poster_file_id"),
            "files": draft.get("files", {}),
            "seasons": draft.get("seasons", []),
            "created_at": now(),
            "updated_at": now(),
            "schema_version": 2,
        }
        result = await self.contents.insert_one(document)
        return str(result.inserted_id)

    async def find_content(self, content_id: str) -> dict[str, Any] | None:
        try:
            return await self.contents.find_one({"_id": object_id(content_id)})
        except Exception:
            return None

    async def list_content(self, kind: str, page: int) -> tuple[list[dict[str, Any]], int]:
        page = max(0, page)
        total = await self.contents.count_documents({"content_type": kind})
        cursor = self.contents.find({"content_type": kind}).sort("updated_at", DESCENDING).skip(page * PAGE_SIZE).limit(PAGE_SIZE)
        return [doc async for doc in cursor], total

    async def delete_content(self, content_id: str) -> bool:
        try:
            return bool((await self.contents.delete_one({"_id": object_id(content_id)})).deleted_count)
        except Exception:
            return False

    async def update_content(self, content_id: str, values: dict[str, Any]) -> bool:
        try:
            values["updated_at"] = now()
            return bool((await self.contents.update_one({"_id": object_id(content_id)}, {"$set": values})).modified_count)
        except DuplicateKeyError:
            raise
        except Exception:
            return False

    async def add_season(self, content_id: str, season: dict[str, Any]) -> bool:
        try:
            result = await self.contents.update_one(
                {"_id": object_id(content_id), "content_type": "series"},
                {"$push": {"seasons": season}, "$set": {"updated_at": now()}},
            )
            return bool(result.modified_count)
        except Exception:
            return False

    async def add_episode(self, content_id: str, season_id: str, episode: dict[str, Any]) -> bool:
        try:
            result = await self.contents.update_one(
                {"_id": object_id(content_id), "content_type": "series"},
                {"$push": {"seasons.$[season].episodes": episode}, "$set": {"updated_at": now()}},
                array_filters=[{"season.sid": season_id}],
            )
            return bool(result.modified_count)
        except Exception:
            return False

    async def delete_season(self, content_id: str, season_id: str) -> bool:
        try:
            result = await self.contents.update_one(
                {"_id": object_id(content_id), "content_type": "series"},
                {"$pull": {"seasons": {"sid": season_id}}, "$set": {"updated_at": now()}},
            )
            return bool(result.modified_count)
        except Exception:
            return False

    async def delete_episode(self, content_id: str, season_id: str, episode_id: str) -> bool:
        try:
            result = await self.contents.update_one(
                {"_id": object_id(content_id), "content_type": "series"},
                {"$pull": {"seasons.$[season].episodes": {"eid": episode_id}}, "$set": {"updated_at": now()}},
                array_filters=[{"season.sid": season_id}],
            )
            return bool(result.modified_count)
        except Exception:
            return False


def language_of(config: dict[str, Any]) -> str:
    language = config.get("language", "hinglish")
    return language if language in PACKS else "hinglish"


def is_main_admin(settings: Settings, update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id in settings.admin_ids)


async def is_admin(store: Store, settings: Settings, update: Update) -> bool:
    if is_main_admin(settings, update):
        return True
    user = update.effective_user
    if not user:
        return False
    config = await store.get_config()
    return user.id in config.get("co_admins", [])


async def reply(update: Update, text: str, **kwargs: Any) -> Any:
    message = update.effective_message
    if not message:
        return None
    return await message.reply_text(text, parse_mode=ParseMode.HTML, **kwargs)


def keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data) for text, data in row] for row in rows])


def url_keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, url=url) for text, url in row] for row in rows])


def quote(description: str) -> str:
    description = h(description.strip())
    if not description:
        return ""
    # Telegram HTML supports expandable blockquotes in current clients.
    tag = "blockquote expandable" if len(description) > 180 else "blockquote"
    return f"<{tag}>{description}</blockquote>"


def post_caption(title: str, description: str) -> str:
    return f"<b>{h(title)}</b>\n\n{quote(description)}".strip()


def truncate_html_caption(caption: str) -> str:
    """A safe compact fallback; full text is sent in the next message."""
    if len(caption) <= TELEGRAM_CAPTION_LIMIT:
        return caption
    return caption[: DESCRIPTION_PREVIEW_LIMIT].rsplit(" ", 1)[0] + "…"


def deep_link(bot_username: str, content_id: str, season_id: str | None = None, episode_id: str | None = None) -> str:
    payload = f"d-{content_id}"
    if season_id:
        payload += f"-{season_id}"
    if episode_id:
        payload += f"-{episode_id}"
    return f"https://t.me/{bot_username}?start={payload}"


class PerUserLocks:
    """Webhook requests stay fast while one user's conversation stays ordered."""

    def __init__(self) -> None:
        self._locks: dict[int, asyncio.Lock] = {}

    async def run(self, update: Update, callback: Callable[[], Awaitable[None]]) -> None:
        key = (update.effective_user.id if update.effective_user else update.effective_chat.id if update.effective_chat else 0)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            await callback()


class MovieSeriesBot:
    """Telegram UI and workflows.  Temporary post edits live only in user_data."""

    def __init__(self, store: Store, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    async def _config_language(self) -> tuple[dict[str, Any], str]:
        config = await self.store.get_config()
        return config, language_of(config)

    async def _admin_or_notice(self, update: Update) -> tuple[dict[str, Any], str] | None:
        config, language = await self._config_language()
        if await is_admin(self.store, self.settings, update):
            return config, language
        if update.callback_query:
            await update.callback_query.answer(tr(language, "not_admin"), show_alert=True)
        else:
            await reply(update, tr(language, "not_admin"))
        return None

    @staticmethod
    def _flow(context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any] | None:
        flow = context.user_data.get("flow")
        return flow if isinstance(flow, dict) else None

    @staticmethod
    def _clear_flow(context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.pop("flow", None)

    async def _answer(self, update: Update, text: str | None = None, *, alert: bool = False) -> None:
        if update.callback_query:
            try:
                await update.callback_query.answer(text, show_alert=alert)
            except BadRequest:
                pass

    async def _send_admin_home(self, update: Update, language: str) -> None:
        buttons = keyboard([
            [(tr(language, "add_content"), "adm:add"), (tr(language, "manage"), "adm:manage")],
            [(tr(language, "post_generator"), "adm:post"), (tr(language, "generate_link"), "adm:links")],
            [(tr(language, "settings"), "adm:settings"), (tr(language, "statistics"), "adm:stats")],
            [(tr(language, "broadcast"), "adm:broadcast")],
        ])
        if update.callback_query:
            await update.callback_query.edit_message_text(f"<b>{tr(language, 'admin')}</b>", reply_markup=buttons, parse_mode=ParseMode.HTML)
        else:
            await reply(update, f"<b>{tr(language, 'admin')}</b>", reply_markup=buttons)

    async def _send_list(self, update: Update, language: str, kind: str, action: str, page: int = 0) -> None:
        docs, total = await self.store.list_content(kind, page)
        if not docs:
            text = tr(language, "no_items")
            markup = keyboard([[(tr(language, "back"), "adm:home")]])
        else:
            title = tr(language, "choose_item", page=page + 1)
            rows = [[(f"{index + page * PAGE_SIZE + 1}. {doc['title'][:45]}", f"pick:{action}:{doc['_id']}")] for index, doc in enumerate(docs)]
            nav: list[tuple[str, str]] = []
            if page:
                nav.append((f"← {tr(language, 'previous')}", f"list:{kind}:{action}:{page - 1}"))
            if (page + 1) * PAGE_SIZE < total:
                nav.append((f"{tr(language, 'next')} →", f"list:{kind}:{action}:{page + 1}"))
            if nav:
                rows.append(nav)
            rows.append([(tr(language, "back"), "adm:home")])
            text, markup = title, keyboard(rows)
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await reply(update, text, reply_markup=markup)

    async def command_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.store.touch_user(update)
        _, language = await self._config_language()
        payload = context.args[0] if context.args else ""
        if payload.startswith("d-"):
            bits = payload.split("-")
            # d-<24-char ObjectId>[-<sid>[-<eid>]]: sid/eid are fixed 8-char ids.
            if len(bits) in (2, 3, 4):
                await self._show_deep_content(update, context, bits[1], bits[2] if len(bits) > 2 else None, bits[3] if len(bits) > 3 else None)
                return
        name = update.effective_user.full_name if update.effective_user else ""
        markup = keyboard([[(tr(language, "admin"), "adm:home")]]) if await is_admin(self.store, self.settings, update) else None
        await reply(update, tr(language, "welcome", name=name), reply_markup=markup)

    async def command_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.store.touch_user(update)
        allowed = await self._admin_or_notice(update)
        if allowed:
            await self._send_admin_home(update, allowed[1])

    async def command_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self._clear_flow(context)
        _, language = await self._config_language()
        await reply(update, tr(language, "cancelled"))

    async def callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.store.touch_user(update)
        query = update.callback_query
        if not query:
            return
        data = query.data or ""
        # User download selectors are intentionally available without admin rights.
        if data.startswith("open:") or data.startswith("quality:"):
            await self._user_callback(update, context, data)
            return

        allowed = await self._admin_or_notice(update)
        if not allowed:
            return
        _, language = allowed
        await self._answer(update)
        try:
            await self._admin_callback(update, context, language, data)
        except Exception:
            LOG.exception("Unhandled admin callback: %s", data)
            await query.edit_message_text(tr(language, "invalid_input"), reply_markup=keyboard([[(tr(language, "back"), "adm:home")]]), parse_mode=ParseMode.HTML)

    async def _admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, data: str) -> None:
        query = update.callback_query
        assert query
        if data.startswith("viewaddseason:"):
            content_id = data.split(":", 1)[1]
            context.user_data["flow"] = {"mode": "add_season", "step": "title", "content_id": content_id, "draft": {"sid": compact_id(), "episodes": []}}
            await query.edit_message_text(tr(language, "ask_season_title"), parse_mode=ParseMode.HTML)
            return
        if data.startswith("viewaddepisode:"):
            content_id = data.split(":", 1)[1]
            doc = await self.store.find_content(content_id)
            if not doc:
                return
            context.user_data["flow"] = {"mode": "add_episode", "step": "select_season", "content_id": content_id}
            await self._show_season_picker(update, language, doc, "epseason")
            return
        if data.startswith("epseason:"):
            _, content_id, season_id = data.split(":", 2)
            flow = self._flow(context)
            if flow:
                flow.update({"mode": "add_episode", "step": "title", "content_id": content_id, "season_id": season_id, "draft": {"eid": compact_id(), "files": {}}})
                await query.edit_message_text(tr(language, "ask_episode_title"), parse_mode=ParseMode.HTML)
            return
        if data.startswith("delseasonpick:"):
            _, content_id, season_id = data.split(":", 2)
            doc = await self.store.find_content(content_id)
            season = self._season(doc, season_id) if doc else None
            if season:
                await query.edit_message_text(tr(language, "delete_confirm", title=season["title"]), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "yes_delete"), f"delseason:{content_id}:{season_id}")], [(tr(language, "cancel"), "adm:manage")]]))
            return
        if data.startswith("delepisodepick:"):
            _, content_id, season_id = data.split(":", 2)
            doc = await self.store.find_content(content_id)
            season = self._season(doc, season_id) if doc else None
            if not season or not season.get("episodes"):
                await query.edit_message_text(tr(language, "no_items"), parse_mode=ParseMode.HTML)
                return
            rows = [[(episode["title"][:50], f"delepisodeconfirm:{content_id}:{season_id}:{episode['eid']}")] for episode in season["episodes"]]
            rows.append([(tr(language, "back"), "adm:manage")])
            await query.edit_message_text(tr(language, "choose_item", page=1), parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))
            return
        if data.startswith("delepisodeconfirm:"):
            _, content_id, season_id, episode_id = data.split(":", 3)
            doc = await self.store.find_content(content_id)
            episode = self._episode(self._season(doc, season_id) if doc else None, episode_id)
            if episode:
                await query.edit_message_text(tr(language, "delete_confirm", title=episode["title"]), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "yes_delete"), f"delepisode:{content_id}:{season_id}:{episode_id}")], [(tr(language, "cancel"), "adm:manage")]]))
            return
        if data == "adm:home":
            self._clear_flow(context)
            await self._send_admin_home(update, language)
            return
        if data == "adm:add":
            await query.edit_message_text(
                tr(language, "add_content"), parse_mode=ParseMode.HTML,
                reply_markup=keyboard([
                    [(tr(language, "add_movie"), "add:movie"), (tr(language, "add_series"), "add:series")],
                    [(tr(language, "add_season"), "series:addseason"), (tr(language, "add_episode"), "series:addepisode")],
                    [(tr(language, "back"), "adm:home")],
                ]),
            )
            return
        if data in {"add:movie", "add:series"}:
            kind = "movie" if data.endswith("movie") else "series"
            context.user_data["flow"] = {"mode": "add_content", "step": "title", "draft": {"content_type": kind, "files": {}, "seasons": []}}
            await query.edit_message_text(tr(language, "ask_title"), parse_mode=ParseMode.HTML)
            return
        if data == "flow:skip":
            await self._skip_flow_step(update, context, language)
            return
        if data == "file:done":
            await self._finish_file_input(update, context, language)
            return
        if data.startswith("file:"):
            quality = data.split(":", 1)[1]
            flow = self._flow(context)
            if not flow or flow.get("step") != "files" or quality not in QUALITY_OPTIONS:
                return
            flow["upload_quality"] = quality
            flow["step"] = "file_upload"
            await query.edit_message_text(tr(language, "send_file", quality=quality), parse_mode=ParseMode.HTML)
            return
        if data == "add:save":
            await self._save_content(update, context, language)
            return
        if data == "series:addseason":
            context.user_data["flow"] = {"mode": "add_season", "step": "select_series"}
            await self._send_list(update, language, "series", "seasonseries")
            return
        if data == "series:addepisode":
            context.user_data["flow"] = {"mode": "add_episode", "step": "select_series"}
            await self._send_list(update, language, "series", "episodeseries")
            return
        if data == "adm:manage":
            await query.edit_message_text(
                tr(language, "manage"), parse_mode=ParseMode.HTML,
                reply_markup=keyboard([
                    [(tr(language, "movies"), "list:movie:view:0"), (tr(language, "series"), "list:series:view:0")],
                    [(tr(language, "delete_season"), "series:delseason"), (tr(language, "delete_episode"), "series:delepisode")],
                    [(tr(language, "back"), "adm:home")],
                ]),
            )
            return
        if data.startswith("list:"):
            _, kind, action, page = data.split(":", 3)
            await self._send_list(update, language, kind, action, int(page))
            return
        if data.startswith("pick:"):
            _, action, content_id = data.split(":", 2)
            await self._pick_content(update, context, language, action, content_id)
            return
        if data.startswith("view:"):
            await self._admin_view_content(update, context, language, data.split(":", 1)[1])
            return
        if data.startswith("edit:"):
            await self._edit_content_menu(update, context, language, data.split(":", 1)[1])
            return
        if data.startswith("editfield:"):
            _, field, content_id = data.split(":", 2)
            context.user_data["flow"] = {"mode": "edit_content", "step": field, "content_id": content_id}
            await query.edit_message_text(tr(language, "ask_new_title" if field == "title" else "ask_new_description"), parse_mode=ParseMode.HTML)
            return
        if data.startswith("del:"):
            content_id = data.split(":", 1)[1]
            doc = await self.store.find_content(content_id)
            if not doc:
                await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
                return
            await query.edit_message_text(tr(language, "delete_confirm", title=doc["title"]), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "yes_delete"), f"delok:{content_id}")], [(tr(language, "cancel"), f"view:{content_id}")]]))
            return
        if data.startswith("delok:"):
            await self.store.delete_content(data.split(":", 1)[1])
            await query.edit_message_text(tr(language, "deleted"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:manage")]]))
            return
        if data == "adm:links":
            await query.edit_message_text(tr(language, "generate_link"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "movies"), "list:movie:link:0"), (tr(language, "series"), "list:series:link:0")], [(tr(language, "back"), "adm:home")]]))
            return
        if data == "adm:post":
            await query.edit_message_text(tr(language, "post_generator"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "movies"), "list:movie:post:0"), (tr(language, "series"), "list:series:post:0")], [(tr(language, "back"), "adm:home")]]))
            return
        if data.startswith("posttype:"):
            _, content_id, level = data.split(":", 2)
            await self._post_type(update, context, language, content_id, level)
            return
        if data.startswith("postseason:"):
            _, content_id, season_id = data.split(":", 2)
            await self._create_post_draft(update, context, language, content_id, season_id=season_id)
            return
        if data.startswith("postepisode:"):
            _, content_id, season_id = data.split(":", 2)
            await self._post_episode_list(update, context, language, content_id, season_id)
            return
        if data.startswith("postep:"):
            _, content_id, season_id, episode_id = data.split(":", 3)
            await self._create_post_draft(update, context, language, content_id, season_id=season_id, episode_id=episode_id)
            return
        if data.startswith("post:"):
            await self._post_callback(update, context, language, data)
            return
        if data == "adm:settings":
            await self._settings_menu(update, language)
            return
        if data == "settings:language":
            rows = [[(name, f"language:{code}")] for code, name in LANGUAGE_NAMES.items()]
            rows.append([(tr(language, "back"), "adm:settings")])
            await query.edit_message_text(tr(language, "select_language"), parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))
            return
        if data.startswith("language:"):
            code = data.split(":", 1)[1]
            if code in PACKS and is_main_admin(self.settings, update):
                await self.store.update_config({"language": code})
                await query.edit_message_text(tr(code, "language_saved", language=LANGUAGE_NAMES[code]), parse_mode=ParseMode.HTML)
            return
        if data == "settings:delete":
            context.user_data["flow"] = {"mode": "set_delete", "step": "seconds"}
            await query.edit_message_text(tr(language, "ask_delete_seconds"), parse_mode=ParseMode.HTML)
            return
        if data == "settings:coadmins":
            if not is_main_admin(self.settings, update):
                await query.answer(tr(language, "not_admin"), show_alert=True)
                return
            config = await self.store.get_config()
            listed = ", ".join(str(item) for item in config.get("co_admins", [])) or "—"
            await query.edit_message_text(f"<b>{tr(language, 'coadmins')}</b>\n<code>{listed}</code>", parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "add_coadmin"), "coadmin:add"), (tr(language, "remove_coadmin"), "coadmin:remove")], [(tr(language, "back"), "adm:settings")]]))
            return
        if data.startswith("coadmin:"):
            if not is_main_admin(self.settings, update):
                return
            action = data.split(":", 1)[1]
            context.user_data["flow"] = {"mode": "coadmin", "step": action}
            await query.edit_message_text(tr(language, "ask_coadmin"), parse_mode=ParseMode.HTML)
            return
        if data == "adm:stats":
            movies, series, users = await asyncio.gather(
                self.store.contents.count_documents({"content_type": "movie"}), self.store.contents.count_documents({"content_type": "series"}), self.store.users.count_documents({}),
            )
            await query.edit_message_text(f"<b>{tr(language, 'statistics')}</b>\n\n{tr(language, 'movies')}: <b>{movies}</b>\n{tr(language, 'series')}: <b>{series}</b>\nUsers: <b>{users}</b>", parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:home")]]))
            return
        if data == "adm:broadcast":
            if not is_main_admin(self.settings, update):
                return
            context.user_data["flow"] = {"mode": "broadcast", "step": "message"}
            await query.edit_message_text(tr(language, "broadcast_prompt"), parse_mode=ParseMode.HTML)
            return
        if data == "broadcast:yes":
            await self._broadcast(update, context, language)
            return
        if data == "series:delseason":
            context.user_data["flow"] = {"mode": "delete_season", "step": "select_series"}
            await self._send_list(update, language, "series", "delseasonseries")
            return
        if data == "series:delepisode":
            context.user_data["flow"] = {"mode": "delete_episode", "step": "select_series"}
            await self._send_list(update, language, "series", "delepisodeseries")
            return
        if data.startswith("delseason:"):
            _, content_id, season_id = data.split(":", 2)
            await self.store.delete_season(content_id, season_id)
            await query.edit_message_text(tr(language, "deleted"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:manage")]]))
            return
        if data.startswith("delepisode:"):
            _, content_id, season_id, episode_id = data.split(":", 3)
            await self.store.delete_episode(content_id, season_id, episode_id)
            await query.edit_message_text(tr(language, "deleted"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:manage")]]))

    async def _pick_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, action: str, content_id: str) -> None:
        query = update.callback_query
        assert query
        doc = await self.store.find_content(content_id)
        if not doc:
            await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
            return
        flow = self._flow(context)
        if action == "view":
            await self._admin_view_content(update, context, language, content_id)
            return
        if action == "link":
            username = (await context.bot.get_me()).username
            link = deep_link(username, content_id)
            await query.edit_message_text(f"<b>{h(doc['title'])}</b>\n\n<code>{link}</code>", parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:links")]]))
            return
        if action == "post":
            if doc["content_type"] == "movie":
                await self._create_post_draft(update, context, language, content_id)
            else:
                await query.edit_message_text(
                    f"<b>{h(doc['title'])}</b>", parse_mode=ParseMode.HTML,
                    reply_markup=keyboard([
                        [(tr(language, "whole_series"), f"posttype:{content_id}:series")],
                        [(tr(language, "season_post"), f"posttype:{content_id}:season")],
                        [(tr(language, "episode_post"), f"posttype:{content_id}:episode")],
                        [(tr(language, "back"), "adm:post")],
                    ]),
                )
            return
        if action == "seasonseries" and flow:
            flow.update({"content_id": content_id, "step": "title", "draft": {"sid": compact_id(), "episodes": []}})
            await query.edit_message_text(tr(language, "ask_season_title"), parse_mode=ParseMode.HTML)
            return
        if action == "episodeseries" and flow:
            flow.update({"content_id": content_id, "step": "select_season"})
            await self._show_season_picker(update, language, doc, "epseason")
            return
        if action == "delseasonseries" and flow:
            flow.update({"content_id": content_id, "step": "select_season"})
            await self._show_season_picker(update, language, doc, "delseasonpick")
            return
        if action == "delepisodeseries" and flow:
            flow.update({"content_id": content_id, "step": "select_season"})
            await self._show_season_picker(update, language, doc, "delepisodepick")
            return

    async def _admin_view_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, content_id: str) -> None:
        query = update.callback_query
        assert query
        doc = await self.store.find_content(content_id)
        if not doc:
            await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
            return
        kind = tr(language, "movies" if doc["content_type"] == "movie" else "series")
        if doc["content_type"] == "movie":
            detail = f"Files: {len(doc.get('files', {}))}"
        else:
            episodes = sum(len(season.get("episodes", [])) for season in doc.get("seasons", []))
            detail = f"Seasons: {len(doc.get('seasons', []))} | Episodes: {episodes}"
        caption = f"<b>{h(doc['title'])}</b>\n{kind}\n{detail}\n\n{quote(doc.get('description', ''))}"
        rows = [[(tr(language, "edit"), f"edit:{content_id}"), (tr(language, "delete"), f"del:{content_id}")]]
        if doc["content_type"] == "series":
            rows.append([(tr(language, "add_season"), f"viewaddseason:{content_id}"), (tr(language, "add_episode"), f"viewaddepisode:{content_id}")])
        rows.append([(tr(language, "back"), f"list:{doc['content_type']}:view:0")])
        await query.edit_message_text(caption[:4000], parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))

    async def _edit_content_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, content_id: str) -> None:
        query = update.callback_query
        assert query
        doc = await self.store.find_content(content_id)
        if not doc:
            await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
            return
        await query.edit_message_text(
            f"<b>{h(doc['title'])}</b>", parse_mode=ParseMode.HTML,
            reply_markup=keyboard([
                [(tr(language, "edit_title"), f"editfield:title:{content_id}"), (tr(language, "edit_description"), f"editfield:description:{content_id}")],
                [(tr(language, "back"), f"view:{content_id}")],
            ]),
        )

    async def _file_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, *, edit: bool = False) -> None:
        flow = self._flow(context)
        if not flow:
            return
        files = flow.get("draft", {}).get("files", {})
        rows: list[list[tuple[str, str]]] = []
        for quality in QUALITY_OPTIONS:
            marker = " ✅" if quality in files else ""
            rows.append([(f"{quality}{marker}", f"file:{quality}")])
        rows.append([(tr(language, "done"), "file:done")])
        text = tr(language, "choose_quality")
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))
        else:
            await reply(update, text, reply_markup=keyboard(rows))

    async def _skip_flow_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        query = update.callback_query
        assert query
        flow = self._flow(context)
        if not flow:
            return
        draft = flow.setdefault("draft", {})
        step = flow.get("step")
        if step == "poster":
            draft["poster_file_id"] = None
            flow["step"] = "description"
            await query.edit_message_text(tr(language, "ask_description"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
        elif step == "description":
            draft["description"] = ""
            if flow["mode"] == "add_content" and draft["content_type"] == "movie":
                flow["step"] = "files"
                await self._file_menu(update, context, language, edit=True)
            else:
                await self._show_save_confirmation(update, context, language)
        elif step == "episode_description":
            draft["description"] = ""
            flow["step"] = "files"
            await self._file_menu(update, context, language, edit=True)
        else:
            await query.answer(tr(language, "invalid_input"), show_alert=True)

    async def _finish_file_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        query = update.callback_query
        assert query
        flow = self._flow(context)
        if not flow:
            return
        files = flow.get("draft", {}).get("files", {})
        if not files:
            await query.answer(tr(language, "need_file"), show_alert=True)
            return
        await self._show_save_confirmation(update, context, language)

    async def _show_save_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        query = update.callback_query
        assert query
        flow = self._flow(context)
        if not flow:
            return
        draft = flow.get("draft", {})
        mode = flow.get("mode")
        if mode == "add_content":
            kind = draft["content_type"]
            count = len(draft.get("files", {})) if kind == "movie" else 0
        elif mode == "add_season":
            kind, count = "season", 0
        else:
            kind, count = "episode", len(draft.get("files", {}))
        title = draft.get("title", "")
        await query.edit_message_text(
            tr(language, "confirm_content", title=title, kind=kind, files=count), parse_mode=ParseMode.HTML,
            reply_markup=keyboard([[(tr(language, "save"), "add:save")], [(tr(language, "cancel"), "adm:home")]]),
        )

    async def _save_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        query = update.callback_query
        assert query
        flow = self._flow(context)
        if not flow:
            return
        draft = flow.get("draft", {})
        mode = flow.get("mode")
        try:
            if mode == "add_content":
                await self.store.add_content(draft)
            elif mode == "add_season":
                season = {"sid": draft["sid"], "title": draft["title"], "description": draft.get("description", ""), "poster_file_id": draft.get("poster_file_id"), "episodes": []}
                if not await self.store.add_season(flow["content_id"], season):
                    raise RuntimeError("series update failed")
            elif mode == "add_episode":
                episode = {"eid": draft["eid"], "title": draft["title"], "description": draft.get("description", ""), "files": draft.get("files", {})}
                if not await self.store.add_episode(flow["content_id"], flow["season_id"], episode):
                    raise RuntimeError("season update failed")
            else:
                return
        except DuplicateKeyError:
            kind = draft.get("content_type", "content")
            await query.answer(tr(language, "already_exists", kind=kind), show_alert=True)
            return
        except Exception:
            LOG.exception("Could not save content")
            await query.answer(tr(language, "invalid_input"), show_alert=True)
            return
        self._clear_flow(context)
        await query.edit_message_text(tr(language, "saved"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "add_content"), "adm:add"), (tr(language, "admin"), "adm:home")]]))

    async def _show_season_picker(self, update: Update, language: str, doc: dict[str, Any], prefix: str) -> None:
        query = update.callback_query
        assert query
        seasons = doc.get("seasons", [])
        if not seasons:
            await query.edit_message_text(tr(language, "no_items"), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "back"), "adm:add")]]))
            return
        rows = [[(season["title"][:50], f"{prefix}:{doc['_id']}:{season['sid']}")] for season in seasons]
        rows.append([(tr(language, "back"), "adm:home")])
        await query.edit_message_text(tr(language, "choose_season"), parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))

    @staticmethod
    def _season(doc: dict[str, Any] | None, season_id: str) -> dict[str, Any] | None:
        if not doc:
            return None
        return next((item for item in doc.get("seasons", []) if item.get("sid") == season_id), None)

    @staticmethod
    def _episode(season: dict[str, Any] | None, episode_id: str) -> dict[str, Any] | None:
        if not season:
            return None
        return next((item for item in season.get("episodes", []) if item.get("eid") == episode_id), None)

    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.store.touch_user(update)
        # Ordinary user messages have no bot flow; ignore them rather than
        # replying "not admin" to every chat message.
        flow = self._flow(context)
        if not flow:
            return
        allowed = await self._admin_or_notice(update)
        if not allowed:
            return
        _, language = allowed
        if not update.effective_message:
            return
        message = update.effective_message
        text = message.text or ""
        if text == "/skip":
            await self._skip_message_step(update, context, language)
            return
        mode, step = flow.get("mode"), flow.get("step")
        try:
            if mode == "add_content":
                await self._message_add_content(update, context, language, flow)
            elif mode == "add_season":
                await self._message_add_season(update, context, language, flow)
            elif mode == "add_episode":
                await self._message_add_episode(update, context, language, flow)
            elif mode == "edit_content":
                await self._message_edit_content(update, context, language, flow)
            elif mode == "post":
                await self._message_post(update, context, language, flow)
            elif mode == "set_delete" and step == "seconds":
                await self._message_delete_seconds(update, context, language, text)
            elif mode == "coadmin":
                await self._message_coadmin(update, context, language, flow, text)
            elif mode == "broadcast" and step == "message":
                await self._message_broadcast_confirm(update, context, language)
            else:
                await reply(update, tr(language, "invalid_input"))
        except Exception:
            LOG.exception("Unhandled admin message in %s/%s", mode, step)
            await reply(update, tr(language, "invalid_input"))

    async def _message_add_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any]) -> None:
        message = update.effective_message
        assert message
        draft = flow["draft"]
        if flow["step"] == "title":
            title = clean_text(message.text or "", limit=160)
            if not title:
                await reply(update, tr(language, "ask_title"))
                return
            draft["title"] = title
            flow["step"] = "poster"
            await reply(update, tr(language, "ask_poster"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
            return
        if flow["step"] == "poster":
            if not message.photo:
                await reply(update, tr(language, "ask_poster"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
                return
            draft["poster_file_id"] = message.photo[-1].file_id
            flow["step"] = "description"
            await reply(update, tr(language, "ask_description"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
            return
        if flow["step"] == "description":
            draft["description"] = (message.text or "").strip()[:3000]
            if draft["content_type"] == "movie":
                flow["step"] = "files"
                await self._file_menu(update, context, language)
            else:
                await reply(update, tr(language, "confirm_content", title=draft["title"], kind="series", files=0), reply_markup=keyboard([[(tr(language, "save"), "add:save")], [(tr(language, "cancel"), "adm:home")]]))
            return
        if flow["step"] == "file_upload":
            reference = self._media_reference(message)
            if not reference:
                await reply(update, tr(language, "send_file", quality=flow["upload_quality"]))
                return
            draft["files"][flow["upload_quality"]] = reference
            flow["step"] = "files"
            await reply(update, tr(language, "file_saved", quality=flow["upload_quality"]))
            await self._file_menu(update, context, language)

    async def _message_add_season(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any]) -> None:
        message = update.effective_message
        assert message
        draft = flow["draft"]
        if flow["step"] == "title":
            title = clean_text(message.text or "", limit=160)
            if not title:
                await reply(update, tr(language, "ask_season_title"))
                return
            draft["title"] = title
            flow["step"] = "poster"
            await reply(update, tr(language, "ask_poster"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
            return
        if flow["step"] == "poster":
            if not message.photo:
                await reply(update, tr(language, "ask_poster"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
                return
            draft["poster_file_id"] = message.photo[-1].file_id
            flow["step"] = "description"
            await reply(update, tr(language, "ask_description"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
            return
        if flow["step"] == "description":
            draft["description"] = (message.text or "").strip()[:3000]
            await reply(update, tr(language, "confirm_content", title=draft["title"], kind="season", files=0), reply_markup=keyboard([[(tr(language, "save"), "add:save")], [(tr(language, "cancel"), "adm:home")]]))

    async def _message_add_episode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any]) -> None:
        message = update.effective_message
        assert message
        draft = flow["draft"]
        if flow["step"] == "title":
            title = clean_text(message.text or "", limit=160)
            if not title:
                await reply(update, tr(language, "ask_episode_title"))
                return
            draft["title"] = title
            flow["step"] = "episode_description"
            await reply(update, tr(language, "ask_description"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
            return
        if flow["step"] == "episode_description":
            draft["description"] = (message.text or "").strip()[:3000]
            flow["step"] = "files"
            await self._file_menu(update, context, language)
            return
        if flow["step"] == "file_upload":
            reference = self._media_reference(message)
            if not reference:
                await reply(update, tr(language, "send_file", quality=flow["upload_quality"]))
                return
            draft["files"][flow["upload_quality"]] = reference
            flow["step"] = "files"
            await reply(update, tr(language, "file_saved", quality=flow["upload_quality"]))
            await self._file_menu(update, context, language)

    @staticmethod
    def _media_reference(message: Any) -> dict[str, Any] | None:
        if message.video:
            media = message.video
            return {"kind": "video", "file_id": media.file_id, "file_name": media.file_name or "video", "file_size": media.file_size or 0}
        if message.document:
            media = message.document
            return {"kind": "document", "file_id": media.file_id, "file_name": media.file_name or "file", "file_size": media.file_size or 0}
        return None

    async def _skip_message_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        flow = self._flow(context)
        if not flow:
            return
        draft = flow.get("draft", {})
        step = flow.get("step")
        if step == "poster":
            draft["poster_file_id"] = None
            flow["step"] = "description"
            await reply(update, tr(language, "ask_description"), reply_markup=keyboard([[(tr(language, "skip"), "flow:skip")]]))
        elif step in {"description", "episode_description"} and flow["mode"] != "post":
            draft["description"] = ""
            if flow["mode"] == "add_content" and draft.get("content_type") == "series" or flow["mode"] == "add_season":
                # Text message has no callback to edit; reuse the normal confirmation sender.
                await reply(update, tr(language, "confirm_content", title=draft.get("title", ""), kind="series" if flow["mode"] == "add_content" else "season", files=0), reply_markup=keyboard([[(tr(language, "save"), "add:save")], [(tr(language, "cancel"), "adm:home")]]))
            else:
                flow["step"] = "files"
                await self._file_menu(update, context, language)
        elif flow["mode"] == "post" and step == "description":
            # /skip here means retain the database description in the temporary draft.
            self._clear_flow(context)
            await self._post_menu(update, context, language)
        elif flow["mode"] == "edit_content" and step == "description":
            await self._save_edit(context, language, update, flow, "")
        else:
            await reply(update, tr(language, "invalid_input"))

    async def _message_edit_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any]) -> None:
        value = clean_text(update.effective_message.text or "", limit=160) if flow["step"] == "title" else (update.effective_message.text or "").strip()[:3000]
        if flow["step"] == "title" and not value:
            await reply(update, tr(language, "ask_new_title"))
            return
        await self._save_edit(context, language, update, flow, value)

    async def _save_edit(self, context: ContextTypes.DEFAULT_TYPE, language: str, update: Update, flow: dict[str, Any], value: str) -> None:
        field = flow["step"]
        changes: dict[str, Any] = {field: value}
        if field == "title":
            changes["title_key"] = normalized_title(value)
        try:
            changed = await self.store.update_content(flow["content_id"], changes)
        except DuplicateKeyError:
            await reply(update, tr(language, "already_exists", kind="content"))
            return
        self._clear_flow(context)
        await reply(update, tr(language, "updated") if changed else tr(language, "content_not_found"))

    async def _settings_menu(self, update: Update, language: str) -> None:
        query = update.callback_query
        assert query
        rows = [[(tr(language, "language"), "settings:language"), (tr(language, "autodelete"), "settings:delete")]]
        if is_main_admin(self.settings, update):
            rows.append([(tr(language, "coadmins"), "settings:coadmins")])
        rows.append([(tr(language, "back"), "adm:home")])
        await query.edit_message_text(f"<b>{tr(language, 'settings')}</b>", parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))

    async def _message_delete_seconds(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, text: str) -> None:
        try:
            seconds = int(text.strip())
            if not 0 <= seconds <= 604800:
                raise ValueError
        except ValueError:
            await reply(update, tr(language, "ask_delete_seconds"))
            return
        await self.store.update_config({"auto_delete_seconds": seconds})
        self._clear_flow(context)
        await reply(update, tr(language, "delete_seconds_saved", seconds=seconds))

    async def _message_coadmin(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any], text: str) -> None:
        try:
            user_id = int(text.strip())
            if user_id <= 0:
                raise ValueError
        except ValueError:
            await reply(update, tr(language, "ask_coadmin"))
            return
        config = await self.store.get_config(fresh=True)
        current = set(config.get("co_admins", []))
        if flow["step"] == "add" and user_id not in self.settings.admin_ids:
            current.add(user_id)
        elif flow["step"] == "remove":
            current.discard(user_id)
        await self.store.update_config({"co_admins": sorted(current)})
        self._clear_flow(context)
        await reply(update, tr(language, "coadmin_saved"))

    async def _message_broadcast_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        message = update.effective_message
        assert message
        count = await self.store.users.count_documents({})
        context.user_data["broadcast_source"] = {"chat_id": message.chat_id, "message_id": message.message_id}
        context.user_data["flow"] = {"mode": "broadcast", "step": "confirm"}
        await reply(update, tr(language, "broadcast_confirm", count=count), reply_markup=keyboard([[(tr(language, "publish"), "broadcast:yes")], [(tr(language, "cancel"), "adm:home")]]))

    async def _broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        query = update.callback_query
        assert query
        source = context.user_data.get("broadcast_source")
        if not source:
            await query.answer(tr(language, "invalid_input"), show_alert=True)
            return
        sent = failed = 0
        cursor = self.store.users.find({}, {"_id": 1})
        async for user in cursor:
            try:
                await context.bot.copy_message(chat_id=user["_id"], from_chat_id=source["chat_id"], message_id=source["message_id"])
                sent += 1
            except RetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after) + 0.5)
                try:
                    await context.bot.copy_message(chat_id=user["_id"], from_chat_id=source["chat_id"], message_id=source["message_id"])
                    sent += 1
                except TelegramError:
                    failed += 1
            except (Forbidden, BadRequest, TelegramError):
                failed += 1
        self._clear_flow(context)
        context.user_data.pop("broadcast_source", None)
        await query.edit_message_text(tr(language, "broadcast_sent", sent=sent, failed=failed), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "admin"), "adm:home")]]))

    async def _post_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, content_id: str, level: str) -> None:
        doc = await self.store.find_content(content_id)
        query = update.callback_query
        assert query
        if not doc:
            await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
            return
        if level == "series":
            await self._create_post_draft(update, context, language, content_id)
        elif level == "season":
            await self._show_season_picker(update, language, doc, "postseason")
        elif level == "episode":
            await self._show_season_picker(update, language, doc, "postepisode")

    async def _post_episode_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, content_id: str, season_id: str) -> None:
        query = update.callback_query
        assert query
        doc = await self.store.find_content(content_id)
        season = self._season(doc, season_id)
        if not season or not season.get("episodes"):
            await query.edit_message_text(tr(language, "no_items"), parse_mode=ParseMode.HTML)
            return
        rows = [[(episode["title"][:50], f"postep:{content_id}:{season_id}:{episode['eid']}")] for episode in season["episodes"]]
        rows.append([(tr(language, "back"), "adm:post")])
        await query.edit_message_text(tr(language, "choose_item", page=1), parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))

    async def _create_post_draft(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, content_id: str, season_id: str | None = None, episode_id: str | None = None) -> None:
        query = update.callback_query
        assert query
        doc = await self.store.find_content(content_id)
        if not doc:
            await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
            return
        title, description = doc["title"], doc.get("description", "")
        poster = doc.get("poster_file_id")
        if season_id:
            season = self._season(doc, season_id)
            if not season:
                await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
                return
            title = f"{doc['title']} — {season['title']}"
            description = season.get("description") or description
            poster = season.get("poster_file_id") or poster
        if episode_id:
            episode = self._episode(self._season(doc, season_id or ""), episode_id)
            if not episode:
                await query.edit_message_text(tr(language, "content_not_found"), parse_mode=ParseMode.HTML)
                return
            title = f"{title} — {episode['title']}"
            description = episode.get("description") or description
        bot_username = (await context.bot.get_me()).username
        original_link = deep_link(bot_username, content_id, season_id, episode_id)
        # This is deliberately session-only.  No title/description below is persisted.
        context.user_data["post_draft"] = {
            "content_id": content_id,
            "season_id": season_id,
            "episode_id": episode_id,
            "title": title,
            "description": description,
            "poster_file_id": poster,
            "original_link": original_link,
            "short_link": "",
            "destination": "",
        }
        context.user_data["flow"] = {"mode": "post", "step": "short_link"}
        await query.edit_message_text(tr(language, "original_link", link=original_link), parse_mode=ParseMode.HTML)

    async def _post_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, data: str) -> None:
        query = update.callback_query
        assert query
        draft = context.user_data.get("post_draft")
        if not isinstance(draft, dict):
            await query.answer(tr(language, "invalid_input"), show_alert=True)
            return
        if data == "post:edittitle":
            context.user_data["flow"] = {"mode": "post", "step": "title"}
            await query.edit_message_text(tr(language, "ask_post_title"), parse_mode=ParseMode.HTML)
            return
        if data == "post:editdescription":
            context.user_data["flow"] = {"mode": "post", "step": "description"}
            await query.edit_message_text(tr(language, "ask_post_description"), parse_mode=ParseMode.HTML)
            return
        if data == "post:destination":
            context.user_data["flow"] = {"mode": "post", "step": "destination"}
            await query.edit_message_text(tr(language, "ask_destination"), parse_mode=ParseMode.HTML)
            return
        if data == "post:preview":
            await self._deliver_draft(context, draft, update.effective_chat.id, preview=True)
            await query.answer(tr(language, "preview"))
            return
        if data == "post:publish":
            if not draft.get("destination"):
                await query.answer(tr(language, "destination_missing"), show_alert=True)
                return
            try:
                await self._deliver_draft(context, draft, draft["destination"], preview=False)
                # Audit contains ids/destination only: it never stores temporary edited text.
                await self.store.post_log.insert_one({"content_id": draft["content_id"], "destination": draft["destination"], "created_at": now()})
                destination = draft["destination"]
                self._clear_flow(context)
                context.user_data.pop("post_draft", None)
                await query.edit_message_text(tr(language, "published", chat_id=destination), parse_mode=ParseMode.HTML, reply_markup=keyboard([[(tr(language, "admin"), "adm:home")]]))
            except TelegramError:
                LOG.exception("Post publish failed")
                await query.answer(tr(language, "post_failed"), show_alert=True)
            return
        if data == "post:cancel":
            self._clear_flow(context)
            context.user_data.pop("post_draft", None)
            await self._send_admin_home(update, language)

    async def _post_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
        draft = context.user_data.get("post_draft")
        if not isinstance(draft, dict):
            return
        destination = draft.get("destination") or "—"
        text = f"{tr(language, 'post_edit_menu')}\n\n<b>{h(draft['title'])}</b>\nDestination: <code>{h(destination)}</code>"
        markup = keyboard([
            [(tr(language, "edit_title"), "post:edittitle"), (tr(language, "edit_description"), "post:editdescription")],
            [(tr(language, "set_destination"), "post:destination")],
            [(tr(language, "preview"), "post:preview"), (tr(language, "publish"), "post:publish")],
            [(tr(language, "cancel"), "post:cancel")],
        ])
        await reply(update, text, reply_markup=markup)

    async def _message_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, language: str, flow: dict[str, Any]) -> None:
        draft = context.user_data.get("post_draft")
        if not isinstance(draft, dict):
            self._clear_flow(context)
            return
        value = (update.effective_message.text or "").strip()
        step = flow["step"]
        if step == "short_link":
            if not valid_url(value):
                await reply(update, tr(language, "bad_link"))
                return
            draft["short_link"] = value
            # Required post-only edit stage: this does not write the content document.
            flow["step"] = "description"
            await reply(update, tr(language, "ask_post_description") + "\n\n/skip = keep original description")
            return
        elif step == "title":
            value = clean_text(value, limit=160)
            if not value:
                await reply(update, tr(language, "ask_post_title"))
                return
            draft["title"] = value
        elif step == "description":
            draft["description"] = value[:3000]
        elif step == "destination":
            if not (value.startswith("@") or re.fullmatch(r"-?\d{5,20}", value)):
                await reply(update, tr(language, "ask_destination"))
                return
            draft["destination"] = value
        else:
            return
        self._clear_flow(context)
        await self._post_menu(update, context, language)

    async def _deliver_draft(self, context: ContextTypes.DEFAULT_TYPE, draft: dict[str, Any], chat_id: int | str, *, preview: bool) -> None:
        config = await self.store.get_config()
        rows: list[list[tuple[str, str]]] = [(tr(language_of(config), "download"), draft["short_link"])]
        support_url = config.get("support_url", "")
        if valid_url(support_url):
            rows.append((tr(language_of(config), "support"), support_url))
        markup = url_keyboard([rows])
        caption = post_caption(draft["title"], draft.get("description", ""))
        long_caption = len(caption) > TELEGRAM_CAPTION_LIMIT
        compact_caption = f"<b>{h(draft['title'])}</b>" if long_caption else caption
        if draft.get("poster_file_id"):
            sent = await context.bot.send_photo(chat_id=chat_id, photo=draft["poster_file_id"], caption=compact_caption, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            sent = await context.bot.send_message(chat_id=chat_id, text=compact_caption, parse_mode=ParseMode.HTML, reply_markup=markup)
        if long_caption and draft.get("description"):
            # The full description remains an expandable quote, linked to the poster.
            await context.bot.send_message(chat_id=chat_id, text=quote(draft["description"]), parse_mode=ParseMode.HTML, reply_to_message_id=sent.message_id)

    async def _show_deep_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE, content_id: str, season_id: str | None, episode_id: str | None) -> None:
        _, language = await self._config_language()
        doc = await self.store.find_content(content_id)
        if not doc:
            await reply(update, tr(language, "content_not_found"))
            return
        if doc["content_type"] == "movie":
            await self._send_user_card(update, language, doc, callback=f"open:{content_id}:m")
            return
        if not season_id:
            seasons = doc.get("seasons", [])
            if not seasons:
                await reply(update, tr(language, "no_items"))
                return
            rows = [[(season["title"][:50], f"open:{content_id}:{season['sid']}")] for season in seasons]
            await reply(update, f"<b>{h(doc['title'])}</b>\n\n{quote(doc.get('description', ''))}", reply_markup=keyboard(rows))
            return
        season = self._season(doc, season_id)
        if not season:
            await reply(update, tr(language, "content_not_found"))
            return
        if not episode_id:
            episodes = season.get("episodes", [])
            if not episodes:
                await reply(update, tr(language, "no_items"))
                return
            rows = [[(episode["title"][:50], f"open:{content_id}:{season_id}:{episode['eid']}")] for episode in episodes]
            await reply(update, f"<b>{h(doc['title'])} — {h(season['title'])}</b>", reply_markup=keyboard(rows))
            return
        episode = self._episode(season, episode_id)
        if not episode:
            await reply(update, tr(language, "content_not_found"))
            return
        title = f"{doc['title']} — {season['title']} — {episode['title']}"
        rows = [[(quality, f"quality:{content_id}:{season_id}:{episode_id}:{quality}")] for quality in episode.get("files", {})]
        await reply(update, tr(language, "select_quality", title=title), reply_markup=keyboard(rows))

    async def _send_user_card(self, update: Update, language: str, doc: dict[str, Any], callback: str) -> None:
        caption = post_caption(doc["title"], doc.get("description", ""))
        if len(caption) > TELEGRAM_CAPTION_LIMIT:
            caption = f"<b>{h(doc['title'])}</b>"
        markup = keyboard([[(tr(language, "download"), callback)]])
        try:
            if doc.get("poster_file_id"):
                await update.effective_message.reply_photo(doc["poster_file_id"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=markup)
            else:
                await reply(update, caption, reply_markup=markup)
        except TelegramError:
            await reply(update, f"<b>{h(doc['title'])}</b>", reply_markup=markup)

    async def _user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        query = update.callback_query
        assert query
        _, language = await self._config_language()
        await self._answer(update)
        if data.startswith("open:"):
            parts = data.split(":")
            content_id = parts[1]
            doc = await self.store.find_content(content_id)
            if not doc:
                await query.answer(tr(language, "content_not_found"), show_alert=True)
                return
            if doc["content_type"] == "movie":
                rows = [[(quality, f"quality:{content_id}:m:{quality}")] for quality in doc.get("files", {})]
                await query.edit_message_reply_markup(reply_markup=keyboard(rows))
                return
            season_id = parts[2] if len(parts) > 2 else None
            episode_id = parts[3] if len(parts) > 3 else None
            season = self._season(doc, season_id or "")
            if not season:
                await query.answer(tr(language, "content_not_found"), show_alert=True)
                return
            if not episode_id:
                rows = [[(episode["title"][:50], f"open:{content_id}:{season_id}:{episode['eid']}")] for episode in season.get("episodes", [])]
                await query.edit_message_text(f"<b>{h(doc['title'])} — {h(season['title'])}</b>", parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))
                return
            episode = self._episode(season, episode_id)
            if not episode:
                return
            rows = [[(quality, f"quality:{content_id}:{season_id}:{episode_id}:{quality}")] for quality in episode.get("files", {})]
            await query.edit_message_text(tr(language, "select_quality", title=episode["title"]), parse_mode=ParseMode.HTML, reply_markup=keyboard(rows))
            return
        if data.startswith("quality:"):
            if update.effective_chat.type != "private":
                await query.answer(tr(language, "private_only"), show_alert=True)
                return
            parts = data.split(":")
            content_id = parts[1]
            doc = await self.store.find_content(content_id)
            if not doc:
                await query.answer(tr(language, "content_not_found"), show_alert=True)
                return
            reference: dict[str, Any] | None = None
            title = doc["title"]
            if len(parts) == 4 and parts[2] == "m":
                reference = doc.get("files", {}).get(parts[3])
            elif len(parts) == 5:
                season = self._season(doc, parts[2])
                episode = self._episode(season, parts[3])
                reference = episode.get("files", {}).get(parts[4]) if episode else None
                if season and episode:
                    title = f"{title} — {season['title']} — {episode['title']}"
            if not reference:
                await query.answer(tr(language, "no_quality"), show_alert=True)
                return
            await query.answer(tr(language, "sending"))
            try:
                if reference.get("kind") == "video":
                    sent = await context.bot.send_video(chat_id=update.effective_chat.id, video=reference["file_id"], caption=h(title), parse_mode=ParseMode.HTML)
                else:
                    sent = await context.bot.send_document(chat_id=update.effective_chat.id, document=reference["file_id"], caption=h(title), parse_mode=ParseMode.HTML)
                config = await self.store.get_config()
                seconds = int(config.get("auto_delete_seconds", 0) or 0)
                if seconds:
                    asyncio.create_task(self._delete_later(context, sent.chat_id, sent.message_id, seconds))
            except RetryAfter as exc:
                await query.answer(f"Try again in {int(float(exc.retry_after)) + 1}s", show_alert=True)
            except TelegramError:
                LOG.exception("File send failed")
                await query.answer(tr(language, "no_quality"), show_alert=True)

    @staticmethod
    async def _delete_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, seconds: int) -> None:
        await asyncio.sleep(seconds)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramError:
            pass


class WebhookRuntime:
    """A Waitress/Flask front end with PTB on one dedicated asyncio loop."""

    def __init__(self, settings: Settings, service: MovieSeriesBot, application: Application) -> None:
        self.settings = settings
        self.service = service
        self.application = application
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.stop_requested: asyncio.Event | None = None
        self.locks = PerUserLocks()
        self.thread = threading.Thread(target=self._run_loop, name="telegram-async-loop", daemon=True)
        self.web = Flask(__name__)
        self._configure_routes()

    def _configure_routes(self) -> None:
        @self.web.get("/")
        def health() -> Response:
            return Response("ok", status=200, mimetype="text/plain")

        @self.web.post(f"/{self.settings.webhook_path}")
        def telegram_webhook() -> Response:
            supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not secrets.compare_digest(supplied, self.settings.webhook_secret):
                abort(403)
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                abort(400)
            try:
                update = Update.de_json(payload, self.application.bot)
                asyncio.run_coroutine_threadsafe(self._process(update), self.loop)
            except Exception:
                LOG.exception("Webhook payload could not be scheduled")
                abort(400)
            # Telegram only needs a quick acknowledgement; the event loop does the work.
            return Response("OK", status=200, mimetype="text/plain")

    async def _process(self, update: Update) -> None:
        try:
            await self.locks.run(update, lambda: self.application.process_update(update))
        except Exception:
            LOG.exception("Telegram update failed")

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._startup())
        self.loop.run_until_complete(self.stop_requested.wait())
        self.loop.run_until_complete(self._shutdown())
        self.loop.close()

    async def _startup(self) -> None:
        await self.service.store.initialize()
        await self.application.initialize()
        await self.application.start()
        url = f"{self.settings.webhook_public_url}/{self.settings.webhook_path}"
        await self.application.bot.set_webhook(
            url=url,
            secret_token=self.settings.webhook_secret,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )
        self.stop_requested = asyncio.Event()
        LOG.info("Webhook registered at %s", url)
        self.ready.set()

    async def _shutdown(self) -> None:
        try:
            await self.application.bot.delete_webhook(drop_pending_updates=False)
        finally:
            await self.application.stop()
            await self.application.shutdown()
            await self.service.store.client.close()

    def start(self) -> None:
        self.thread.start()
        if not self.ready.wait(timeout=30):
            raise RuntimeError("Bot startup timed out; inspect logs for MongoDB or Telegram errors")

    def stop(self) -> None:
        if self.stop_requested is not None and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.stop_requested.set)
            self.thread.join(timeout=20)


def build_application(service: MovieSeriesBot, settings: Settings) -> Application:
    app = (
        Application.builder()
        .token(settings.token)
        .connect_timeout(15)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .connection_pool_size(32)
        .build()
    )
    app.add_handler(CommandHandler("start", service.command_start))
    app.add_handler(CommandHandler("admin", service.command_admin))
    app.add_handler(CommandHandler("menu", service.command_admin))
    app.add_handler(CommandHandler("cancel", service.command_cancel))
    app.add_handler(CallbackQueryHandler(service.callback))
    app.add_handler(MessageHandler(filters.ALL, service.message))
    return app


def main() -> None:
    settings = Settings.from_environment()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", settings.webhook_secret):
        raise RuntimeError("WEBHOOK_SECRET may only contain letters, digits, _ and -")
    store = Store(settings)
    service = MovieSeriesBot(store, settings)
    runtime = WebhookRuntime(settings, service, build_application(service, settings))
    runtime.start()

    def close(_signal: int, _frame: Any) -> None:
        runtime.stop()

    signal.signal(signal.SIGINT, close)
    signal.signal(signal.SIGTERM, close)
    LOG.info("Waitress listening on port %s", settings.port)
    try:
        serve(runtime.web, host="0.0.0.0", port=settings.port, threads=12)
    finally:
        runtime.stop()


if __name__ == "__main__":
    main()
