"""
Webhook server for Lava.top payment notifications.
Runs alongside the bot on the same Railway service.
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import sqlite3
import threading

from aiohttp import web

logger = logging.getLogger(__name__)

LAVA_SECRET  = os.getenv("LAVA_SECRET", "")   # Секрет из кабинета Lava.top
VIP_CHANNEL  = os.getenv("VIP_CHANNEL", "-100XXXXXXXXXX")
ADMIN_ID     = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN    = os.getenv("BOT_TOKEN", "")

# Импортируем bot из основного модуля (запускается в одном процессе)
_bot = None

def set_bot(bot_instance):
    global _bot
    _bot = bot_instance

def db_set_vip(user_id: int, status: bool):
    con = sqlite3.connect("chinatown.db")
    con.execute("UPDATE users SET is_vip=? WHERE user_id=?", (int(status), user_id))
    con.commit()
    con.close()

def verify_lava_signature(body: bytes, signature: str) -> bool:
    if not LAVA_SECRET:
        return True  # dev mode
    expected = hmac.new(LAVA_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

async def handle_webhook(request: web.Request) -> web.Response:
    body = await request.read()
    sig  = request.headers.get("X-Signature", "")

    if not verify_lava_signature(body, sig):
        logger.warning("Invalid Lava signature")
        return web.Response(status=403, text="Invalid signature")

    try:
        data = json.loads(body)
    except Exception:
        return web.Response(status=400, text="Bad JSON")

    logger.info(f"Lava webhook: {data}")

    status  = data.get("status")
    comment = data.get("comment", "")   # сюда кладём tg_USER_ID

    if status == "success" and comment.startswith("tg_"):
        try:
            user_id = int(comment.replace("tg_", ""))
            db_set_vip(user_id, True)

            if _bot:
                link = await _bot.create_chat_invite_link(VIP_CHANNEL, member_limit=1)
                await _bot.send_message(
                    user_id,
                    f"⭐️ <b>Оплата прошла! Добро пожаловать в Chinatown Black!</b>\n\n"
                    f"Твоя ссылка для входа:\n{link.invite_link}\n\n"
                    f"Ссылка одноразовая — не передавай её.",
                    parse_mode="HTML"
                )
                if ADMIN_ID:
                    await _bot.send_message(
                        ADMIN_ID,
                        f"💰 Новый VIP!\nUser ID: {user_id}\nСумма: {data.get('amount', '?')} ₽"
                    )
            logger.info(f"VIP granted to {user_id}")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")

    return web.Response(text="OK")

async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="Chinatown bot is running")

def run_webhook_server(bot_instance, port=8080):
    """Запускает webhook сервер в отдельном треде"""
    set_bot(bot_instance)
    app = web.Application()
    app.router.add_post("/webhook/lava", handle_webhook)
    app.router.add_get("/",              handle_health)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    web.run_app(app, port=port, loop=loop)
