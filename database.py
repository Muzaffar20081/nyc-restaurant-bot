import json
import os
from config import RESTAURANTS_FOLDER

def ensure_restaurants_folder():
    if not os.path.exists(RESTAURANTS_FOLDER):
        os.makedirs(RESTAURANTS_FOLDER)

def load_restaurants():
    ensure_restaurants_folder()
    restaurants_file = os.path.join(RESTAURANTS_FOLDER, "restaurants.json")
    
    if not os.path.exists(restaurants_file):
        return {}
    
    try:
        with open(restaurants_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_restaurants(restaurants):
    ensure_restaurants_folder()
    restaurants_file = os.path.join(RESTAURANTS_FOLDER, "restaurants.json")
    
    with open(restaurants_file, 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

def create_example_restaurant():
    restaurants = load_restaurants()
    if "pizza_napoli" not in restaurants:
        example_restaurant = {
            "pizza_napoli": {
                "name": "Pizza Napoli",
                "welcome": "Добро пожаловать в лучшую пиццерию NYC!",
                "categories": {
                    "пицца": [
                        ["Маргарита", "16"],
                        ["Пепперони", "18"]
                    ],
                    "напитки": [
                        ["Кола", "3"],
                        ["Сок", "4"]
                    ]
                }
            }
        }
        save_restaurants(example_restaurant)

def add_restaurant(resto_id, name, welcome, categories):
    restaurants = load_restaurants()
    restaurants[resto_id] = {
        "name": name,
        "welcome": welcome,
        "categories": categories
    }
    save_restaurants(restaurants)
