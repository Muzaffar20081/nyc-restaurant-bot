# bot.py
import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, FSInputFile
)
from aiogram.filters import Command
from config import BOT_TOKEN

# Логи
logging.basicConfig(level=logging.INFO)

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Загрузка данных
try:
    with open("restaurants.json", "r", encoding="utf-8") as f:
        DATA = json.load(f)["restaurants"]
except FileNotFoundError:
    logging.error("restaurants.json не найден!")
    DATA = []

# === Клавиатуры ===
def get_menu_kb():
    rest = DATA[0]  # Только Burger King
    kb = [
        [InlineKeyboardButton(text=f"{d['name']} — {d['price']} ₽", callback_data=f"dish_{i}")]
        for i, d in enumerate(rest["menu"])
    ]
    kb.append([InlineKeyboardButton(text="Назад", callback_data="start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_dish_kb():
    kb = [
        [InlineKeyboardButton(text="Заказать", callback_data="order")],
        [InlineKeyboardButton(text="Назад к меню", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# === КОМАНДЫ ===
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        f"🍔 *Привет, {message.from_user.first_name}!*\n\n"
        "Добро пожаловать в *Burger King*!",
        '  \n\n чтобы сделать заказ' ,
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def menu_command(message: Message):
    if not DATA:
        await message.answer("Меню пустое.")
        return
    rest = DATA[0]
    await message.answer(
        f"🍔 *{rest['name']} — Полное меню:*",
        reply_markup=get_menu_kb(),
        parse_mode="Markdown"
    )
@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "❓ *Помощь*\n\n"
        "/start — Главное меню\n"
        "/menu — Показать меню\n"
        "/help — Это сообщение",
        parse_mode="Markdown"
    )

# === КАЛЛБЭКИ ===
@dp.callback_query(F.data == "start")
async def back_to_start(call: CallbackQuery):
    await call.message.edit_text(
        "🍔 *Выберите блюдо:*",
        reply_markup=get_menu_kb(),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("dish_"))
async def show_dish(call: CallbackQuery):
    dish_idx = int(call.data.split("_")[1])
    dish = DATA[0]["menu"][dish_idx]
    caption = f"*{dish['name']}*\n\n{dish['description']}\n\n*Цена: {dish['price']} ₽*"

    photo_path = dish.get("photo")
    if photo_path and os.path.exists(photo_path):
        try:
            await call.message.delete()
            await call.message.answer_photo(FSInputFile(photo_path), caption=caption, reply_markup=get_dish_kb(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка фото: {e}")
            await call.message.edit_text(caption + "\n\n(Фото не загружено)", reply_markup=get_dish_kb(), parse_mode="Markdown")
    else:
        await call.message.edit_text(caption, reply_markup=get_dish_kb(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "order")
async def order(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Заказ принят! Скоро свяжутся.")
    await call.answer()

@dp.callback_query(F.data == "menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text(
        "🍔 *Выберите блюдо:*",
        reply_markup=get_menu_kb(),
        parse_mode="Markdown"
    )
    await call.answer()

# === Запуск ===
async def main():
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

