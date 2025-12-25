# bot.py
import asyncio
import logging
from typing import List

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

# ── Импорт твоих модулей ───────────────────────────────
from config import config  # предполагаю, что у тебя есть BOT_TOKEN и CUISINES
from menus import MENU_BY_CUISINE, burger_menu, italy_menu, sushi_menu  # твои меню

# Если config.py нет — вот минимальный вариант
# class Config:
#     BOT_TOKEN = "YOUR_TOKEN_HERE"
#     CUISINES = {"burgers": "🍔 Бургеры", "italy": "🍝 Италия", "sushi": "🍣 Суши"}
# config = Config()

# ── Состояния ───────────────────────────────────────────
class OrderStates(StatesGroup):
    CHOOSE_CUISINE = State()
    VIEW_MENU = State()
    IN_CART = State()

# ── Router ──────────────────────────────────────────────
router = Router()

ITEMS_PER_PAGE = 4

# ── Вспомогательные функции ─────────────────────────────
def get_cuisine_kb() -> InlineKeyboardMarkup:
    buttons = []
    for key, name in config.CUISINES.items():
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"cuisine:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_menu(
    msg_or_call: Message | CallbackQuery,
    state: FSMContext,
    page: int = 0
):
    data = await state.get_data()
    cuisine = data.get("cuisine")

    if not cuisine or cuisine not in MENU_BY_CUISINE:
        text = "Сначала выберите кухню! /start"
        if isinstance(msg_or_call, Message):
            await msg_or_call.answer(text)
        else:
            await msg_or_call.message.answer(text)
        return

    menu_list: List = MENU_BY_CUISINE[cuisine]
    total_pages = (len(menu_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    start_idx = page * ITEMS_PER_PAGE
    items = menu_list[start_idx : start_idx + ITEMS_PER_PAGE]

    kb_lines = []
    for item in items:
        btn_text = f"{item.name} — ${item.price:.2f}"
        kb_lines.append([InlineKeyboardButton(text=btn_text, callback_data=f"add:{item.id}")])

    # Навигация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("← Назад", callback_data=f"page:{page-1}"))
    if start_idx + ITEMS_PER_PAGE < len(menu_list):
        nav.append(InlineKeyboardButton("Вперёд →", callback_data=f"page:{page+1}"))

    if nav:
        kb_lines.append(nav)

    kb_lines.append([InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")])

    markup = InlineKeyboardMarkup(inline_keyboard=kb_lines)

    text = f"Меню: {config.CUISINES[cuisine]}   (стр {page+1}/{total_pages or 1})\n\nВыберите блюдо:"

    if isinstance(msg_or_call, Message):
        await msg_or_call.answer(text, reply_markup=markup)
    else:
        await msg_or_call.message.edit_text(text, reply_markup=markup)


async def show_cart(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart: dict = data.get("cart", {})
    cuisine = data.get("cuisine")

    if not cart:
        text = "Корзина пуста 😔\nДобавьте что-нибудь вкусное!"
        kb = [[InlineKeyboardButton("← В меню", callback_data="back_menu")]]
    else:
        menu = MENU_BY_CUISINE.get(cuisine, [])
        menu_dict = {item.id: item for item in menu}

        lines = []
        total = 0.0
        for item_id, qty in cart.items():
            item = menu_dict.get(item_id)
            if item:
                subtotal = item.price * qty
                total += subtotal
                lines.append(f"• {item.name} ×{qty} = ${subtotal:.2f}")

        text = "<b>Ваша корзина:</b>\n" + "\n".join(lines) + f"\n\n<b>Итого: ${total:.2f}</b>"
        kb = [
            [InlineKeyboardButton("Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton("← Продолжить", callback_data="back_menu")],
            [InlineKeyboardButton("Очистить", callback_data="clear_cart")]
        ]

    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await call.answer()


# ── Хендлеры ────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать в NYC Restaurant Bot! 🍔🍕🍣\n\nВыберите кухню:",
        reply_markup=get_cuisine_kb()
    )
    await state.set_state(OrderStates.CHOOSE_CUISINE)


@router.callback_query(F.data.startswith("cuisine:"))
async def process_cuisine(call: CallbackQuery, state: FSMContext):
    cuisine = call.data.split(":", 1)[1]
    if cuisine not in config.CUISINES:
        await call.message.answer("Что-то пошло не так... Попробуйте /start")
        await call.answer()
        return

    await state.update_data(cuisine=cuisine, cart={})
    await call.message.edit_text(f"Выбрано: {config.CUISINES[cuisine]}\n\nЗагружаю меню...")
    await show_menu(call, state, page=0)
    await state.set_state(OrderStates.VIEW_MENU)
    await call.answer()


@router.callback_query(F.data.startswith("page:"))
async def change_page(call: CallbackQuery, state: FSMContext):
    page = int(call.data.split(":", 1)[1])
    await show_menu(call, state, page=page)
    await call.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_item(call: CallbackQuery, state: FSMContext):
    item_id = call.data.split(":", 1)[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[item_id] = cart.get(item_id, 0) + 1
    await state.update_data(cart=cart)
    await call.answer("✅ Добавлено в корзину!", show_alert=True)


@router.callback_query(F.data == "show_cart")
async def cb_show_cart(call: CallbackQuery, state: FSMContext):
    await show_cart(call, state)


@router.callback_query(F.data == "back_menu")
async def back_to_menu(call: CallbackQuery, state: FSMContext):
    await show_menu(call, state, page=0)
    await call.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart_cb(call: CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await show_cart(call, state)
    await call.answer("Корзина очищена", show_alert=True)


@router.callback_query(F.data == "checkout")
async def checkout_placeholder(call: CallbackQuery):
    await call.message.edit_text("Оформление заказа (пока заглушка)\n\nАдрес: ...")
    await call.answer("Скоро добавим оплату и адрес!")


# ── Запуск ──────────────────────────────────────────────
async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
