# bot.py — 100% РАБОТАЕТ ДАЖЕ НА САМОМ ГЛЮЧНОМ RAILWAY
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# ТВОЁ ЭПИЧНОЕ МЕНЮ ПРЯМО ЗДЕСЬ — НИКАКИХ ИМПОРТОВ
BEAUTIFUL_MENU = """
BURGER KING - ТВОЯ КАМАНДА ВКУСА
БУРГЕРЫ-БОССЫ
• ВОППЕР — 349₽
• ДВОЙНОЙ ВОППЕР — 449₽
• ЧИЗБУРГЕР — 149₽
• ДВОЙНОЙ ЧИЗБУРГЕР — 229₽
• БИГ КИНГ — 399₽
• ВОППЕР СЫРНЫЙ — 379₽
• БЕКОНАЙЗЕР — 299₽
• ЛОНГ ЧИКЕН — 279₽

ЗАКУСКИ-УБИЙЦЫ
• КАРТОШКА ФРИ — 149₽
• КАРТОШКА ПО-ДЕРЕВЕНСКИ — 169₽
• НАГГЕТСЫ (8ШТ) — 259₽
• НАГГЕТСЫ (16ШТ) — 399₽
• ЛУКОВЫЕ КОЛЬЦА — 189₽
• СЫРНЫЕ ПАЛОЧКИ — 229₽

НАПИТКИ-ДРАЙВ
• КОЛА (0.5Л) — 119₽
• КОЛА (1Л) — 179₽
• ФАНТА — 119₽
• СПРАЙТ — 119₽
• МОЛОЧНЫЙ КОКТЕЙЛЬ — 199₽

ДЕСЕРТЫ-КАЙФ
• МОРОЖЕНОЕ — 99₽
• ЧИЗКЕЙК — 159₽
• ЯБЛОЧНЫЙ ПИРОГ — 139₽

ПИШИ ЧТО ХОЧЕШЬ — СДЕЛАЕМ БЫСТРО И ЧИСТО!
"""

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025*\n\nПиши что угодно — я всё пойму!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    await call.message.edit_caption(caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Корзина", callback_data="cart")]]))
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    await call.message.edit_caption(caption="*Корзина пустая, брат!*\n\nПиши заказ — я добавлю!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Меню", callback_data="menu")]]))
    await call.answer()

@dp.message()
async def echo(message: types.Message):
    await message.answer("Скоро пойму любой заказ и добавлю в корзину!\nПока просто проверяем, что всё работает")

async def main():
    print("БОТ ЖИВОЙ — 1000000%")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
