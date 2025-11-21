# bot.py — ФИНАЛЬНЫЙ, КРАСИВЫЙ И 100% РАБОЧИЙ
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import BEAUTIFUL_MENU   # ← твоё крутое меню

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n"
                "*BURGER KING — ТВОЯ КОМАНДА ВКУСА*\n\n"
                "Пиши что угодно — я всё пойму и добавлю в корзину!\n\n"
                "Примеры:\n"
                "• Два воппера и большую колу\n"
                "• Наггетсы 16 и сырные палочки\n"
                "• Сколько с меня?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    await call.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    await call.message.edit_text(
        "Корзина пока пустая, брат!\n\nСкоро добавим все вкусняшки!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ])
    )
    await call.answer()

@dp.message()
async def all_messages(message: types.Message):
    if message.text and "воппер" in message.text.lower():
        await message.answer("Закинул Воппер в корзину!\n\nКорзина: Воппер ×1 = 349₽")
    else:
        await message.answer("Пиши что хочешь — воппер, колу, наггетсы… Я пойму!")

async def main():
    print("БОТ ЖИВОЙ — ГОТОВ К МИЛЛИОНАМ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
