# bot.py — САМЫЙ КРАСИВЫЙ И УМНЫЙ BURGER KING БОТ В РОССИИ 2025
import asyncio
import os
import logging
import httpx
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# Корзина для каждого пацана
user_cart = defaultdict(list)

# Цены всех вкусняшек
MENU_PRICES = {
    "воппер": 349, "двойной воппер": 449, "чизбургер": 149, "двойной чизбургер": 229,
    "биг кинг": 399, "бигкинг": 399, "картошка": 149, "фри": 149, "наггетсы": 259,
    "кола": 119, "кола 1л": 179, "коктейль": 199, "молочный коктейль": 199, "соус": 49
}

# Синонимы для поиска в тексте
MENU_SYNONYMS = {
    "воппер": ["воппер", "вопер", "wopper"],
    "двойной воппер": ["двойной воппер", "двойной вопер", "двойной воппер", "двойной вopper"],
    "чизбургер": ["чизбургер", "чизбургер", "чиз"],
    "двойной чизбургер": ["двойной чизбургер", "двойной чиз"],
    "биг кинг": ["биг кинг", "бигкинг", "биг кин", "big king"],
    "картошка": ["картошка", "картофель", "фри", "картофель фри"],
    "наггетсы": ["наггетсы", "наггетс", "нагетсы", "нагетс", "nuggets"],
    "кола": ["кола", "кока кола", "coca cola", "колу"],
    "кола 1л": ["кола 1л", "кола 1 литр", "кока кола 1л"],
    "молочный коктейль": ["молочный коктейль", "коктейль", "милкшейк", "молочный"],
    "соус": ["соус", "сырный соус", "соус сырный"]
}

# Самое красивое меню в России
BEAUTIFUL_MENU = """
🍔 *МЕНЮ BURGER KING — МАКСИМАЛКИ 2025* 🍔

🔥 *Бургеры* 🔥
Воппер — 349₽
Двойной Воппер — 449₽
Чизбургер — 149₽
Двойной Чизбургер — 229₽
Биг Кинг — 399₽

🍟 *Гарниры и закуски* 🍟
Картошка фри большая — 149₽
Наггетсы 9 шт — 259₽
Соус сырный — 49₽

🥤 *Напитки* 🥤
Кола 0.5л — 119₽
Кола 1л — 179₽
Молочный коктейль — 199₽

Пиши что угодно — я пойму и добавлю в корзину автоматически!
"""

# Функция для Grok — он теперь дерзкий сотрудник BK
async def grok_brain(user_text: str, cart_info: str) -> str:
    prompt = f"""Ты — самый дерзкий сотрудник Burger King в России. Отвечай коротко, по-пацански, с матом можно (но умеренно).

Меню Burger King:
{BEAUTIFUL_MENU}

Корзина клиента:
{cart_info}

Клиент написал: "{user_text}"

Правила:
1. Если просят меню — отвечай кратко и отправляй меню
2. Если заказывают еду — подтверждай добавление в корзину
3. Если спрашивают про сумму — показывай итог
4. Будь кратким и по-пацански!"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                    "max_tokens": 150
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logging.error(f"Grok API error: {resp.status_code} - {resp.text}")
                return "Братан, серваки глючат, попробуй ещё раз 🤙"
    except Exception as e:
        logging.error(f"Grok request failed: {e}")
        return "Чёт интернет тупит, брат... Попробуй снова 💪"

# Корзина — красиво и с итогом
def get_cart(user_id):
    items = user_cart[user_id]
    if not items:
        return "🛒 *Корзина пустая, брат*"
    
    total = sum(item["price"] * item["qty"] for item in items)
    text = "🛒 *Твоя корзина:*\n\n"
    for item in items:
        text += f"• {item['name'].title()} × {item['qty']} = {item['price'] * item['qty']}₽\n"
    text += f"\n💰 *Итого: {total}₽*"
    return text

# Добавляем в корзину по словам
def add_to_cart(user_id, text):
    text = text.lower()
    added_items = []
    
    # Проверяем синонимы
    for item_name, synonyms in MENU_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in text:
                # Ищем, есть ли уже в корзине
                found = False
                for item in user_cart[user_id]:
                    if item["name"] == item_name:
                        item["qty"] += 1
                        found = True
                        break
                
                if not found:
                    user_cart[user_id].append({
                        "name": item_name, 
                        "price": MENU_PRICES[item_name], 
                        "qty": 1
                    })
                
                added_items.append(item_name)
                break
    
    return added_items

# /start — красивая картинка и приветствие
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    try:
        logging.info(f"Start command received from {message.from_user.id}")
        await message.answer_photo(
            photo="https://via.placeholder.com/400x200/FF6B00/FFFFFF?text=Burger+King+2025",
            caption=f"Здарова, {message.from_user.first_name}!\n\n"
                    "*Добро пожаловать в Burger King нового уровня!*\n\n"
                    "Просто пиши мне как живому сотруднику:\n"
                    "«Два воппера и колу»\n"
                    "«Сколько с меня?»\n"
                    "«Дай меню»\n\n"
                    "Я всё пойму сам!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ])
        )
        logging.info("Start command executed successfully")
    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")
        await message.answer("Произошла ошибка, попробуйте позже")

# Команда /menu
@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer(
        BEAUTIFUL_MENU,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
        ])
    )

# Команда /cart
@dp.message(Command("cart"))
async def cmd_cart(message: types.Message):
    await message.answer(
        get_cart(message.from_user.id),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
        ])
    )

# Кнопка Меню
@dp.callback_query(lambda c: c.data == "menu")
async def show_menu(call: types.CallbackQuery):
    try:
        await call.message.edit_text(
            BEAUTIFUL_MENU,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
            ])
        )
    except Exception as e:
        await call.message.answer(
            BEAUTIFUL_MENU,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
            ])
        )
    await call.answer()

# Кнопка Корзина
@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    try:
        await call.message.edit_text(
            get_cart(call.from_user.id),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
            ])
        )
    except Exception as e:
        await call.message.answer(
            get_cart(call.from_user.id),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="❌ Очистить корзину", callback_data="clear")]
            ])
        )
    await call.answer()

# Очистить корзину
@dp.callback_query(lambda c: c.data == "clear")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_cart[user_id]:
        user_cart[user_id].clear()
        await call.answer("Корзина очищена! 🗑️", show_alert=True)
        await show_cart(call)
    else:
        await call.answer("Корзина и так пустая! 🤷", show_alert=True)

# Все остальные сообщения
@dp.message()
async def all_messages(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id
    
    # Пробуем добавить в корзину
    added_items = add_to_cart(user_id, message.text)
    
    if added_items:
        items_text = ", ".join([item.title() for item in added_items])
        response = f"✅ Добавил в корзину: {items_text}! 🔥\n\n{get_cart(user_id)}"
        await message.answer(
            response,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]
            ])
        )
        return

    # Если не заказ — спрашиваем у Grok
    cart_info = get_cart(user_id)
    answer = await grok_brain(message.text, cart_info)
    
    # Проверяем специальные команды от Grok
    if "меню" in answer.lower() and len(answer) < 100:
        await cmd_menu(message)
    elif "корзин" in answer.lower() and len(answer) < 100:
        await cmd_cart(message)
    else:
        await message.answer(answer)

# Запуск бота
async def main():
    logging.info("BURGER KING БОТ НА GROK ЗАПУЩЕН — САМЫЙ КРУТОЙ В РОССИИ!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
