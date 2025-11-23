# bot.py — УЛУЧШЕННАЯ ВЕРСИЯ С ПОЛНОЙ КОРЗИНОЙ И ЗАКАЗАМИ
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Хранилище данных (в продакшене лучше использовать БД)
user_cart = defaultdict(list)
user_orders = defaultdict(list)

# Словарь с товарами
ITEMS = {
    "Воппер": 349,
    "Двойной Воппер": 449,
    "Картошка": 149,
    "Кола": 119,
    "Чизбургер": 199,
    "Наггетсы": 179
}

class OrderStates(StatesGroup):
    waiting_for_item = State()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer_photo(
        "https://i.ibb.co/m9kJ7B/welcome-burger.png",
        caption=f"Здарова, {message.from_user.first_name}!\n\n*BURGER KING 2025 ЖИВОЙ НА МАКСИМАЛКАХ*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Меню", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "menu")
async def menu(call: types.CallbackQuery):
    menu_text = "*🍔 МЕНЮ BURGER KING 2025*\n\n"
    for item, price in ITEMS.items():
        menu_text += f"• {item} — {price}₽\n"
    
    menu_text += "\nВыбери что хочешь заказать:"
    
    keyboard = []
    items_list = list(ITEMS.keys())
    # Создаем кнопки в 2 колонки
    for i in range(0, len(items_list), 2):
        row = []
        for j in range(2):
            if i + j < len(items_list):
                item = items_list[i + j]
                row.append(InlineKeyboardButton(text=item, callback_data=f"add_{item}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    
    await call.message.edit_caption(
        caption=menu_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add_to_cart(call: types.CallbackQuery):
    item_name = call.data[4:]  # Убираем "add_"
    user_id = call.from_user.id
    
    if item_name in ITEMS:
        user_cart[user_id].append({
            "name": item_name,
            "price": ITEMS[item_name]
        })
        
        await call.answer(f"✅ {item_name} добавлен в корзину!")
        
        # Показываем обновленное меню
        await menu(call)
    else:
        await call.answer("❌ Товар не найден")

@dp.callback_query(lambda c: c.data == "cart")
async def show_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
    
    if not cart_items:
        caption = "*🛒 Корзина пуста!*\n\nЗайди в меню и выбери что-нибудь вкусненькое 🍔"
        keyboard = [[InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart_items)
        caption = "*🛒 Твоя корзина:*\n\n"
        
        # Группируем одинаковые товары
        item_counts = {}
        for item in cart_items:
            name = item["name"]
            if name in item_counts:
                item_counts[name]["count"] += 1
                item_counts[name]["total_price"] += item["price"]
            else:
                item_counts[name] = {
                    "count": 1,
                    "price": item["price"],
                    "total_price": item["price"]
                }
        
        for name, data in item_counts.items():
            caption += f"• {name} ×{data['count']} — {data['total_price']}₽\n"
        
        caption += f"\n💵 *Итого: {total}₽*"
        
        keyboard = [
            [InlineKeyboardButton(text="🧹 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
            [InlineKeyboardButton(text="🍔 Продолжить покупки", callback_data="menu")]
        ]
    
    await call.message.edit_caption(
        caption=caption,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_cart[user_id] = []
    
    await call.answer("🧹 Корзина очищена!")
    await show_cart(call)

@dp.callback_query(lambda c: c.data == "checkout")
async def checkout(call: types.CallbackQuery):
    user_id = call.from_user.id
    cart_items = user_cart[user_id]
    
    if not cart_items:
        await call.answer("❌ Корзина пуста!")
        return
    
    total = sum(item["price"] for item in cart_items)
    
    # Сохраняем заказ
    order_id = len(user_orders[user_id]) + 1
    user_orders[user_id].append({
        "id": order_id,
        "items": cart_items.copy(),
        "total": total,
        "status": "принят"
    })
    
    # Очищаем корзину
    user_cart[user_id] = []
    
    order_text = f"✅ *Заказ #{order_id} принят!*\n\n"
    for item in cart_items:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💵 Сумма: {total}₽\n📱 Статус: принят\n\nОжидай уведомление о готовности!"
    
    await call.message.edit_caption(
        caption=order_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="my_orders")]
        ]),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(lambda c: c.data == "my_orders")
async def my_orders(call: types.CallbackQuery):
    user_id = call.from_user.id
    orders = user_orders[user_id]
    
    if not orders:
        caption = "📦 *У тебя пока нет заказов*\n\nСделай первый заказ в меню! 🍔"
        keyboard = [[InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]]
    else:
        caption = "📦 *Твои заказы:*\n\n"
        for order in orders[-5:]:  # Показываем последние 5 заказов
            caption += f"*Заказ #{order['id']}*\n"
            caption += f"💵 Сумма: {order['total']}₽\n"
            caption += f"📱 Статус: {order['status']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton(text="🍔 Новый заказ", callback_data="menu")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ]
    
    await call.message.edit_caption(
        caption=caption,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await call.answer()

@dp.message()
async def handle_text(message: types.Message):
    # Если пользователь пишет название товара текстом
    text = message.text.strip()
    
    if text in ITEMS:
        user_id = message.from_user.id
        user_cart[user_id].append({
            "name": text,
            "price": ITEMS[text]
        })
        await message.answer(f"✅ {text} добавлен в корзину!")
        await show_cart_after_text(message)
    else:
        await message.answer("Не понял тебя, брат! Используй кнопки меню 👇")

async def show_cart_after_text(message: types.Message):
    user_id = message.from_user.id
    cart_items = user_cart[user_id]
    
    if not cart_items:
        text = "*🛒 Корзина пуста!*"
        keyboard = [[InlineKeyboardButton(text="🍔 Меню", callback_data="menu")]]
    else:
        total = sum(item["price"] for item in cart_items)
        text = f"*🛒 В корзине товаров на {total}₽*\n\nНажми кнопку ниже чтобы посмотреть детали:"
        keyboard = [[InlineKeyboardButton(text="🛒 Посмотреть корзину", callback_data="cart")]]
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
