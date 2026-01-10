# menus/sushi_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class SushiMenu:
    def __init__(self):
        self.name = "🍣 Суши и роллы"
        self.icon = "🍣"
        self.category = "sushi"
        
        self.items = [
            {
                "id": "roll_philadelphia",
                "name": "Филадельфия",
                "description": "Лосось, сливочный сыр, огурец, авокадо",
                "price": 450,
                "pieces": 8
            },
            {
                "id": "roll_california",
                "name": "Калифорния",
                "description": "Краб, огурец, авокадо, икра масаго",
                "price": 420,
                "pieces": 8
            },
            {
                "id": "roll_baked",
                "name": "Запеченные роллы",
                "description": "Лосось под сырной корочкой",
                "price": 480,
                "pieces": 8
            },
            {
                "id": "set_sakura",
                "name": "Сет 'Сакура'",
                "description": "Ассорти 24 шт: роллы и суши",
                "price": 850,
                "pieces": 24
            }
        ]
    
    def get_menu_text(self):
        text = f"<b>{self.name}</b>\n\n"
        for item in self.items:
            text += f"🍣 <b>{item['name']}</b>\n"
            text += f"   💰 {item['price']}₽ | 🍽️ {item['pieces']} шт\n"
            text += f"   {item['description']}\n\n"
        return text
    
    def get_keyboard(self):
        buttons = []
        for item in self.items:
            emoji = "🍣" if "roll" in item["id"] else "🎌"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{emoji} {item['name']} - {item['price']}₽",
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
