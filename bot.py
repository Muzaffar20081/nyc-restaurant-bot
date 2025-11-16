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
def get_restaurants_kb():
    kb = [
        [InlineKeyboardButton(text=f"{r['emoji']} {r['name']}", callback_data=f"rest_{i}")]
        for i, r in enumerate(DATA)
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_menu_kb(rest_idx: int):
    rest = DATA[rest_idx]
    kb = [
        [InlineKeyboardButton(text=f"{d['name']} — {d['price']} ₽", callback_data=f"dish_{rest_idx}_{i}")]
        for i, d in enumerate(rest["menu"])
    ]
    kb.append([InlineKeyboardButton(text="Назад", callback_data="start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_dish_kb():
    kb = [
        [InlineKeyboardButton(text="Заказать", callback_data="order")],
        [InlineKeyboardButton(text="Назад к меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# === КОМАНДЫ ===
@dp.message(Command("start"))
async def start(message: Message):
    if not DATA:
        await message.answer("Меню пустое. Добавьте рестораны в restaurants.json")
        return

    # Приветствие + первый ресторан
    first_rest = DATA[0]
    welcome = (
        f"🍔 *Привет, {message.from_user.first_name}!*\n\n"
        f"Добро пожаловать в *{first_rest['name']}*!\n"
        "Вот наше меню:"
    )
    await message.answer(welcome, parse_mode="Markdown", reply_markup=get_menu_kb(0))

@dp.message(Command("menu"))
async def menu_command(message: Message):
    # Ищем Burger King (или первый ресторан)
    burger_idx = next((i for i, r in enumerate(DATA) if "Burger" in r["name"]), 0)
    rest = DATA[burger_idx]
    await message.answer(
        f"*{rest['name']}* — Каталог еды:",
        reply_markup=get_menu_kb(burger_idx),
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "❓ *Помощь*\n\n"
        "/start — Главное меню\n"
        "/menu — Каталог Burger King\n"
        "/help — Это сообщение\n\n"
        "💡 Поддержка: @muzaffar_support"
    )
    await message.answer(help_text, parse_mode="Markdown")

# === КАЛЛБЭКИ ===
@dp.callback_query(F.data == "start")
async def back_to_start(call: CallbackQuery):
    await call.message.edit_text("🍕 *Выберите ресторан:*", reply_markup=get_restaurants_kb(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.startswith("rest_"))
async def show_menu(call: CallbackQuery):
    idx = int(call.data.split("_")[1])
    rest = DATA[idx]
    await call.message.edit_text(
        f"*{rest['name']}*\n\nВыберите блюдо:",
        reply_markup=get_menu_kb(idx),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("dish_"))
async def show_dish(call: CallbackQuery):
    _, rest_idx, dish_idx = call.data.split("_")
    rest_idx, dish_idx = int(rest_idx), int(dish_idx)
    dish = DATA[rest_idx]["menu"][dish_idx]

    caption = f"*{dish['name']}*\n\n{dish['description']}\n\n*Цена: {dish['price']} ₽*"

    photo_path = dish.get("photo")
    if photo_path and os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        try:
            await call.message.delete()
            await call.message.answer_photo(photo, caption=caption, reply_markup=get_dish_kb(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка фото: {e}")
            await call.message.edit_text(caption + "\n\n(Фото не загружено)", reply_markup=get_dish_kb(), parse_mode="Markdown")
    else:
        await call.message.edit_text(caption, reply_markup=get_dish_kb(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "order")
async def order(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Заказ принят! Скоро с вами свяжутся.")
    await call.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("🍕 *Выберите ресторан:*", reply_markup=get_restaurants_kb(), parse_mode="Markdown")
    await call.answer()

# === Запуск ===
async def main():
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
