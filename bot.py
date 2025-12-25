# bot.py — ФИНАЛЬНАЯ КРАСИВАЯ ВЕРСИЯ С ФОТО, КОРЗИНОЙ И ЗАКАЗОМ
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

user_cart = defaultdict(list)

# Ссылки на фото (твои или мои — можно менять)
PHOTOS = {
    "start": "https://i.ibb.co/m9kJ7B/welcome-burger.png",
    "menu": "https://i.ibb.co/m9kJ7B/welcome-burger.png",
    "cart": "https://i.ibb.co/m9kJ7B/welcome-burger.png"
}

# Цены (можно потом вынести в JSON)
PRICES = {
    "Воппер": 349,
    "Двойной Воппер": 449,
    "Картошка": 149,
    "Кола": 119,
    "Чизбургер": 199,
    "Наггетсы": 179
}

@dp.message(CommandStart())
async def start(message: types.Message):
    try:
        await message.answer_photo(
            photo=PHOTOS["start"],
            caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ* (фото не загрузилось)",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    try:
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=PHOTOS["menu"],
                caption="*🍔 МЕНЮ BURGER KING 2025*\n\n"
                        "Воппер — 349₽\n"
                        "Двойной Воппер — 449₽\n"
                        "Картошка — 149₽\n"
                        "Кола — 119₽\n"
                        "Чизбургер — 199₽\n"
                        "Наггетсы — 179₽\n\n"
                        "Нажми на кнопку — добавлю в корзину!",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Воппер", callback_data="add_Воппер")],
                [InlineKeyboardButton(text="🍔 Двойной Воппер", callback_data="add_Двойной Воппер")],
                [InlineKeyboardButton(text="🍟 Картошка", callback_data="add_Картошка")],
                [InlineKeyboardButton(text="🥤 Кола", callback_data="add_Кола")],
                [InlineKeyboardButton(text="🍔 Чизбургер", callback_data="add_Чизбургер")],
                [InlineKeyboardButton(text="🍗 Наггетсы", callback_data="add_Наггетсы")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ])
        )
    except Exception as e:
        await call.message.edit_text(
            text="*🍔 МЕНЮ BURGER KING 2025*\n\n"
                 "Воппер — 349₽\n"
                 "Двойной Воппер — 449₽\n"
                 "Картошка — 149₽\n"
                 "Кола — 119₽\n"
                 "Чизбургер — 199₽\n"
                 "Наггетсы — 179₽\n\n"
                 "Нажми на кнопку — добавлю в корзину!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Воппер", callback_data="add_Воппер")],
                [InlineKeyboardButton(text="🍔 Двойной Воппер", callback_data="add_Двойной Воппер")],
                [InlineKeyboardButton(text="🍟 Картошка", callback_data="add_Картошка")],
                [InlineKeyboardButton(text="🥤 Кола", callback_data="add_Кола")],
                [InlineKeyboardButton(text="🍔 Чизбургер", callback_data="add_Чизбургер")],
                [InlineKeyboardButton(text="🍗 Наггетсы", callback_data="add_Наггетсы")],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_name = call.data[4:]
    prices = {
        "Воппер": 349,
        "Двойной Воппер": 449,
        "Картошка": 149,
        "Кола": 119,
        "Чизбургер": 199,
        "Наггетсы": 179
    }
   
    if item_name in prices:
        user_cart[call.from_user.id].append({
            "name": item_name,
            "price": prices[item_name]
        })
        await call.answer(f"✅ {item_name} добавлен в корзину!")
    else:
        await call.answer("❌ Товар не найден")
    await call.message.edit_reply_markup(reply_markup=None)  # убираем кнопки после добавления

@dp.callback_query(lambda c: c.data == "cart")
async def cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
   
    if not cart_items:
        caption = "*🛒 Корзина пуста, брат!*\n\nЗайди в меню и выбери что-нибудь вкусненькое 🍔"
        keyboard = [[InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart_items)
        caption = "*🛒 Твоя корзина:*\n\n"
       
        # Группируем одинаковые товары
        item_counts = {}
        for item in cart_items:
            name = item["name"]
            if name in item_counts:
                item_counts[name] += 1
            else:
                item_counts[name] = 1
       
        for name, count in item_counts.items():
            price = next(item["price"] for item in cart_items if item["name"] == name)
            caption += f"• {name} ×{count} — {price * count}₽\n"
       
        caption += f"\n💵 *Итого: {total}₽*"
       
        keyboard = [
            [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🍔 Продолжить покупки", callback_data="menu")]
        ]
   
    try:
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=PHOTOS["cart"],
                caption=caption,
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        await call.message.edit_text(
            text=caption,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id] = []
    await call.answer("🧹 Корзина очищена!")
    await cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
   
    if not cart_items:
        await call.answer("❌ Корзина пуста!")
        return
   
    total = sum(item["price"] for item in cart_items)
   
    # Очищаем корзину после заказа
    user_cart[user_id] = []
   
    order_text = f"✅ *Заказ принят!*\n\n"
    for item in cart_items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💵 Сумма: {total}₽\n📱 Статус: принят\n\nОжидай уведомление о готовности!"
   
    try:
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=PHOTOS["start"],
                caption=order_text,
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")]
            ])
        )
    except:
        await call.message.edit_text(
            text=order_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")]
            ]),
            parse_mode="Markdown"
        )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    if not message.text:
        return
    text = message.text.strip()
    prices = {
        "Воппер": 349, "Двойной Воппер": 449, "Картошка": 149,
        "Кола": 119, "Чизбургер": 199, "Наггетсы": 179
    }
   
    if text in prices:
        user_id = message.from_user.id
        user_cart[user_id].append({
            "name": text,
            "price": prices[text]
        })
        await message.answer(f"✅ {text} добавлен в корзину!")
       
        # Показываем кнопку для просмотра корзины
        cart_items = user_cart[user_id]
        total = sum(item["price"] for item in cart_items)
       
        await message.answer(
            f"*🛒 В корзине товаров на {total}₽*\n\nНажми кнопку ниже чтобы посмотреть детали:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Посмотреть корзину", callback_data="cart")]
            ]),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "Не понял тебя, брат! Используй кнопки 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🍔 Открыть меню", callback_data="menu")]
            ])
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
