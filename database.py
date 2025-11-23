# database.py - ДЛЯ РАБОТЫ С ДАННЫМИ
import json
import os

def save_user_data(user_id, data):
    """Сохраняем данные пользователя"""
    try:
        with open(f'user_{user_id}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_user_data(user_id):
    """Загружаем данные пользователя"""
    try:
        with open(f'user_{user_id}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}
