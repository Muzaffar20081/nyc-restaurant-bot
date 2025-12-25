# menus/__init__.py
from .burger_menu import ALL_ITEMS as BURGER_ITEMS, MENU_TEXT as BURGER_TEXT
from .italy_menu import ALL_ITEMS as ITALY_ITEMS, MENU_TEXT as ITALY_TEXT
from .sushi_menu import ALL_ITEMS as SUSHI_ITEMS, MENU_TEXT as SUSHI_TEXT

MENU_BY_CUISINE = {
    "burgers": {
        "name": "🍔 Бургер-хоус",
        "items": BURGER_ITEMS,
        "text": BURGER_TEXT
    },
    "italy": {
        "name": "🍕 Итальянская кухня",
        "items": ITALY_ITEMS,
        "text": ITALY_TEXT
    },
    "sushi": {
        "name": "🍣 Суши-бар Токио",
        "items": SUSHI_ITEMS,
        "text": SUSHI_TEXT
    }
}
