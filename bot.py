# test_import.py
try:
    from menu import MENU_CATEGORIES, get_menu_by_category, find_item_by_id
    print("✅ Импорты работают!")
    print(f"Категории: {MENU_CATEGORIES}")
    
    # Проверим меню
    burgers = get_menu_by_category("burgers")
    print(f"🍔 Найдено бургеров: {len(burgers)}")
    
    # Проверим поиск товара
    item = find_item_by_id("whopper")
    print(f"🔍 Найден товар: {item['name'] if item else 'Не найден'}")
    
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
