# menus/__init__.py
from .burger_menu import BurgerMenu
from .italy_menu import ItalyMenu
from .sushi_menu import SushiMenu

# Создаем экземпляры меню
burger_menu = BurgerMenu()
italy_menu = ItalyMenu()
sushi_menu = SushiMenu()

# Словарь для быстрого доступа
MENUS = {
    'burger': burger_menu,
    'italy': italy_menu,
    'sushi': sushi_menu
}

__all__ = ['burger_menu', 'italy_menu', 'sushi_menu', 'MENUS']
