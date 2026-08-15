import logging
from telegram.ext import Application, CommandHandler

# Import everything from our modular files
from config import BOT_TOKEN, logger
from server import start_webhook_server
from user_handlers import start_command

# Yahan par tu apne baki conversation handlers import karega jo picchle parts me the.
# Example: 
# from admin_add import add_movie_conv, add_series_conv
# from admin_post import post_gen_conv
# from admin_core import admin_command, cancel_handler

def main():
    logger.info("🚀 Initializing Prime Level Bot Architecture...")
    
    # Built exactly like the original working bot to prevent weakref crashes
    bot_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(15)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .connection_pool_size(32)
        .build()
    )

    # 1. REGISTER BASIC COMMANDS
    bot_app.add_handler(CommandHandler("start", start_command))
    
    # 2. REGISTER ADMIN & CONVERSATION HANDLERS
    # bot_app.add_handler(CommandHandler(["admin", "menu"], admin_command))
    # bot_app.add_handler(add_movie_conv)
    # bot_app.add_handler(add_series_conv)
    # bot_app.add_handler(post_gen_conv)

    # 3. START WEBHOOK SERVER
    logger.info("🌐 Handlers registered. Handing over to Webhook Server...")
    start_webhook_server(bot_app)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually by user.")
    except Exception as e:
        logger.critical(f"❌ Fatal error in main.py: {e}")
