# menus/pizza_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class PizzaMenu:
    def __init__(self):
        self.name = "🍕 Пицца"
        self.icon = "🍕"
        self.category = "pizza"
        
        self.items = [
            {
                "id": "pizza_margherita",
                "name": "Маргарита",
                "description": "Классическая пицца с моцареллой и томатами",
                "price": 550,
                "size": "30 см"
            },
            {
                "id": "pizza_pepperoni",
                "name": "Пепперони",
                "description": "Острая салями, сыр, томатный соус",
                "price": 650,
                "size": "30 см"
            },
            {
                "id": "pizza_4cheese",
                "name": "4 Сыра",
                "description": "Смесь четырех видов сыра",
                "price": 600,
                "size": "30 см"
            },
            {
                "id": "pizza_hawaiian",
                "name": "Гавайская",
                "description": "Курица, ананас, сыр, соус",
                "price": 580,
                "size": "30 см"
            }
        ]
    
    def get_menu_text(self):
        text = f"<b>{self.name}</b>\n\n"
        for item in self.items:
            text += f"🍕 <b>{item['name']}</b>\n"
            text += f"   💰 {item['price']}₽ | 📏 {item['size']}\n"
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
