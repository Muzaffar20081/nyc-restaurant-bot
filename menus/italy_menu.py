"""
Итальянское меню
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ItalyMenu:
    def __init__(self):
        self.name = "🍕 Итальянская кухня"
        self.category = "italy"
        self.icon = "🍕"
        self.description = "Настоящая итальянская кухня от шеф-повара из Рима"
        
        self.items = [
            {
                "id": "pizza_margherita",
                "name": "Маргарита",
                "description": "Классическая пицца на тонком тесте, моцарелла, томаты, базилик",
                "price": 550,
                "size": "30 см",
                "weight": 480,
                "calories": 820,
                "cooking_time": 20
            },
            {
                "id": "pizza_pepperoni",
                "name": "Пепперони",
                "description": "Острая салями, моцарелла, томатный соус, орегано",
                "price": 650,
                "size": "30 см",
                "weight": 520,
                "calories": 890,
                "cooking_time": 22
            },
            {
                "id": "pasta_carbonara",
                "name": "Паста Карбонара",
                "description": "Спагетти, бекон, сливочный соус, пармезан, яичный желток",
                "price": 480,
                "weight": 350,
                "calories": 650,
                "cooking_time": 15
            },
            {
                "id": "lasagna",
                "name": "Лазанья Болоньезе",
                "description": "Слои пасты, мясной соус, бешамель, сыр моцарелла",
                "price": 520,
                "weight": 400,
                "calories": 720,
                "cooking_time": 25
            },
            {
                "id": "tiramisu",
                "name": "Тирамису",
                "description": "Классический итальянский десерт с маскарпоне",
                "price": 320,
                "weight": 180,
                "calories": 380,
                "cooking_time": 5
            }
        ]
    
    def get_menu_text(self):
        """Генерирует текст для меню"""
        text = f"<b>{self.name}</b>\n"
        text += f"<i>{self.description}</i>\n\n"
        text += "📋 <b>Наше меню:</b>\n\n"
        
        categories = {
            "🍕 Пицца": [item for item in self.items if "pizza" in item["id"]],
            "🍝 Паста": [item for item in self.items if "pasta" in item["id"] or "lasagna" in item["id"]],
            "🍰 Десерты": [item for item in self.items if "tiramisu" in item["id"]]
        }
        
        for category_name, items in categories.items():
            if items:
                text += f"<b>{category_name}</b>\n"
                for item in items:
                    emoji = "🍕" if "pizza" in item["id"] else "🍝" if "pasta" in item["id"] else "🍰"
                    text += (
                        f"{emoji} <b>{item['name']}</b>\n"
                        f"   💰 {item['price']}₽ | "
                        f"{item.get('size', str(item['weight']) + 'г')} | "
                        f"⏱️ {item['cooking_time']} мин\n"
                        f"   {item['description']}\n\n"
                    )
        
        return text
    
    def get_keyboard(self, show_back_button=True):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        # Группируем по категориям
        pizza_items = [item for item in self.items if "pizza" in item["id"]]
        pasta_items = [item for item in self.items if "pasta" in item["id"] or "lasagna" in item["id"]]
        dessert_items = [item for item in self.items if "tiramisu" in item["id"]]
        
        # Пицца
        if pizza_items:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍕 Выбрать пиццу",
                callback_data="show_category:pizza"
            )])
        
        # Паста
        if pasta_items:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍝 Выбрать пасту",
                callback_data="show_category:pasta"
            )])
        
        # Десерты
        if dessert_items:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍰 Десерты",
                callback_data="show_category:dessert"
            )])
        
        # Дополнительные кнопки
        keyboard_buttons.append([
            InlineKeyboardButton(text="🍷 Винная карта", callback_data="wine_list"),
            InlineKeyboardButton(text="👨‍🍳 Шеф-рекомендует", callback_data="chef_recommendation")
        ])
        
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
        item = self.get_item_details(item_id)
        if not item:
            return None
        
        extra_buttons = []
        if "pizza" in item_id:
            extra_buttons = [
                [InlineKeyboardButton(
                    text="🔍 Выбрать размер",
                    callback_data=f"select_size:{item_id}"
                )]
            ]
        
        keyboard = [
            [
                InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_to_cart:{self.category}:{item_id}"),
                InlineKeyboardButton(text="❤️ В избранное", callback_data=f"add_favorite:{self.category}:{item_id}")
            ],
            *extra_buttons,
            [
                InlineKeyboardButton(text="◀️ Назад к меню", callback_data=f"back_to_menu:{self.category}")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
