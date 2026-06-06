import asyncio
import logging
import sqlite3
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── ENV ──────────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
LAVA_TOP_URL  = os.getenv("LAVA_TOP_URL", "https://lava.top/YOUR_LINK")
VIP_CHANNEL   = os.getenv("VIP_CHANNEL", "-100XXXXXXXXXX")   # ID закрытого канала
ADMIN_ID      = int(os.getenv("ADMIN_ID", "0"))
VIP_PRICE     = os.getenv("VIP_PRICE", "2 990")              # для отображения

# Ссылки на разделы форума/каналов (замени когда создашь)
LINKS = {
    "cargo":     os.getenv("LINK_CARGO",     "https://t.me/+PLACEHOLDER_CARGO"),
    "buyers":    os.getenv("LINK_BUYERS",    "https://t.me/+PLACEHOLDER_BUYERS"),
    "suppliers": os.getenv("LINK_SUPPLIERS", "https://t.me/+PLACEHOLDER_SUPPLIERS"),
    "exchange":  os.getenv("LINK_EXCHANGE",  "https://t.me/+PLACEHOLDER_EXCHANGE"),
    "visas":     os.getenv("LINK_VISAS",     "https://t.me/+PLACEHOLDER_VISAS"),
    "hotels":    os.getenv("LINK_HOTELS",    "https://t.me/+PLACEHOLDER_HOTELS"),
    "food":      os.getenv("LINK_FOOD",      "https://t.me/+PLACEHOLDER_FOOD"),
    "esim":      os.getenv("LINK_ESIM",      "https://t.me/+PLACEHOLDER_ESIM"),
    "routes":    os.getenv("LINK_ROUTES",    "https://t.me/+PLACEHOLDER_ROUTES"),
    "jobs":      os.getenv("LINK_JOBS",      "https://t.me/+PLACEHOLDER_JOBS"),
    "community": os.getenv("LINK_COMMUNITY", "https://t.me/+PLACEHOLDER_COMMUNITY"),
    "support":   os.getenv("LINK_SUPPORT",   "https://t.me/chinatown_support"),
}

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# ── DATABASE ─────────────────────────────────────────────────────────────────
def db_init():
    con = sqlite3.connect("chinatown.db")
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INTEGER PRIMARY KEY,
            username   TEXT,
            full_name  TEXT,
            is_vip     INTEGER DEFAULT 0,
            joined_at  TEXT
        )
    """)
    con.commit()
    con.close()

def db_upsert(user_id, username, full_name):
    con = sqlite3.connect("chinatown.db")
    con.execute("""
        INSERT INTO users (user_id, username, full_name, joined_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name
    """, (user_id, username, full_name, datetime.utcnow().isoformat()))
    con.commit()
    con.close()

def db_set_vip(user_id: int, status: bool):
    con = sqlite3.connect("chinatown.db")
    con.execute("UPDATE users SET is_vip=? WHERE user_id=?", (int(status), user_id))
    con.commit()
    con.close()

def db_is_vip(user_id: int) -> bool:
    con = sqlite3.connect("chinatown.db")
    row = con.execute("SELECT is_vip FROM users WHERE user_id=?", (user_id,)).fetchone()
    con.close()
    return bool(row and row[0])

def db_count() -> dict:
    con = sqlite3.connect("chinatown.db")
    total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    vip   = con.execute("SELECT COUNT(*) FROM users WHERE is_vip=1").fetchone()[0]
    con.close()
    return {"total": total, "vip": vip}

# ── KEYBOARDS ────────────────────────────────────────────────────────────────
def kb_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼  Бизнес",        callback_data="menu_business")],
        [InlineKeyboardButton(text="✈️  Путешествия",   callback_data="menu_travel")],
        [InlineKeyboardButton(text="💱  Обмен валют",   callback_data="menu_exchange")],
        [InlineKeyboardButton(text="💼  Работа",        callback_data="menu_jobs")],
        [InlineKeyboardButton(text="👥  Комьюнити",     callback_data="menu_community")],
        [InlineKeyboardButton(text="⭐️  Chinatown Black", callback_data="menu_vip")],
    ])

def kb_business():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Карго",              url=LINKS["cargo"])],
        [InlineKeyboardButton(text="🛍️ Байеры",             url=LINKS["buyers"])],
        [InlineKeyboardButton(text="🏭 Поставщики",         url=LINKS["suppliers"])],
        [InlineKeyboardButton(text="🔍 Инспекция товара",   callback_data="coming_soon")],
        [InlineKeyboardButton(text="📋 Таможня и логистика",callback_data="coming_soon")],
        [InlineKeyboardButton(text="← Назад",               callback_data="back_main")],
    ])

def kb_travel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛂 Визы и въезд",  url=LINKS["visas"])],
        [InlineKeyboardButton(text="🏨 Отели и жильё", url=LINKS["hotels"])],
        [InlineKeyboardButton(text="🍜 Еда и рестораны",url=LINKS["food"])],
        [InlineKeyboardButton(text="📱 eSIM и VPN",    url=LINKS["esim"])],
        [InlineKeyboardButton(text="📍 Маршруты",      url=LINKS["routes"])],
        [InlineKeyboardButton(text="← Назад",          callback_data="back_main")],
    ])

def kb_exchange():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Проверенные обменники", url=LINKS["exchange"])],
        [InlineKeyboardButton(text="⚠️ Как не попасть на скам", callback_data="scam_warning")],
        [InlineKeyboardButton(text="💳 Карты и Alipay",        callback_data="coming_soon")],
        [InlineKeyboardButton(text="← Назад",                  callback_data="back_main")],
    ])

def kb_vip():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💳 Получить доступ — {VIP_PRICE} ₽/мес",
                              web_app=WebAppInfo(url=LAVA_TOP_URL))],
        [InlineKeyboardButton(text="🙋 Задать вопрос", url=LINKS["support"])],
        [InlineKeyboardButton(text="← Назад",          callback_data="back_main")],
    ])

def kb_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Главное меню", callback_data="back_main")]
    ])

# ── TEXTS ────────────────────────────────────────────────────────────────────
TEXT_WELCOME = """🏮 <b>Chinatown</b>

Всё, что нужно для жизни, бизнеса 
и путешествий в Китае — в одном месте.

Только проверенные люди и сервисы.
Без спама. Без скама.

👇 Выбери раздел:"""

TEXT_BUSINESS = """💼 <b>Бизнес в Китае</b>

Карго, байеры, поставщики, таможня — 
все нужные сервисы в одном месте.

✅ Все участники верифицированы командой Chinatown."""

TEXT_TRAVEL = """✈️ <b>Путешествия в Китай</b>

Визы, жильё, еда, маршруты — 
реальный опыт от людей которые там живут и работают."""

TEXT_EXCHANGE = """💱 <b>Обмен валют</b>

RUB ⇄ USDT ⇄ CNY

Только проверенные обменники ✅
Курсы обновляются ежедневно.

⚠️ Незнакомые люди в личку с хорошим курсом = скам"""

TEXT_JOBS = """💼 <b>Работа и вакансии</b>

Работа в Китае и удалённо по китайской тематике."""

TEXT_COMMUNITY = """👥 <b>Комьюнити Chinatown</b>

Живое сообщество людей, связанных с Китаем."""

TEXT_VIP = f"""⭐️ <b>Chinatown Black</b>

Закрытый клуб для тех, кто серьёзно работает с Китаем.

Внутри:
✅ База прямых поставщиков с контактами фабрик
✅ Лучшие обменники с эксклюзивными курсами
✅ Закрытый нетворкинг
✅ Приоритетная помощь команды
✅ Личный менеджер

<b>Стоимость: {VIP_PRICE} ₽ / месяц</b>"""

TEXT_SCAM = """⚠️ <b>Как не попасть на скам</b>

— Работай только с верифицированными сервисами из нашего хаба
— Крупные суммы — только через гаранта Chinatown
— Никто из команды не напишет первым в личку с предложением
— Проверяй отзывы перед переводом любых денег
— Незнакомые с "хорошим курсом" в личке = 100% скам"""

TEXT_SOON = "🔧 Раздел в разработке. Скоро!"

# ── HANDLERS ─────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    db_upsert(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    await msg.answer(TEXT_WELCOME, reply_markup=kb_main(), parse_mode="HTML")

@dp.message(Command("menu"))
async def cmd_menu(msg: Message):
    await msg.answer(TEXT_WELCOME, reply_markup=kb_main(), parse_mode="HTML")

# Admin commands
@dp.message(Command("confirm"))
async def cmd_confirm(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) < 2:
        await msg.answer("Использование: /confirm USER_ID")
        return
    uid = int(parts[1])
    db_set_vip(uid, True)
    try:
        link = await bot.create_chat_invite_link(VIP_CHANNEL, member_limit=1)
        await bot.send_message(uid,
            f"⭐️ <b>Добро пожаловать в Chinatown Black!</b>\n\n"
            f"Твоя ссылка для входа:\n{link.invite_link}\n\n"
            f"Ссылка одноразовая — не передавай её другим.",
            parse_mode="HTML")
        await msg.answer(f"✅ Доступ выдан пользователю {uid}")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")

@dp.message(Command("revoke"))
async def cmd_revoke(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) < 2:
        return
    uid = int(parts[1])
    db_set_vip(uid, False)
    try:
        await bot.ban_chat_member(VIP_CHANNEL, uid)
        await bot.unban_chat_member(VIP_CHANNEL, uid)
        await bot.send_message(uid, "⚠️ Ваша подписка Chinatown Black завершена.")
    except Exception as e:
        logger.error(f"Revoke error: {e}")
    await msg.answer(f"✅ Доступ отозван у {uid}")

@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    s = db_count()
    await msg.answer(
        f"📊 <b>Статистика Chinatown</b>\n\n"
        f"👤 Всего юзеров: {s['total']}\n"
        f"⭐️ VIP (Black): {s['vip']}",
        parse_mode="HTML"
    )

# Callbacks — навигация
@dp.callback_query(F.data == "back_main")
async def cb_back(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_WELCOME, reply_markup=kb_main(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_business")
async def cb_business(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_BUSINESS, reply_markup=kb_business(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_travel")
async def cb_travel(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_TRAVEL, reply_markup=kb_travel(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_exchange")
async def cb_exchange(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_EXCHANGE, reply_markup=kb_exchange(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_jobs")
async def cb_jobs(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_JOBS, reply_markup=kb_back(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_community")
async def cb_community(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_COMMUNITY, reply_markup=kb_back(), parse_mode="HTML")

@dp.callback_query(F.data == "menu_vip")
async def cb_vip(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_VIP, reply_markup=kb_vip(), parse_mode="HTML")

@dp.callback_query(F.data == "scam_warning")
async def cb_scam(cb: CallbackQuery):
    await cb.message.edit_text(TEXT_SCAM, reply_markup=kb_back(), parse_mode="HTML")

@dp.callback_query(F.data == "coming_soon")
async def cb_soon(cb: CallbackQuery):
    await cb.answer(TEXT_SOON, show_alert=True)

# ── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    db_init()
    logger.info("Chinatown bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
