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
except (KeyError, json.JSONDecodeError) as e:
    logging.error(f"Ошибка в структуре restaurants.json: {e}")
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

def get_dish_kb(rest_idx: int, dish_idx: int):
    kb = [
        [InlineKeyboardButton(text="Заказать", callback_data="order")],
        [InlineKeyboardButton(text="Назад к меню", callback_data=f"rest_{rest_idx}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# === Хэндлеры ===
@dp.message(Command("start"))
async def start(message: Message):
    if not DATA:
        await message.answer("Меню пустое. Добавьте рестораны в restaurants.json")
        return
    await message.answer("Выберите ресторан:", reply_markup=get_restaurants_kb())

@dp.callback_query(F.data == "start")
async def back_to_start(call: CallbackQuery):
    await call.message.edit_text("Выберите ресторан:", reply_markup=get_restaurants_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("rest_"))
async def show_menu(call: CallbackQuery):
    try:
        idx = int(call.data.split("_")[1])
        if idx >= len(DATA):
            await call.answer("Ресторан не найден!", show_alert=True)
            return
            
        rest = DATA[idx]
        await call.message.edit_text(
            f"*{rest['name']}*\n\nВыберите блюдо:",
            reply_markup=get_menu_kb(idx),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка в show_menu: {e}")
        await call.answer("Произошла ошибка!", show_alert=True)
    await call.answer()

@dp.callback_query(F.data.startswith("dish_"))
async def show_dish(call: CallbackQuery):
    try:
        _, rest_idx, dish_idx = call.data.split("_")
        rest_idx, dish_idx = int(rest_idx), int(dish_idx)
        
        # Проверка валидности индексов
        if rest_idx >= len(DATA) or dish_idx >= len(DATA[rest_idx]["menu"]):
            await call.answer("Блюдо не найдено!", show_alert=True)
            return
            
        dish = DATA[rest_idx]["menu"][dish_idx]

        caption = f"*{dish['name']}*\n\n{dish['description']}\n\n*Цена: {dish['price']} ₽*"

        photo_path = dish.get("photo")
        if photo_path and os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            try:
                await call.message.delete()
                await call.message.answer_photo(photo, caption=caption, reply_markup=get_dish_kb(rest_idx, dish_idx), parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка загрузки фото: {e}")
                await call.message.edit_text(caption + "\n\n(Фото не загружено)", reply_markup=get_dish_kb(rest_idx, dish_idx), parse_mode="Markdown")
        else:
            await call.message.edit_text(caption, reply_markup=get_dish_kb(rest_idx, dish_idx), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка в show_dish: {e}")
        await call.answer("Произошла ошибка!", show_alert=True)
    await call.answer()

@dp.callback_query(F.data == "order")
async def order(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Заказ принят! Скоро с вами свяжутся.")
    await call.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("Выберите ресторан:", reply_markup=get_restaurants_kb())
    await call.answer()

# === Запуск ===
async def main():
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
