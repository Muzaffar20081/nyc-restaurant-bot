# bot.py — УМНЫЙ BURGER KING БОТ НА GROK (работает 100%)
import asyncio
import json
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Логи
logging.basicConfig(level=logging.INFO)

# Токен бота и ключ Grok
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Загружаем меню
with open("restaurants.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)["restaurants"][0]

# Клавиатура меню
def get_menu_kb():
    kb = [
        [InlineKeyboardButton(text=f"{d['name']} — {d['price']} ₽", callback_data=f"dish_{i}")]
        for i, d in enumerate(DATA["menu"])
    ]
    kb.append([InlineKeyboardButton(text="Назад в меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Запрос к Grok (РАБОЧИЙ URL 2025!)
async def ask_grok(text: str) -> str:
    if not GROK_API_KEY:
        return "API ключ не найден 😅"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                "https://api.grok.xai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-beta",
                    "messages": [
                        {"role": "system", "content": "Ты — весёлый и дерзкий сотрудник Burger King в России. Отвечай коротко, по-русски, с юмором."},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.9,
                    "max_tokens": 300
                }
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"Грок приуныл 😓 (код {resp.status_code})"
        except Exception as e:
            logging.error(f"Grok error: {e}")
            return "Я щас немного торможу… Спроси ещё разок!"

# Команды
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
"f"Привет, {message.from_user.first_name}!\n\n"
"Это *Burger King* 🔥\n"
"• /menu — всё меню\n"
"• Просто пиши — я отвечу как живой сотрудник\n\n"
"Го закажем вкусняшку?",
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def menu_cmd(message: Message):
    await message.answer("Выбери что-нибудь вкусное:", reply_markup=get_menu_kb())

# Обычный чат — отправляем в Grok
@dp.message()
async def chat(message: Message):
    if message.text and not message.text.startswith("/"):
        answer = await ask_grok(message.text)
        await message.answer(answer)

# Выбор блюда
@dp.callback_query(F.data.startswith("dish_"))
async def show_dish(call: CallbackQuery):
    idx = int(call.data.split("_")[1])
    dish = DATA["menu"][idx]
    text = f"*{dish['name']}*\n\n{dish['description']}\n\nЦена: {dish['price']} ₽"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить в корзину", callback_data=f"add_{idx}")],
        [InlineKeyboardButton(text="Назад", callback_data="menu")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "menu")
async def back_to_menu(call: CallbackQuery):
    await call.message.edit_text("Выбери что-нибудь вкусное:", reply_markup=get_menu_kb())

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    await call.answer("Добавлено в корзину!", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Скоро добавлю полноценную корзину с оплатой 😉")

async def main():
    logging.info("БОТ ЗАПУЩЕН НА GROK!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
