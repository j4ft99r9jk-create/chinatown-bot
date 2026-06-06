"""
Entry point: запускает бота и webhook-сервер в одном процессе.
"""
import asyncio
import threading
import logging
import os

from bot import bot, dp, db_init
from webhook_server import run_webhook_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

PORT = int(os.getenv("PORT", 8080))

async def start_bot():
    db_init()
    logging.info("Chinatown bot starting polling...")
    await dp.start_polling(bot)

def start_server():
    run_webhook_server(bot, port=PORT)

if __name__ == "__main__":
    # Запускаем webhook в отдельном треде
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Бот в главном треде
    asyncio.run(start_bot())
