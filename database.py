# database.py
import json
import os
from config import RESTAURANTS_FOLDER

def load_restaurants():
    restaurants = {}
    if not os.path.exists(RESTAURANTS_FOLDER):
        return restaurants
    
    for file in os.listdir(RESTAURANTS_FOLDER):
        if file.endswith(".json"):
            try:
                with open(f"{RESTAURANTS_FOLDER}/{file}", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    restaurants[data["id"]] = data
            except Exception as e:
                print(f"Ошибка загрузки {file}: {e}")
    return restaurants

def create_example_restaurant():
    if not os.path.exists(RESTAURANTS_FOLDER):
        os.makedirs(RESTAURANTS_FOLDER)
    
    example_file = f"{RESTAURANTS_FOLDER}/pizza_napoli.json"
    if not os.path.exists(example_file):
        example = {
            "id": "pizza_napoli",
            "name": "Pizza Napoli",
            "welcome": "Добро пожаловать в Pizza Napoli! Лучшая пицца в Бруклине!",
            "menu": {
                "еда": ["Маргарита - $12", "Пепперони - $14", "4 сыра - $16"],
                "напитки": ["Кола - $3", "Вода - $2", "Пиво - $6"],
                "десерты": ["Тирамису - $8", "Мороженое - $5"]
            }
        }
        with open(example_file, "w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False, indent=4)
        print(f"Создан пример: {example_file}")



def add_restaurant(restaurant_id, name, welcome, menu_dict):
    if not os.path.exists(RESTAURANTS_FOLDER):
        os.makedirs(RESTAURANTS_FOLDER)
    file_path = f"{RESTAURANTS_FOLDER}/{restaurant_id}.json"
    data = {
        "id": restaurant_id,
        "name": name,
        "welcome": welcome,
        "menu": menu_dict
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Ресторан добавлен: {name}")