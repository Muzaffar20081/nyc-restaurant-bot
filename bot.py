# bot.py
import asyncio
import logging
from typing import List, Union

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)

# Твои импорты
from config import config
from menus import MENU_BY_CUISINE

# ── Состояния FSM ────────────────────────────────────────────────────────────
class OrderStates(StatesGroup):
    CHOOSE_CUISINE = State()
    VIEW_MENU = State()
    IN_CART = State()


# ── Router ───────────────────────────────────────────────────────────────────
router = Router()

ITEMS_PER_PAGE = 4


# ── Вспомогательные функции ──────────────────────────────────────────────────
def get_cuisine_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора кухни"""
    buttons = []
    for key, name in config.CUISINES.items():
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"cuisine:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_menu(
    msg_or_call: Union[Message, CallbackQuery],
    state: FSMContext,
    page: int = 0
):
    """Показ страницы меню"""
    data = await state.get_data()
    cuisine = data.get("cuisine")

    if not cuisine or cuisine not in MENU_BY_CUISINE:
        text = "Сначала выберите кухню! → /start"
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
        kb_lines.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"add:{item.id}")
        ])

    # Навигация
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("← Назад", callback_data=f"page:{page-1}"))
    if start_idx + ITEMS_PER_PAGE < len(menu_list):
        nav.append(InlineKeyboardButton("Вперёд →", callback_data=f"page:{page+1}"))

    if nav:
        kb_lines.append(nav)

    kb_lines.append([InlineKeyboardButton("🛒 Посмотреть корзину", callback_data="show_cart")])

    markup = InlineKeyboardMarkup(inline_keyboard=kb_lines)

    text = f"<b>{config.CUISINES[cuisine]}</b>   (страница {page+1} из {total_pages or 1})\n\nВыберите блюдо:"

    if isinstance(msg_or_call, Message):
        await msg_or_call.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        await msg_or_call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")


async def show_cart(call: CallbackQuery, state: FSMContext):
    """Показ корзины"""
    data = await state.get_data()
    cart: dict = data.get("cart", {})
    cuisine = data.get("cuisine")

    if not cart:
        text = "🛒 Ваша корзина пока пуста\nДобавьте что-нибудь из меню!"
        kb = [[InlineKeyboardButton("← Вернуться в меню", callback_data="back_menu")]]
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
                lines.append(f"• {item.name} × {qty} = ${subtotal:.2f}")

        text = "<b>Корзина:</b>\n\n" + "\n".join(lines) + f"\n\n<b>Итого: ${total:.2f}</b>"
        kb = [
            [InlineKeyboardButton("Оформить заказ →", callback_data="checkout")],
            [InlineKeyboardButton("← Продолжить выбор", callback_data="back_menu")],
            [InlineKeyboardButton("Очистить корзину", callback_data="clear_cart")]
        ]

    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await call.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await call.answer()


# ── Обработчики ──────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🍔🍕🍣 Добро пожаловать в NYC Restaurant Bot!\n\nВыберите кухню:",
        reply_markup=get_cuisine_keyboard()
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
    await call.message.edit_text(
        f"Выбрана кухня: <b>{config.CUISINES[cuisine]}</b>\n\nЗагружаю меню...",
        parse_mode="HTML"
    )
    await show_menu(call, state, page=0)
    await state.set_state(OrderStates.VIEW_MENU)
    await call.answer()


@router.callback_query(F.data.startswith("page:"))
async def change_page(call: CallbackQuery, state: FSMContext):
    try:
        page = int(call.data.split(":", 1)[1])
        await show_menu(call, state, page=page)
    except:
        await call.answer("Ошибка смены страницы", show_alert=True)
    else:
        await call.answer()


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(call: CallbackQuery, state: FSMContext):
    item_id = call.data.split(":", 1)[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[item_id] = cart.get(item_id, 0) + 1
    await state.update_data(cart=cart)
    await call.answer(f"Добавлено: +1", show_alert=True)


@router.callback_query(F.data == "show_cart")
async def cb_show_cart(call: CallbackQuery, state: FSMContext):
    await show_cart(call, state)


@router.callback_query(F.data == "back_menu")
async def cb_back_menu(call: CallbackQuery, state: FSMContext):
    await show_menu(call, state, page=0)
    await call.answer()


@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(call: CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await show_cart(call, state)
    await call.answer("Корзина очищена", show_alert=True)


@router.callback_query(F.data == "checkout")
async def cb_checkout(call: CallbackQuery, state: FSMContext):
    # Пока заглушка — следующий шаг: ввод адреса
    await call.message.edit_text(
        "Оформление заказа (в разработке)\n\n"
        "Сейчас добавим ввод адреса и сохранение заказа"
    )
    await call.answer("Скоро будет оформление!", show_alert=True)


# ── Запуск бота ──────────────────────────────────────────────────────────────
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Если есть инициализация базы данных — можно добавить сюда
    # from database import init_db
    # await init_db()

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
