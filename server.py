import asyncio
import threading
import httpx
from flask import Flask, request
from waitress import serve
from telegram import Update
from config import BOT_TOKEN, WEBHOOK_URL, PORT, logger

class PerUserLocks:
    """Webhook requests stay fast while one user's conversation stays ordered."""
    def __init__(self):
        self._locks = {}

    async def run(self, update: Update, callback):
        key = update.effective_user.id if update.effective_user else 0
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            await callback()

class WebhookRuntime:
    """A Waitress/Flask front end with PTB on one dedicated asyncio loop."""
    def __init__(self, application):
        self.application = application
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, name="telegram-async-loop", daemon=True)
        self.web = Flask(__name__)
        self.locks = PerUserLocks()
        
        @self.web.route('/', methods=['GET'])
        def health():
            return "Prime Bot Webhook Server is Online & Active!", 200
            
        @self.web.route(f"/{BOT_TOKEN}", methods=['POST'])
        def telegram_webhook():
            payload = request.get_json(silent=True)
            if payload:
                update = Update.de_json(payload, self.application.bot)
                asyncio.run_coroutine_threadsafe(self._process(update), self.loop)
            return "OK", 200

    async def _process(self, update: Update):
        try:
            await self.locks.run(update, lambda: self.application.process_update(update))
        except Exception as e:
            logger.error(f"Telegram update failed: {e}")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._startup())
        self.loop.run_forever()

    async def _startup(self):
        await self.application.initialize()
        await self.application.start()
        
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

    def start(self):
        self.thread.start()
        logger.info(f"🚀 Starting Waitress Web Server on port {PORT}...")
        serve(self.web, host='0.0.0.0', port=PORT, threads=12)

def start_webhook_server(application):
    runtime = WebhookRuntime(application)
    runtime.start()
