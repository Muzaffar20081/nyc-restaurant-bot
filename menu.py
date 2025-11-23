# menu.py - ЗАГРУЗКА МЕНЮ ДЛЯ ТЕКУЩЕГО РЕСТОРАНА
from restaurants import get_restaurant  # ИМПОРТ ИЗ restaurants.py
from config import RESTAURANT_ID

# Загружаем данные ресторана
restaurant_data = get_restaurant(RESTAURANT_ID)

if restaurant_data:
    CATEGORIES = restaurant_data["categories"]
    MENU_TEXT = restaurant_data["welcome_text"]
    RESTAURANT_NAME = restaurant_data["name"]
    CONTACT_INFO = restaurant_data["contact_info"]
    DELIVERY_TIME = restaurant_data["delivery_time"]
    MIN_ORDER = restaurant_data["min_order"]
else:
    # Данные по умолчанию (если ресторан не найден)
    CATEGORIES = {
        "🍔 Бургеры": {
            "Воппер": 349,
            "Чизбургер": 199
        },
        "🍟 Закуски": {
            "Картошка Фри": 149
        }
    }
    MENU_TEXT = "🍕 *РЕСТОРАН*\n\nДобро пожаловать!"
    RESTAURANT_NAME = "Ресторан"
    CONTACT_INFO = "📞 +1 (555) 000-0000\n📍 ул. Центральная, 1"
    DELIVERY_TIME = "30-45 минут"
    MIN_ORDER = 0

# Создаем общий словарь всех товаров
ALL_ITEMS = {}
for category_items in CATEGORIES.values():
    ALL_ITEMS.update(category_items)
