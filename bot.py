# bot.py — ФИНАЛЬНЫЙ КРУТОЙ BURGER KING 2025
import asyncio
import os
import httpx
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import BEAUTIFUL_MENU   # ← твоё эпичное меню

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

GROK_API_KEY = os.getenv("GROK_API_KEY")
user_cart = defaultdict(list)

# все цены из твоего нового меню
PRICES = {
    "воппер":349,"двойной воппер":449,"чизбургер":149,"двойной чизбургер":229,
    "биг кинг":399,"воппер сырный":379,"беконайзер":299,"лонг чикен":279,
    "картошка фри":149,"картошка по-деревенски":169,"наггетсы":259,"наггетсы 16":399,
    "луковые кольца":189,"сырные палочки":229,"кола":119,"кола 1л":179,
    "фанта":119,"спрайт":119,"молочный коктейль":199,"ледяной чай":149,"кофе":129,
    "мороженое":99,"чизкейк":159,"яблочный пирог":139,"маффин":119,
    "кетчуп":49,"сырный соус":49,"чесночный соус":49,"барбекю":49,"карри":49
}

def get_cart(uid):
    if not user_cart[uid]: return "*Корзина пустая, брат!*"
    total = sum(i["price"]*i["qty"] for i in user_cart[uid])
    txt = "*Твоя корзина:*\n\n"
    for i in user_cart[uid]:
        txt += f"• {i['name'].title()} × {i['qty']} = {i['price']*i['qty']}₽\n"
    txt += f"\n*Итого: {total}₽*"
    return txt

async def grok(text, cart):
    prompt = f"Меню:\n{BEAUTIFUL_MENU}\nКорзина: {cart}\nКлиент написал: {text}\nОтветь коротко и дерзко, по-пацански"
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={"model":"grok-2-latest","messages":[{"role":"user","content":prompt}],"temperature":0.9})
            if r.status_code == 200: return r.json()["choices"][0]["message"]["content"].strip()
    except: pass
    return "Сек, ща всё будет!"

def add(uid, text):
    text = text.lower()
    added = []
    for name in PRICES:
        if name in text:
            for i in user_cart[uid]:
                if i["name"]==name: i["qty"]+=1; added.append(name.title()); break
            else:
                user_cart[uid].append({"name":name,"price":PRICES[name],"qty":1})
                added.append(name.title())
    return added

@dp.message(CommandStart())
async def start(m: types.Message):
    await m.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {m.from_user.first_name}!\n\n*BURGER KING — ТВОЯ КОМАНДА ВКУСА*\n\nПиши что угодно — я всё пойму и закину в корзину!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
            [InlineKeyboardButton(text="Корзина", callback_data="cart")]
        ])
    )

@dp.callback_query(lambda c: c.data=="menu")
async def menu(c: types.CallbackQuery):
    await c.message.edit_caption(caption=BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Корзина",callback_data="cart")]]))

@dp.callback_query(lambda c: c.data=="cart")
async def cart(c: types.CallbackQuery):
    await c.message.edit_caption(caption=get_cart(c.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Очистить",callback_data="clear")],
            [InlineKeyboardButton(text="Меню",callback_data="menu")]
        ]))

@dp.callback_query(lambda c: c.data=="clear")
async def clear(c: types.CallbackQuery):
    user_cart[c.from_user.id].clear()
    await c.answer("Очищено!",show_alert=True)
    await cart(c)

@dp.message()
async def msg(m: types.Message):
    if not m.text: return
    added = add(m.from_user.id, m.text)
    if added:
        await m.answer(f"Закинул: {', '.join(added)}!\n\n{get_cart(m.from_user.id)}")
    else:
        await m.answer(await grok(m.text, get_cart(m.from_user.id)))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
