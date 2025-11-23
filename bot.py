# bot.py — ФИНАЛЬНЫЙ КРУТОЙ BURGER KING 2025
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=os.environ.get("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Цены (пока вручную, потом можно из restaurants.json)
PRICES = {
    "воппер":349,"двойной воппер":449,"чизбургер":149,"биг кинг":399,
    "картошка":149,"наггетсы":259,"кола":119,"кола 1л":179,"коктейль":199
}

def get_cart(uid):
    if not user_cart[uid]: return "*Корзина пустая*"
    total = sum(i["p"]*i["q"] for i in user_cart[uid])
    txt = "*Твоя корзина:*\n\n"
    for i in user_cart[uid]:
        txt += f"• {i['name']} × {i['q']} = {i['p']*i['q']}₽\n"
    txt += f"\n*Итого: {total}₽*"
    return txt

@dp.message(CommandStart())
async def start(m: types.Message):
    await m.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {m.from_user.first_name}!\n\n*BURGER KING 2025 — ЖИВОЙ НА МАКСИМАЛКАХ*\n\nПиши что хочешь заказать — я пойму!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(c: types.CallbackQuery):
    await c.message.edit_caption(caption="""
*МЕНЮ BURGER KING 2025*

Воппер — 349₽
Двойной Воппер — 449₽
Чизбургер — 149₽
Биг Кинг — 399₽
Картошка фри — 149₽
Наггетсы 9шт — 259₽
Кола 0.5л — 119₽
Кола 1л — 179₽
Молочный коктейль — 199₽
    """, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Корзина", callback_data="cart")]]))

@dp.callback_query(lambda c: c.data == "cart")
async def cart(c: types.CallbackQuery):
    await c.message.edit_caption(caption=get_cart(c.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Очистить", callback_data="clear")],
            [InlineKeyboardButton(text="Меню", callback_data="menu")]
        ]))

@dp.callback_query(lambda c: c.data == "clear")
async def clear(c: types.CallbackQuery):
    user_cart[c.from_user.id].clear()
    await c.answer("Корзина очищена!", show_alert=True)
    await cart(c)

@dp.message()
async def msg(m: types.Message):
    if not m.text: return
    text = m.text.lower()
    added = False
    for name, price in PRICES.items():
        if name in text:
            user_cart[m.from_user.id].append({"name": name.title(), "p": price, "q": 1})
            added = True
    if added:
        await m.answer(f"Закинул в корзину!\n\n{get_cart(m.from_user.id)}")
    else:
        await m.answer("Пиши что хочешь — воппер, колу, наггетсы… я пойму!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
