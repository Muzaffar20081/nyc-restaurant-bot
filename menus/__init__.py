# menu/__init__.py
from .burger_menu import BURGER_MENU
from .italy_menu import ITALY_MENU
from .sushi_menu import SUSHI_MENU

ALL_MENUS = {
    "burgers": BURGER_MENU,
    "italy": ITALY_MENU,
    "sushi": SUSHI_MENU,
}

def get_menu_by_category(category_id):
    return ALL_MENUS.get(category_id, [])

def find_item_by_id(item_id):
    for items in ALL_MENUS.values():
        for item in items:
            if item.get("id") == item_id:
                return item
    return None

def search_items(query):
    results = []
    query = query.lower()
    for items in ALL_MENUS.values():
        for item in items:
            if query in item["name"].lower():
                results.append(item)
    return results
