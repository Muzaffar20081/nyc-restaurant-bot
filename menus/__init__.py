# menus/__init__.py
from .burger_menu import BurgerMenu
from .pizza_menu import PizzaMenu
from .sushi_menu import SushiMenu

# Создаем экземпляры меню
burger_menu = BurgerMenu()
pizza_menu = PizzaMenu()
sushi_menu = SushiMenu()

# Словарь всех меню
ALL_MENUS = {
    "burger": burger_menu,
    "pizza": pizza_menu,
    "sushi": sushi_menu,
}

__all__ = ["burger_menu", "pizza_menu", "sushi_menu", "ALL_MENUS"]
