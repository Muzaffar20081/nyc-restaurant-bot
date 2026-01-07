# menus/sushi_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class SushiMenu:
    def __init__(self):
        self.name = "🍣 Суши и роллы"
        self.icon = "🍣"
        self.description = "Свежие суши и роллы от японского шеф-повара"
        
        self.items = [
            {
                "id": "roll_philadelphia",
                "name": "Роллы Филадельфия",
                "description": "Лосось, сливочный сыр, огурец, авокадо",
                "price": 450,
                "pieces": 8,
                "weight": 280,
                "calories": 380,
                "cooking_time": 12
            },
            {
                "id": "roll_california",
                "name": "Роллы Калифорния",
                "description": "Краб, огурец, авокадо, икра масаго",
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
                "description": "Ассорти из 24 кусочков",
                "price": 1200,
                "pieces": 24,
                "weight": 800,
                "calories": 1100,
                "cooking_time": 20
            }
        ]
    
    def get_menu_text(self):
        """Генерирует текст для меню"""
        text = f"<b>{self.name}</b>\n"
        text += f"<i>{self.description}</i>\n\n"
        text += "<b>Наше меню:</b>\n\n"
        
        for idx, item in enumerate(self.items, 1):
            emoji = "🍣" if "roll" in item["id"] else "🍙" if "sushi" in item["id"] else "🎌"
            pieces_info = f" | 🍽️ {item['pieces']} шт" if 'pieces' in item else ""
            
            text += (
                f"{idx}. {emoji} <b>{item['name']}</b>\n"
                f"   💰 {item['price']}₽{pieces_info} | ⚖️ {item['weight']}г\n"
                f"   ⏱️ {item['cooking_time']} мин | {item['description']}\n\n"
            )
        
        return text
    
    def get_keyboard(self):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        for item in self.items:
            emoji = "🍣" if "roll" in item["id"] else "🍙" if "sushi" in item["id"] else "🎌"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{emoji} {item['name']} - {item['price']}₽",
                    callback_data=f"menu_item:sushi:{item['id']}"
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
