# menus/burger_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class BurgerMenu:
    def __init__(self):
        self.name = "🍔 Бургеры"
        self.icon = "🍔"
        self.category = "burger"
        
        self.items = [
            {
                "id": "burger_classic",
                "name": "Классический бургер",
                "description": "Говяжья котлета 200г, салат, помидор, сыр, соус",
                "price": 350,
                "weight": 380
            },
            {
                "id": "burger_cheese",
                "name": "Двойной чизбургер",
                "description": "Две котлеты, три слоя сыра, бекон, BBQ соус",
                "price": 450,
                "weight": 420
            },
            {
                "id": "burger_spicy",
                "name": "Острый бургер",
                "description": "Котлета из мраморной говядины, халапеньо, острый соус",
                "price": 380,
                "weight": 400
            },
            {
                "id": "burger_chicken",
                "name": "Чикенбургер",
                "description": "Куриная котлета в панировке, салат, соус тартар",
                "price": 320,
                "weight": 350
            }
        ]
    
    def get_menu_text(self):
        text = f"<b>{self.name}</b>\n\n"
        for item in self.items:
            text += f"🍔 <b>{item['name']}</b>\n"
            text += f"   💰 {item['price']}₽ | ⚖️ {item['weight']}г\n"
            text += f"   {item['description']}\n\n"
        return text
    
    def get_keyboard(self):
        buttons = []
        for item in self.items:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{item['name']} - {item['price']}₽",
                    callback_data=f"item:{self.category}:{item['id']}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
        ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def get_item(self, item_id):
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None
