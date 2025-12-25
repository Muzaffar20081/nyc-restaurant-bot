# menus/__init__.py
from .burger_menu import BURGER_MENU
from .italy_menu import ITALY_MENU
from .sushi_menu import SUSHI_MENU

MENU_BY_CUISINE = {
    "burgers": BURGER_MENU,
    "italy":   ITALY_MENU,
    "sushi":   SUSHI_MENU
}
