# check_json.py - проверяет правильность JSON файла

import json
import os

def check_restaurants_json():
    print("🔍 Проверка файла restaurants.json...")
    
    # Проверяем существование файла
    if not os.path.exists('restaurants.json'):
        print("❌ Файл restaurants.json не найден!")
        return False
    
    try:
        # Пробуем загрузить JSON
        with open('restaurants.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON файл корректен!")
        print(f"🍽 Загружено ресторанов: {len(data)}")
        
        # Выводим информацию о ресторанах
        for resto_id, resto_info in data.items():
            print(f"\n📋 {resto_info['name']} (ID: {resto_id})")
            print(f"   Приветствие: {resto_info['welcome']}")
            print(f"   Категории: {len(resto_info['categories'])}")
            
            for category, items in resto_info['categories'].items():
                print(f"     - {category}: {len(items)} блюд")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате JSON: {e}")
        print("\n💡 Совет: Проверь:")
        print("   - Лишние или недостающие запятые")
        print("   - Незакрытые кавычки или скобки")
        print("   - Правильную структуру массива")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def check_bot_loading():
    print("\n🔍 Проверка загрузки в боте...")
    try:
        from database import load_restaurants
        
        restaurants = load_restaurants()
        print(f"🤖 Бот загрузил ресторанов: {len(restaurants)}")
        
        if restaurants:
            print("📝 Список ресторанов в боте:")
            for resto_id, resto_info in restaurants.items():
                print(f"   - {resto_info['name']} (ID: {resto_id})")
        else:
            print("⚠️ Бот не загрузил ни одного ресторана")
            
        return len(restaurants) > 0
        
    except Exception as e:
        print(f"❌ Ошибка при проверке бота: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🛠️ ПРОВЕРКА RESTAURANTS.JSON")
    print("=" * 50)
    
    # Проверяем JSON файл
    json_ok = check_restaurants_json()
    
    # Проверяем загрузку в боте
    bot_ok = check_bot_loading()
    
    print("\n" + "=" * 50)
    if json_ok and bot_ok:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("🚀 Бот должен работать корректно")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ ДЛЯ ИСПРАВЛЕНИЯ")
        if not json_ok:
            print("   - Исправь ошибки в restaurants.json")
        if not bot_ok:
            print("   - Проверь настройки базы данных")
    print("=" * 50)