from menus import MENUS, burger_menu, italy_menu, sushi_menu

# Пример обработчика команды /start
@dp.message(CommandStart())
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=burger_menu.name, callback_data=f"show_menu:burger")],
        [InlineKeyboardButton(text=italy_menu.name, callback_data=f"show_menu:italy")],
        [InlineKeyboardButton(text=sushi_menu.name, callback_data=f"show_menu:sushi")]
    ])
    
    await message.answer(
        "🍽️ <b>Добро пожаловать в Food Delivery!</b>\n\n"
        "Выберите кухню:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

# Пример обработчика выбора меню
@dp.callback_query(lambda call: call.data.startswith("show_menu:"))
async def show_menu_handler(call: types.CallbackQuery):
    menu_type = call.data.split(":")[1]
    menu = MENUS.get(menu_type)
    
    if menu:
        await call.message.edit_text(
            menu.get_menu_text(),
            parse_mode="HTML",
            reply_markup=menu.get_keyboard()
        )
    await call.answer()

# Пример обработчика выбора блюда
@dp.callback_query(lambda call: call.data.startswith("menu_item:"))
async def show_item_handler(call: types.CallbackQuery):
    _, menu_type, item_id = call.data.split(":")
    menu = MENUS.get(menu_type)
    
    if menu:
        item = menu.get_item_details(item_id)
        if item:
            text = (
                f"<b>{item['name']}</b>\n\n"
                f"<i>{item['description']}</i>\n\n"
                f"💰 <b>Цена:</b> {item['price']}₽\n"
            )
            
            # Добавляем дополнительную информацию в зависимости от типа меню
            if 'weight' in item:
                text += f"⚖️ <b>Вес:</b> {item['weight']}г\n"
            if 'pieces' in item:
                text += f"🍽️ <b>Количество:</b> {item['pieces']} шт\n"
            if 'size' in item:
                text += f"📏 <b>Размер:</b> {item['size']}\n"
            
            text += f"⏱️ <b>Приготовление:</b> {item['cooking_time']} мин\n"
            text += f"🔥 <b>Калории:</b> {item['calories']} ккал"
            
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=menu.get_item_keyboard(item_id)
            )
    await call.answer()
