import asyncio
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from ai_brain import ask_grok
from menu import BEAUTIFUL_MENU

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

@dp.message(Command("start"))
async def start(m: types.Message):
    photo = FSInputFile("welcome.png")  # ← вот эта твоя красивая картинка
    await m.answer_photo(
        photo,
        caption=f"Здарова, {m.from_user.first_name}! 🔥\n\n"
                "Добро пожаловать в Burger King нового уровня!\n"
                "Просто пиши мне что хочешь — я всё сделаю сам!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Открыть меню", callback_data="menu")]
        ])
    )

@dp.callback_query(F.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ]),
        parse_mode="Markdown"
    )

@dp.message()
async def all_msg(m: types.Message):
    if not m.text or m.text.startswith("/"): return
    
    cart = ""  # потом добавим
    answer = await ask_grok(m.text, cart)
    
    if answer == "/menu":
        await m.answer(BEAUTIFUL_MENU, parse_mode="Markdown")
    else:
        await m.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
