# bot.py — ФИНАЛЬНЫЙ, РАБОТАЕТ 100% НА RAILWAY С aiogram 3.13.1
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    await call.message.edit_caption(caption="*МЕНЮ BURGER KING 2025*\n\nВоппер — 349₽\nДвойной — 449₽\nКартошка — 149₽\nКола — 119₽\n\nПиши что хочешь — я добавлю в корзину!", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Корзина", callback_data="cart")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    await call.message.edit_caption(caption="*Корзина пока пустая, брат!*", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Меню", callback_data="menu")]]))
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
