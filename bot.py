# bot.py
import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ── Твои импорты ─────────────────────────────────────────────────────────────
from config import config
from menus import MENU_BY_CUISINE

# ── Состояния ────────────────────────────────────────────────────────────────
class OrderStates(StatesGroup):
    CHOOSE_CUISINE = State()
    VIEW_MENU = State()

# ── Router и константы ───────────────────────────────────────────────────────
router = Router()
ITEMS_PER_PAGE = 4

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-super-secret-123"  # ← поменяй на свой сложный секрет!

# ── Вспомогательные функции (как раньше) ─────────────────────────────────────
def get_cuisine_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"cuisine:{key}")]
        for key, name in config.CUISINES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_menu(msg_or_call, state: FSMContext, page: int = 0):
    data = await state.get_data()
    cuisine = data.get("cuisine")

    if not cuisine or cuisine not in MENU_BY_CUISINE:
        text = "Выберите кухню заново: /start"
        if isinstance(msg_or_call, Message):
            await msg_or_call.answer(text)
        else:
            await msg_or_call.message.answer(text)
        return

    menu_list = MENU_BY_CUISINE[cuisine]
    total_pages = (len(menu_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    start = page * ITEMS_PER_PAGE
    items = menu_list[start : start + ITEMS_PER_PAGE]

    kb = []
    for item in items:
        kb.append([
            InlineKeyboardButton(
                text=f"{item.name} — ${item.price:.2f}",
                callback_data=f"add:{item.id}"
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("← Назад", callback_data=f"page:{page-1}"))
    if start + ITEMS_PER_PAGE < len(menu_list):
        nav.append(InlineKeyboardButton("Вперёд →", callback_data=f"page:{page+1}"))

    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")])

    text = f"<b>{config.CUISINES[cuisine]}</b>  (стр. {page+1}/{total_pages})\n\nВыберите:"
    
    if isinstance(msg_or_call, Message):
        await msg_or_call.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    else:
        await msg_or_call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")


# ── Основные обработчики (оставляем твои) ────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Добро пожаловать! 🍔 Выберите кухню:", reply_markup=get_cuisine_keyboard())
    await state.set_state(OrderStates.CHOOSE_CUISINE)


@router.callback_query(F.data.startswith("cuisine:"))
async def process_cuisine(call: CallbackQuery, state: FSMContext):
    cuisine = call.data.split(":", 1)[1]
    if cuisine not in config.CUISINES:
        await call.message.answer("Ошибка выбора. /start")
        return

    await state.update_data(cuisine=cuisine, cart={})
    await call.message.edit_text(f"Выбрано: {config.CUISINES[cuisine]}\nЗагружаю меню...")
    await show_menu(call, state, 0)
    await call.answer()


# Добавь остальные callback-хендлеры (add:, page:, show_cart и т.д.) как раньше


# ── Запуск webhook-сервера ──────────────────────────────────────────────────
async def on_startup(bot: Bot):
    base_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}"
    if not base_url:
        base_url = "https://your-service-name.railway.app"  # ← поменяй если нужно
    webhook_url = f"{base_url}{WEBHOOK_PATH}"
    
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    print(f"Webhook установлен: {webhook_url}")


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)
    dp.startup.register(on_startup)

    app = web.Application()

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET
    )
    handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print(f"Сервер запущен на порту {port}")
    await asyncio.Event().wait()  # держим процесс живым


if __name__ == "__main__":
    asyncio.run(main())
