import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# from menus import MENUS, burger_menu, italy_menu, sushi_menu   # ← предполагается, что этот файл существует

# Замените на реальный токен!
bot = Bot(token="ВАШ_ТОКЕН_ЗДЕСЬ")
dp = Dispatcher()

# Временное хранилище корзин (в продакшене → Redis / БД)
user_carts = {}


@dp.message(CommandStart())
async def start(message: types.Message):
    user = message.from_user

    builder = InlineKeyboardBuilder()

    # Пример — предполагаем, что у burger_menu, italy_menu, sushi_menu есть .icon, .name, .description
    buttons = [
        (f"{burger_menu.icon} {burger_menu.name}", "show_menu:burger"),
        (f"{italy_menu.icon} {italy_menu.name}",   "show_menu:italy"),
        (f"{sushi_menu.icon} {sushi_menu.name}",   "show_menu:sushi"),
        ("🎯 Рекомендации", "recommendations"),
        ("⭐ Избранное", "favorites"),
        ("📊 Топ продаж", "top_sales")
    ]

    for text, cb in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=cb))

    builder.adjust(2, 2, 1, 1)

    builder.row(
        InlineKeyboardButton(text="ℹ️ О нас", callback_data="about"),
        InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")
    )

    welcome_text = f"""
🌟 <b>Добро пожаловать, {user.first_name}!</b> 🌟
🍽️ <b>Food Delivery</b> — ваш гастрономический гид!

✨ <b>Что у нас есть:</b>
• {burger_menu.icon} <b>{burger_menu.name}</b> — {burger_menu.description}
• {italy_menu.icon}  <b>{italy_menu.name}</b>  — {italy_menu.description}
• {sushi_menu.icon}  <b>{sushi_menu.name}</b>  — {sushi_menu.description}

🎁 <b>Специальные предложения:</b>
🔥 Первый заказ — <b>20%</b> скидка
🚚 Бесплатная доставка от <b>1500 ₽</b>
⏰ Доставка за <b>30 минут</b> или бесплатно!

👇 <b>Выберите кухню или навигацию:</b>
"""

    await message.answer_photo(
        photo="https://via.placeholder.com/1200x400/FF6B6B/FFFFFF?text=Food+Delivery",
        caption=welcome_text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data.startswith("show_menu:"))
async def show_menu_handler(callback: types.CallbackQuery):
    _, menu_type = callback.data.split(":", 1)
    menu = MENUS.get(menu_type)

    if not menu:
        await callback.answer("Меню не найдено", show_alert=True)
        return

    # Здесь должна быть ваша реализация menu.get_menu_text()
    # Для примера:
    menu_items_text = "\n".join(f"• {item['name']} — {item['price']} ₽" for item in menu.items[:8])

    text = f"""
{menu.icon * 3} <b>{menu.name.upper()}</b> {menu.icon * 3}

📋 <b>КАТАЛОГ БЛЮД</b>
━━━━━━━━━━━━━━━━━━━━
{menu_items_text}

💰 Цены от: <b>{min(i['price'] for i in menu.items)} ₽</b>
⏱️ Среднее время: <b>~15–35 мин</b>
⭐ Рейтинг: <b>★★★★.8</b>
"""

    builder = InlineKeyboardBuilder()

    for item in menu.items:
        emoji = "🍽️"  # здесь ваша логика выбора эмодзи
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {item['name']} · {item['price']}₽",
            callback_data=f"menu_item:{menu_type}:{item['id']}"
        ))

    builder.adjust(1)

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("add_to_cart:"))
async def add_to_cart_handler(callback: types.CallbackQuery):
    try:
        _, menu_type, item_id, qty_str = callback.data.split(":")
        qty = int(qty_str)
    except:
        await callback.answer("Ошибка формата", show_alert=True)
        return

    # Дальше ваша логика добавления в корзину...
    # user_carts[callback.from_user.id] = ...

    await callback.answer(f"Добавлено {qty} шт ✓", show_alert=True)


@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    # Здесь логика возврата на главное меню
    # Можно просто вызвать start() но с edit
    await callback.message.edit_text(
        "Возвращаемся на главную...",
        parse_mode="HTML"
    )
    await asyncio.sleep(0.6)
    await start(callback.message)  # не идеально, но для прототипа сойдёт


async def main():
    print("🚀 Food Delivery Bot запущен...")
    await dp.start_polling(bot, allowed_updates=types.default_allowed_updates)


if __name__ == "__main__":
    asyncio.run(main())
