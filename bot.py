import asyncio
import json
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Меню
with open("restaurants.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)["restaurants"][0]

def menu_kb():
    kb = []
    for i, dish in enumerate(DATA["menu"]):
        kb.append([InlineKeyboardButton(
            text=f"{dish['name']} — {dish['price']}₽",
            callback_data=f"dish_{i}"
        )])
    kb.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# РАБОЧИЙ GROK (ноябрь 2025)
async def ask_grok(text: str) -> str:
    if not GROK_API_KEY:
        return "Ключ пропал 😭"

    async with httpx.AsyncClient(timeout=40.0) as client:
        try:
            r = await client.post(
                "https://api.x.ai/v1/chat/completions",           # ← правильный URL
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-2-latest",                         # ← актуальная модель
                    "messages": [
                        {"role": "system", "content": "Ты весёлый и дерзкий сотрудник Burger King в России. Отвечай коротко, по-русски и с юмором."},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.85,
                    "max_tokens": 300
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"Грок грустит: код {r.status_code}"
        except Exception as e:
            logging.error(f"Grok error: {e}")
            return "Я чуть торможу… Спроси ещё разок 🔥"

# /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🔥\n\n"
        "Это Burger King нового уровня!\n"
        "• /menu — всё меню\n"
        "• Просто пиши мне — я отвечу как живой сотрудник\n\n"
        "Го закажем что-нибудь вкусное?",
        parse_mode="Markdown"
    )

# /menu
@dp.message(Command("menu"))
async def menu_cmd(message: types.Message):
    await message.answer("Выбирай вкусняшку:", reply_markup=menu_kb())

# Любой текст → Grok
@dp.message()
async def any_text(message: types.Message):
    if message.text and not message.text.startswith("/"):
        answer = await ask_grok(message.text)
        await message.answer(answer)

# Кнопки блюд
@dp.callback_query(F.data.startswith("dish_"))
async def show_dish(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    dish = DATA["menu"][idx]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В корзину ✅", callback_data=f"add_{idx}")],
        [InlineKeyboardButton(text="Назад", callback_data="back")]
    ])
    await call.message.edit_text(
        f"*{dish['name']}*\n\n{dish['description']}\n\nЦена: {dish['price']}₽",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text("Выбирай вкусняшку:", reply_markup=menu_kb())

@dp.callback_query(F.data.startswith("add_"))
async def added(call: types.CallbackQuery):
    await call.answer("Добавлено в корзину! 🔥", show_alert=True)

# Запуск
async def main():
    logging.info("БОТ ЗАПУЩЕН НА GROK 2 LATEST — ГОТОВ ПРОДАВАТЬ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
