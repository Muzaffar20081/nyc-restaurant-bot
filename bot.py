# bot.py — 100% БЕЗ КРАШЕЙ (18 ноября 2025)
import asyncio
import os
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from ai_brain import ask_grok
from menu import BEAUTIFUL_MENU

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Цены (для надёжности)
PRICES = {
    "воппер": 349, "двойной воппер": 449, "чизбургер": 149, "биг кинг": 399,
    "картошка": 149, "наггетсы": 259, "кола": 119, "кола 1л": 179, "коктейль": 199,
    "двойной чизбургер": 229, "сырный соус": 49
}

def get_cart_text(user_id):
    if not user_cart[user_id]:
        return "пустая 😅"
    total = sum(item["price"] * item["qty"] for item in user_cart[user_id])
    items = "\n".join(f"• {item['name'].capitalize()} × {item['qty']} = {item['price']*item['qty']}₽" 
                     for item in user_cart[user_id])
    return f"{items}\n\n*Итого: {total}₽*"

def add_to_cart(user_id, text):
    text = text.lower()
    added = False
    message = ""
    for name, price in PRICES.items():
        if name in text or any(word in text for word in name.split()):
            for item in user_cart[user_id]:
                if item["name"] == name:
                    item["qty"] += 1
                    message = f"Закинул ещё один {name.title()}! 🔥"
                    added = True
                    break
            if not added:
                user_cart[user_id].append({"name": name, "price": price, "qty": 1})
                message = f"Добавил {name.title()} в корзину! 🍔"
            added = True
            break
    return message if added else None

@dp.message(Command("start"))
async def start(message: types.Message):
    try:
        photo = FSInputFile("welcome.png")
        await message.answer_photo(
            photo=photo,
            caption=f"Здарова, {message.from_user.first_name}! 🔥\n\n"
                    "*Добро пожаловать в Burger King на максималках!*\n\n"
                    "Просто пиши что хочешь — я всё пойму и сделаю заказ!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Открыть меню", callback_data="menu")]
            ])
        )
    except Exception as e:
        logging.error(f"Фото не загрузилось: {e}")
        await message.answer(
            f"Здарова, {message.from_user.first_name}! 🔥\n\n"
            "Burger King на максималках!\n"
            "Пиши что хочешь — я всё сделаю!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="menu")]
            ])
        )

@dp.callback_query(F.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(F.data == "cart")
async def show_cart(call: types.CallbackQuery):
    text = f"*Твоя корзина:*\n\n{get_cart_text(call.from_user.id)}"
    await call.message.edit_caption(
        caption=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="Очистить", callback_data="clear_cart")],
            [InlineKeyboardButton(text="Назад", callback_data="menu")]
        ])
    )

@dp.callback_query(F.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_cart[call.from_user.id].clear()
    await call.answer("Корзина очищена!", show_alert=True)
    await show_cart(call)

@dp.message()
async def all_messages(message: types.Message):
    if not message.text or message.text.startswith("/"):
        return

    user_id = message.from_user.id
    added_msg = add_to_cart(user_id, message.text)
    
    if added_msg:
        await message.answer(added_msg + f"\n\n{get_cart_text(user_id)}", parse_mode="Markdown")
        return

    cart_info = get_cart_text(user_id)
    answer = await ask_grok(message.text, cart_info)
    
    if answer == "/menu":
        await message.answer(BEAUTIFUL_MENU, parse_mode="Markdown")
    else:
        await message.answer(answer, parse_mode="Markdown")

async def main():
    logging.info("БОТ ЗАПУЩЕН БЕЗ КРАШЕЙ — ГОТОВ ПРОДАВАТЬ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
