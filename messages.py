import html
from database import get_bot_config
from fonts import apply_font_formatting
from config import logger

async def get_default_messages():
    return {
        "welcome": "Welcome, {name}! Use the buttons below.",
        "user_welcome_admin": "Salaam, Admin! Admin panel ke liye /menu use karein.",
        "user_welcome_basic": "Salaam, {full_name}! Apna user menu dekhne ke liye /user use karein.",
        "user_not_admin": "Aap admin nahi hain.",
        "user_dl_dm_alert": "✅ <f>Check your DM (private chat) with me!</f>",
        "user_dl_movie_not_found": "❌ <f>Error: Content nahi mila.</f>",
        "user_dl_file_error": "❌ <f>Error! {quality} file nahi bhej paya.</f>",
        "user_dl_fetching": "⏳ <f>Fetching files...</f>",
        "user_dl_sending_file": "✅ <b>{title}</b> | <b>{quality}</b>\n\n<f>Aapki file bhej raha hoon...</f>",
        "user_dl_select_quality": "<b>{title}</b>\n\n<f>Quality select karein:</f>",
        "file_warning": "⚠️ <b><f>Yeh file {minutes} minute(s) mein automatically delete ho jaayegi.</f></b>",
        "admin_cancel": "<f>Operation cancel kar diya gaya hai.</f>",
        "post_gen_caption": "🎬 <b>{title}</b>\n\n{description}\n\n<f>Neeche button se download karein!</f>"
    }

async def format_message(key: str, variables: dict = None) -> str:
    config = await get_bot_config()
    default_msgs = await get_default_messages()
    raw_text = config.get("messages", {}).get(key, default_msgs.get(key, f"MISSING: {key}"))
    
    if variables:
        safe_vars = {k: str(v).replace('<', '&lt;').replace('>', '&gt;') for k, v in variables.items()}
        try:
            raw_text = raw_text.format(**safe_vars)
        except Exception as e:
            logger.error(f"Message format error for key {key}: {e}")

    font_settings = config.get("appearance", {"font": "default", "style": "normal"})
    return await apply_font_formatting(raw_text, font_settings)

def quote_text(description: str, enable_quotes: bool) -> str:
    description = html.escape(description.strip(), quote=False)
    if not description:
        return ""
    if enable_quotes:
        tag = "blockquote expandable" if len(description) > 180 else "blockquote"
        return f"<{tag}>{description}</blockquote>"
    return description
