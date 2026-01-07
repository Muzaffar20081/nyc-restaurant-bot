# menus/italy_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ItalyMenu:
    def __init__(self):
        self.name = "🍕 Итальянская кухня"
        self.icon = "🍕"
        self.description = "Настоящая итальянская кухня от шеф-повара"
        
        self.items = [
            {
                "id": "pizza_margherita",
                "name": "Пицца Маргарита",
                "description": "Классическая пицца с томатами и моцареллой",
                "price": 550,
                "size": "30 см",
                "weight": 480,
                "calories": 820,
                "cooking_time": 20
            },
            {
                "id": "pizza_pepperoni",
                "name": "Пицца Пепперони",
                "description": "Острая салями, моцарелла, томатный соус",
                "price": 650,
                "size": "30 см",
                "weight": 520,
                "calories": 890,
                "cooking_time": 22
            },
            {
                "id": "pasta_carbonara",
                "name": "Паста Карбонара",
                "description": "Спагетти, бекон, сливочный соус, пармезан",
                "price": 480,
                "weight": 350,
                "calories": 650,
                "cooking_time": 15
            },
            {
                "id": "tiramisu",
                "name": "Тирамису",
                "description": "Классический итальянский десерт",
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
        text += "<b>Наше меню:</b>\n\n"
        
        for idx, item in enumerate(self.items, 1):
            emoji = "🍕" if "pizza" in item["id"] else "🍝" if "pasta" in item["id"] else "🍰"
            size_info = f" | 📏 {item['size']}" if 'size' in item else ""
            
            text += (
                f"{idx}. {emoji} <b>{item['name']}</b>\n"
                f"   💰 {item['price']}₽ | ⚖️ {item['weight']}г{size_info}\n"
                f"   ⏱️ {item['cooking_time']} мин | {item['description']}\n\n"
            )
        
        return text
    
    def get_keyboard(self):
        """Создает клавиатуру для меню"""
        keyboard_buttons = []
        
        for item in self.items:
            emoji = "🍕" if "pizza" in item["id"] else "🍝" if "pasta" in item["id"] else "🍰"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{emoji} {item['name']} - {item['price']}₽",
                    callback_data=f"menu_item:italy:{item['id']}"
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
