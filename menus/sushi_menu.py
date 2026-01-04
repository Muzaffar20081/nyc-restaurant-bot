"""
Меню суши и роллов
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class SushiMenu:
    def __init__(self):
        self.name = "🍣 Японская кухня"
        self.category = "sushi"
        self.icon = "🍣"
        self.description = "Свежие суши и роллы от японского шеф-повара"
        
        self.items = [
            {
                "id": "roll_philadelphia",
                "name": "Филадельфия",
                "description": "Лосось, сливочный сыр, огурец, авокадо, нори, рис",
                "price": 450,
                "pieces": 8,
                "weight": 280,
                "calories": 380,
                "cooking_time": 12
            },
            {
                "id": "roll_california",
                "name": "Калифорния",
                "description": "Краб, огурец, авокадо, масаго, кунжут, рис снаружи",
                "price": 420,
                "pieces": 8,
                "weight": 260,
                "calories": 350,
                "cooking_time": 10
            },
            {
                "id": "sushi_salmon",
                "name": "Суши с лососем",
                "description": "Свежий норвежский лосось на рисе",
                "price": 80,
                "pieces": 1,
                "weight": 40,
                "calories": 60,
                "cooking_time": 8
            },
            {
                "id": "set_sakura",
                "name": "Сет 'Сакура'",
                "description": "Ассорти из 24 кусочков: 8 Филадельфия, 8 Калифорния, 8 суши",
                "price": 1200,
                "pieces": 24,
                "weight": 800,
                "calories": 1100,
                "cooking_time": 20
            },
            {
                "id": "tempura_shrimp",
                "name": "Темпура с креветкой",
                "description": "Креветки в хрустящем тесте с соусом терияки",
                "price": 380,
                "weight": 220,
                "calories": 320,
                "cooking_time": 15
            }
        ]
    
    def get_menu_text(self):
        """Генерирует текст для меню"""
        text = f"<b>{self.name}</b>\n"
        text += f"<i>{self.description}</i>\n\n"
        text += "📋 <b>Наше предложение:</b>\n\n"
        
        for idx, item in enumerate(self.items, 1):
            emoji = "🍣" if "sushi" in item["id"] else "🍤" if "tempura" in item["id"] else "🎌" if "set" in item["id"] else "🍙"
            pieces_info = f" | 🍽️ {item['pieces']} шт" if 'pieces' in item else ""
            
            text += (
                f"{emoji} <b>{item['name']}</b>\n"
                f"   💰 <b>{item['price']}₽</b>{pieces_info} | ⚖️ {item['weight']}г\n"
                f"   ⏱️ Приготовление: {item['cooking_time']} мин\n"
                f"   {item['description']}\n\n"
            )
        
        # Добавляем информацию о акциях
        text += "\n🎌 <b>Специальные предложения:</b>\n"
        text += "• При заказе от 1500₽ — бесплатная доставка\n"
        text += "• Второй сет со скидкой 20%\n"
        text += "• Бесплатный мисо-суп к каждому заказу\n"
        
        return text
    
    def get_keyboard(self, show_back_button=True):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        # Роллы и суши отдельно
        rolls = [item for item in self.items if "roll" in item["id"]]
        sushi_items = [item for item in self.items if "sushi" in item["id"] and "set" not in item["id"]]
        sets = [item for item in self.items if "set" in item["id"]]
        hot_dishes = [item for item in self.items if "tempura" in item["id"]]
        
        # Категории
        if rolls:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍣 Роллы",
                callback_data="show_category:rolls"
            )])
        
        if sushi_items:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍙 Суши",
                callback_data="show_category:sushi"
            )])
        
        if sets:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🎌 Сеты",
                callback_data="show_category:sets"
            )])
        
        if hot_dishes:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🍤 Горячие блюда",
                callback_data="show_category:hot"
            )])
        
        # Специальные кнопки
        keyboard_buttons.append([
            InlineKeyboardButton(text="📦 Собрать свой сет", callback_data="build_your_set"),
            InlineKeyboardButton(text="🎁 Акции", callback_data="promotions")
        ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🥢 Палочки обучение", callback_data="chopsticks_tutorial"),
            InlineKeyboardButton(text="🎌 Японский этикет", callback_data="etiquette")
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
        
        # Для суши добавляем кнопку выбора количества
        if "sushi" in item_id and "set" not in item_id:
            extra_buttons.append([
                InlineKeyboardButton(text="➖", callback_data=f"decrease:{item_id}"),
                InlineKeyboardButton(text="1 шт", callback_data=f"quantity:{item_id}:1"),
                InlineKeyboardButton(text="➕", callback_data=f"increase:{item_id}")
            ])
        
        # Для сетов добавляем кнопку изменения состава
        if "set" in item_id:
            extra_buttons.append([
                InlineKeyboardButton(
                    text="🔧 Настроить состав",
                    callback_data=f"customize_set:{item_id}"
                )
            ])
        
        keyboard = [
            *extra_buttons,
            [
                InlineKeyboardButton(text="➕ Добавить в корзину", callback_data=f"add_to_cart:{self.category}:{item_id}"),
                InlineKeyboardButton(text="❤️ В избранное", callback_data=f"add_favorite:{self.category}:{item_id}")
            ],
            [
                InlineKeyboardButton(text="🍱 Похожие блюда", callback_data=f"similar:{item_id}"),
                InlineKeyboardButton(text="⭐ Отзывы", callback_data=f"reviews:{item_id}")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад к меню", callback_data=f"back_to_menu:{self.category}")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
