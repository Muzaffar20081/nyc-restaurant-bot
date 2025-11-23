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
