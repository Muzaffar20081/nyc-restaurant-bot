# debug_all.py
import os
import sys
import traceback

print("=" * 60)
print("🛠️  ПОЛНАЯ ДИАГНОСТИКА")
print("=" * 60)

# 1. Проверяем структуру
print("\n📁 ФАЙЛОВАЯ СТРУКТУРА:")
current_dir = os.listdir('.')
print(f"Текущая папка: {current_dir}")

menu_files = []
if os.path.exists('menu'):
    menu_files = os.listdir('menu')
    print(f"Папка 'menu': {menu_files}")
else:
    print("❌ Папка 'menu' не существует!")

# 2. Проверяем config.py
print("\n⚙️ CONFIG.PY:")
try:
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"✅ config.py существует ({len(content)} символов)")
        
        # Ищем токен
        if 'BOT_TOKEN' in content:
            print("✅ BOT_TOKEN найден")
        else:
            print("❌ BOT_TOKEN не найден!")
            
        if 'CUISINES' in content:
            print("✅ CUISINES найден")
        else:
            print("❌ CUISINES не найден!")
            
except FileNotFoundError:
    print("❌ config.py не существует!")
except Exception as e:
    print(f"❌ Ошибка чтения: {e}")

# 3. Проверяем menu/__init__.py
print("\n🍔 MENU/__INIT__.PY:")
try:
    with open('menu/__init__.py', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"✅ __init__.py существует ({len(content)} символов)")
        
        # Проверяем ключевые функции
        required = ['get_menu_by_category', 'find_item_by_id', 'search_items']
        for func in required:
            if func in content:
                print(f"✅ Функция {func} найдена")
            else:
                print(f"❌ Функция {func} не найдена!")
                
except FileNotFoundError:
    print("❌ menu/__init__.py не существует!")
except Exception as e:
    print(f"❌ Ошибка чтения: {e}")

# 4. Тест импортов
print("\n🔄 ТЕСТ ИМПОРТОВ:")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import BOT_TOKEN, CUISINES
    print(f"✅ config.py импортирован успешно")
    print(f"   Токен: {BOT_TOKEN[:15]}...")
    print(f"   Кухни: {CUISINES}")
except Exception as e:
    print(f"❌ Ошибка импорта config.py: {e}")

try:
    from menu import get_menu_by_category
    print(f"✅ menu импортирован успешно")
    
    # Тестируем каждую кухню
    test_cuisines = list(CUISINES.keys()) if 'CUISINES' in locals() else ['burgers', 'italy', 'sushi']
    
    for cuisine in test_cuisines:
        try:
            items = get_menu_by_category(cuisine)
            print(f"   {cuisine}: {len(items)} товаров")
            if items:
                for item in items[:2]:
                    print(f"     - {item.get('name', '?')}: {item.get('price', 0)}₽")
        except Exception as e:
            print(f"   {cuisine}: ОШИБКА - {e}")
            
except Exception as e:
    print(f"❌ Ошибка импорта menu: {e}")
    traceback.print_exc()

# 5. Проверяем aiogram
print("\n🤖 AIOGRAM:")
try:
    import aiogram
    print(f"✅ aiogram установлен, версия: {aiogram.__version__}")
    
    # Проверяем основные компоненты
    from aiogram import Bot, Dispatcher
    print("✅ Основные классы доступны")
    
except ImportError as e:
    print(f"❌ aiogram не установлен: {e}")
    print("   Установите: pip install aiogram")
except Exception as e:
    print(f"❌ Ошибка aiogram: {e}")

print("\n" + "=" * 60)
print("Диагностика завершена")
print("=" * 60)

# 6. Просим ввести команду для теста
print("\n🚀 Чтобы запустить простейший тест, введите:")
print("   1. python debug_all.py")
print("   2. Пришлите ВЕСЬ текст выше")
print("   3. Что пишет python improved_bot.py?")
