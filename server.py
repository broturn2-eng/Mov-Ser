import asyncio
import threading
import httpx
from flask import Flask, request
from waitress import serve
from telegram import Update
from config import BOT_TOKEN, WEBHOOK_URL, PORT, logger

app = Flask(__name__)
bot_app = None
bot_loop = None

@app.route('/')
def home():
    return "Prime Bot Webhook Server is Online & Active!", 200

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.is_json:
        update_data = request.get_json()
        update = Update.de_json(update_data, bot_app.bot)
        # Send update to the async event loop safely
        asyncio.run_coroutine_threadsafe(bot_app.process_update(update), bot_loop)
        return "OK", 200
    return "Bad Request", 400

def start_webhook_server(application):
    global bot_app, bot_loop
    bot_app = application
    bot_loop = asyncio.new_event_loop()
    
    def run_bot_async(loop, app_instance):
        asyncio.set_event_loop(loop)
        
        # Set Webhook automatically on startup
        if WEBHOOK_URL:
            url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
            try:
                response = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={url}")
                if response.status_code == 200:
                    logger.info(f"✅ Webhook successfully connected to: {url}")
                else:
                    logger.error(f"❌ Webhook connection failed: {response.text}")
            except Exception as e:
                logger.error(f"❌ Failed to set webhook: {e}")
        
        # Start Telegram Application in background
        loop.run_until_complete(app_instance.initialize())
        loop.run_until_complete(app_instance.start())
        loop.run_forever()

    # Start the bot's event loop in a separate thread
    threading.Thread(target=run_bot_async, args=(bot_loop, bot_app), daemon=True).start()
    
    # Start the high-performance Waitress server
    logger.info(f"🚀 Starting Waitress Web Server on port {PORT}...")
    serve(app, host='0.0.0.0', port=PORT)
