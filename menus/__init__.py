"""
Инициализация модуля меню
"""
from .burger_menu import BurgerMenu
from .italy_menu import ItalyMenu
from .sushi_menu import SushiMenu

__all__ = ['BurgerMenu', 'ItalyMenu', 'SushiMenu']

# Создаем глобальные экземпляры меню для использования во всем приложении
burger_menu = BurgerMenu()
italy_menu = ItalyMenu()
sushi_menu = SushiMenu()

# Словарь всех меню для быстрого доступа
MENUS = {
    'burger': burger_menu,
    'italy': italy_menu,
    'sushi': sushi_menu
}
