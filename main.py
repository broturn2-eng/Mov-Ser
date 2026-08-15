import logging
from telegram.ext import Application, CommandHandler, Defaults
from telegram.constants import ParseMode

# Import everything from our modular files
from config import BOT_TOKEN, logger
from server import start_webhook_server
from user_handlers import start_command

# Yahan par tu apne baki conversation handlers import karega jo maine picchle parts me diye the.
# Example: 
# from admin_add import add_movie_conv, add_series_conv
# from admin_post import post_gen_conv
# from admin_core import admin_command, cancel_handler

def main():
    logger.info("🚀 Initializing Prime Level Bot Architecture...")

    # Set HTML parsing globally so we don't have to write it every time
    defaults = Defaults(parse_mode=ParseMode.HTML)
    
    # Build the application
    bot_app = Application.builder().token(BOT_TOKEN).defaults(defaults).build()

    # ==========================================
    # 1. REGISTER BASIC COMMANDS
    # ==========================================
    bot_app.add_handler(CommandHandler("start", start_command))
    
    # ==========================================
    # 2. REGISTER ADMIN & CONVERSATION HANDLERS
    # ==========================================
    # Yahan apne saare Add Movie, Add Series, Post Generator wale handlers register kar dena.
    # bot_app.add_handler(CommandHandler("admin", admin_command))
    # bot_app.add_handler(add_movie_conv)
    # bot_app.add_handler(add_series_conv)
    # bot_app.add_handler(post_gen_conv)

    # ==========================================
    # 3. START WEBHOOK SERVER
    # ==========================================
    logger.info("🌐 Handlers registered. Handing over to Webhook Server...")
    
    # Ye function server.py se aa raha hai, jo Waitress/Flask ko port 8080 par chalayega
    # aur Telegram bot ko background async loop me start kar dega.
    start_webhook_server(bot_app)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually by user.")
    except Exception as e:
        logger.critical(f"❌ Fatal error in main.py: {e}")
