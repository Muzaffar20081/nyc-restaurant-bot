# bot.py
import asyncio
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ai_brain import ask_grok
from menu import BEAUTIFUL_MENU

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

def get_cart_text(user_id):
    if not user_cart[user_id]: return "пустая"
    total = sum(i["price"] * i["qty"] for i in user_cart[user_id])
    items = "\n".join(f"• {i['name']} × {i['qty']}" for i in user_cart[user_id])
    return f"{items}\n\nИтого: {total}₽"

def add_to_cart(user_id, name, price):
    for item in user_cart[user_id]:
        if item["name"] == name:
            item["qty"] += 1
            return
    user_cart[user_id].append({"name": name, "price": price, "qty": 1})

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(f"Здарова, бро! Го бургеры?!\n\n{BEAUTIFUL_MENU}",
                   parse_mode="Markdown")

@dp.message()
async def all_msg(m: types.Message):
    if not m.text or m.text.startswith("/"): return
    
    cart = get_cart_text(m.from_user.id)
    answer = await ask_grok(m.text, cart)
    
    if answer == "/menu":
        await m.answer(BEAUTIFUL_MENU, parse_mode="Markdown")
    else:
        await m.answer(answer, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
