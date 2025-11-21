# bot.py
import asyncio
import os
import httpx
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Инициализация бота
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

GROK_API_KEY = os.getenv("GROK_API_KEY")
user_cart = defaultdict(list)

PRICES = {
    "воппер": 349, "двойной воппер": 449, "чизбургер": 149, "двойной чизбургер": 229,
    "биг кинг": 399, "воппер сырный": 379, "беконайзер": 299, "лонг чикен": 279,
    "картошка": 149, "картошка по-деревенски": 169, "наггетсы": 259, "наггетсы 16шт": 399,
    "луковые кольца": 189, "сырные палочки": 229, "кола": 119, "кола 1л": 179,
    "фанта": 119, "спрайт": 119, "коктейль": 199, "ледяной чай": 149, "кофе": 129,
    "мороженое": 99, "чизкейк": 159, "яблочный пирог": 139, "маффин": 119,
    "соус": 49, "кетчуп": 49, "сырный соус": 49, "чесночный соус": 49, 
    "соус барбекю": 49, "соус карри": 49
}

BEAUTIFUL_MENU = """
🔥 *BURGER KING - ТВОЯ КАМАНДА ВКУСА* 🔥

🍔 *БУРГЕРЫ-БОССЫ*
┣ • ВОППЕР — 349₽
┣ • ДВОЙНОЙ ВОППЕР — 449₽  
┣ • ЧИЗБУРГЕР — 149₽
┣ • ДВОЙНОЙ ЧИЗБУРГЕР — 229₽
┣ • БИГ КИНГ — 399₽
┣ • ВОППЕР СЫРНЫЙ — 379₽
┣ • БЕКОНАЙЗЕР — 299₽
┗ • ЛОНГ ЧИКЕН — 279₽

🍟 *ЗАКУСКИ-УБИЙЦЫ*
┣ • КАРТОШКА ФРИ — 149₽
┣ • КАРТОШКА ПО-ДЕРЕВЕНСКИ — 169₽
┣ • НАГГЕТСЫ (8ШТ) — 259₽
┣ • НАГГЕТСЫ (16ШТ) — 399₽
┣ • ЛУКОВЫЕ КОЛЬЦА — 189₽
┗ • СЫРНЫЕ ПАЛОЧКИ — 229₽

🥤 *НАПИТКИ-ДРАЙВ*
┣ • КОЛА (0.5Л) — 119₽
┣ • КОЛА (1Л) — 179₽
┣ • ФАНТА (0.5Л) — 119₽
┣ • СПРАЙТ (0.5Л) — 119₽
┣ • МОЛОЧНЫЙ КОКТЕЙЛЬ — 199₽
┣ • ЛЕДЯНОЙ ЧАЙ — 149₽
┗ • КОФЕ — 129₽

🍦 *ДЕСЕРТЫ-КАЙФ*
┣ • МОРОЖЕНОЕ — 99₽
┣ • ЧИЗКЕЙК — 159₽
┣ • ЯБЛОЧНЫЙ ПИРОГ — 139₽
┗ • МАФФИН — 119₽

🫙 *СОУСЫ-ПРИКОЛЫ*
┣ • СОУС КЕТЧУП — 49₽
┣ • СОУС СЫРНЫЙ — 49₽
┣ • СОУС ЧЕСНОЧНЫЙ — 49₽
┣ • СОУС БАРБЕКЮ — 49₽
┗ • СОУС КАРРИ — 49₽

💥 *ПИШИ ЧТО ХОЧЕШЬ — СДЕЛАЕМ БЫСТРО И ЧИСТО!* 💥
"""

def get_cart(uid):
    if not user_cart[uid]: 
        return "*Корзина пустая*"
    
    total = sum(item["price"] * item["qty"] for item in user_cart[uid])
    txt = "*Твоя корзина:*\n\n"
    for item in user_cart[uid]:
        txt += f"• {item['name'].title()} × {item['qty']} = {item['price'] * item['qty']}₽\n"
    txt += f"\n*Итого: {total}₽*"
    return txt

async def grok(text, cart):
    prompt = f"Меню:\n{BEAUTIFUL_MENU}\nКорзина: {cart}\nКлиент написал: {text}\nОтветь коротко и дерзко, по-пацански"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Ошибка Grok: {e}")
    return "Ща всё будет, брат"

def add_to_cart(text, user_id):
    text = text.lower()
    for product_name in PRICES:
        if product_name in text:
            # Проверяем есть ли уже товар в корзине
            for item in user_cart[user_id]:
                if item["name"] == product_name:
                    item["qty"] += 1
                    return product_name.title()
            
            # Если товара нет - добавляем
            user_cart[user_id].append({
                "name": product_name, 
                "price": PRICES[product_name], 
                "qty": 1
            })
            return product_name.title()
    return None

@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer_photo(
        photo="https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\\n\\n*Burger King на максималках*\\nПиши что хочешь — я всё сделаю!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="show_menu")],
                [InlineKeyboardButton(text="Корзина", callback_data="show_cart")]
            ]
        )
    )

@dp.callback_query(lambda c: c.data == "show_menu")
async def show_menu(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption=BEAUTIFUL_MENU,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Корзина", callback_data="show_cart")]
            ]
        )
    )

@dp.callback_query(lambda c: c.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption=get_cart(callback.from_user.id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Очистить", callback_data="clear_cart")],
                [InlineKeyboardButton(text="Меню", callback_data="show_menu")]
            ]
        )
    )

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_cart[user_id].clear()
    await callback.answer("Корзина очищена!", show_alert=True)
    await show_cart(callback)

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text or ""
    
    added_product = add_to_cart(text, user_id)
    if added_product:
        await message.answer(
            f"Закинул {added_product}!\\n\\n{get_cart(user_id)}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        cart_text = get_cart(user_id)
        response = await grok(text, cart_text)
        await message.answer(response)

async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
