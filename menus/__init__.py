# menu/__init__.py
from .burger_menu import BURGER_MENU
from .italy_menu import ITALY_MENU
from .sushi_menu import SUSHI_MENU

# Объединяем все меню в один словарь
ALL_MENUS = {
    "burgers": BURGER_MENU,
    "pizza": ITALY_MENU,
    "sushi": SUSHI_MENU,
}

# Категории для отображения
MENU_CATEGORIES = [
    {"id": "burgers", "name": "🍔 Бургеры", "emoji": "🍔"},
    {"id": "pizza", "name": "🍕 Пицца", "emoji": "🍕"},
    {"id": "sushi", "name": "🍣 Суши", "emoji": "🍣"},
]

def get_menu_by_category(category_id):
    """Получить меню по категории"""
    return ALL_MENUS.get(category_id, [])

def get_all_categories():
    """Получить все категории меню"""
    return MENU_CATEGORIES

def find_item_by_id(item_id):
    """Найти товар по ID во всех меню"""
    for category in ALL_MENUS.values():
        for item in category:
            if item.get("id") == item_id:
                return item
    return None
