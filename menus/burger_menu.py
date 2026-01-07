# menus/burger_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class BurgerMenu:
    def __init__(self):
        self.name = "🍔 Бургеры NYC"
        self.icon = "🍔"
        self.description = "Американские бургеры в нью-йоркском стиле"
        
        self.items = [
            {
                "id": "burger_classic",
                "name": "Классический NYC бургер",
                "description": "Говяжья котлета 200г, салат, помидор, лук, соленые огурчики, фирменный соус",
                "price": 350,
                "weight": 380,
                "calories": 560,
                "cooking_time": 15
            },
            {
                "id": "burger_cheese",
                "name": "Чизбургер с беконом",
                "description": "Двойной сыр, бекон, карамелизированный лук, соус BBQ",
                "price": 490,
                "weight": 450,
                "calories": 720,
                "cooking_time": 18
            },
            {
                "id": "burger_spicy",
                "name": "Острый бургер",
                "description": "Котлета из мраморной говядины, халапеньо, острый сыр",
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
            }
        ]
    
    def get_menu_text(self):
        """Генерирует текст для меню"""
        text = f"<b>{self.name}</b>\n"
        text += f"<i>{self.description}</i>\n\n"
        text += "<b>Наше меню:</b>\n\n"
        
        for idx, item in enumerate(self.items, 1):
            text += (
                f"{idx}. <b>{item['name']}</b>\n"
                f"   💰 {item['price']}₽ | ⚖️ {item['weight']}г | ⏱️ {item['cooking_time']} мин\n"
                f"   {item['description']}\n\n"
            )
        
        return text
    
    def get_keyboard(self):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        for item in self.items:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{item['name']} - {item['price']}₽",
                    callback_data=f"menu_item:burger:{item['id']}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    def get_item_details(self, item_id):
        """Получает детальную информацию о блюде"""
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None
