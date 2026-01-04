"""
Меню бургеров
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class BurgerMenu:
    def __init__(self):
        self.name = "🍔 Бургеры"
        self.category = "burger"
        self.icon = "🍔"
        self.description = "Сочные бургеры с авторскими соусами и свежими овощами"
        
        self.items = [
            {
                "id": "burger_classic",
                "name": "Классический бургер",
                "description": "Говяжья котлета 200г, салат айсберг, помидор, красный лук, соленые огурчики, фирменный соус",
                "price": 350,
                "weight": 380,
                "calories": 560,
                "cooking_time": 15
            },
            {
                "id": "burger_cheese",
                "name": "Двойной чизбургер",
                "description": "Две говяжьи котлеты, три ломтика чеддера, бекон, карамелизированный лук, соус BBQ",
                "price": 490,
                "weight": 450,
                "calories": 720,
                "cooking_time": 18
            },
            {
                "id": "burger_spicy",
                "name": "Острый бургер",
                "description": "Котлета из мраморной говядины, халапеньо, острый сыр, салат романо, соус шрирача",
                "price": 420,
                "weight": 400,
                "calories": 580,
                "cooking_time": 16
            },
            {
                "id": "burger_chicken",
                "name": "Чикенбургер",
                "description": "Куриная котлета в панировке, салат, помидор, соус тартар",
                "price": 380,
                "weight": 360,
                "calories": 480,
                "cooking_time": 14
            },
            {
                "id": "burger_vegan",
                "name": "Веганский бургер",
                "description": "Растительная котлета, авокадо, микрозелень, томаты черри, веганский майонез",
                "price": 390,
                "weight": 350,
                "calories": 420,
                "cooking_time": 12
            }
        ]
    
    def get_menu_text(self):
        """Генерирует текст для меню"""
        text = f"<b>{self.name}</b>\n"
        text += f"<i>{self.description}</i>\n\n"
        text += "📋 <b>Доступные позиции:</b>\n\n"
        
        for idx, item in enumerate(self.items, 1):
            text += (
                f"{idx}. <b>{item['name']}</b>\n"
                f"   💰 <b>{item['price']}₽</b> | ⚖️ {item['weight']}г | 🔥 {item['calories']} ккал\n"
                f"   ⏱️ Приготовление: {item['cooking_time']} мин\n"
                f"   {item['description']}\n\n"
            )
        
        return text
    
    def get_keyboard(self, show_back_button=True):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        # Кнопки для каждого бургера (по 2 в ряд)
        row = []
        for item in self.items:
            button = InlineKeyboardButton(
                text=f"{item['name']} - {item['price']}₽",
                callback_data=f"menu_item:{self.category}:{item['id']}"
            )
            row.append(button)
            if len(row) == 2:
                keyboard_buttons.append(row)
                row = []
        
        if row:  # Если осталась неполная строка
            keyboard_buttons.append(row)
        
        # Кнопки действий
        keyboard_buttons.append([
            InlineKeyboardButton(text="📞 Связаться с поваром", callback_data=f"contact:{self.category}"),
            InlineKeyboardButton(text="⭐ Хиты продаж", callback_data=f"popular:{self.category}")
        ])
        
        # Кнопка возврата если нужно
        if show_back_button:
            keyboard_buttons.append([
                InlineKeyboardButton(text="◀️ Назад к ресторанам", callback_data="back_to_restaurants")
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    def get_item_details(self, item_id):
        """Получает детальную информацию о блюде"""
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None
    
    def get_item_keyboard(self, item_id):
        """Клавиатура для конкретного блюда"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_to_cart:{self.category}:{item_id}"),
                InlineKeyboardButton(text="⭐ Добавить в избранное", callback_data=f"add_favorite:{self.category}:{item_id}")
            ],
            [
                InlineKeyboardButton(text="📋 Полный состав", callback_data=f"ingredients:{self.category}:{item_id}"),
                InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews:{self.category}:{item_id}")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад к меню", callback_data=f"back_to_menu:{self.category}")
            ]
        ])
