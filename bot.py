import os
import telebot
from telebot import types
from dotenv import load_dotenv
from database import load_restaurants, add_restaurant
from config import RESTAURANTS_FOLDER

# Загружаем .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244967100:AAFG7beMN450dqwzlqQDjnFJoHxWl0qjXAE")
bot = telebot.TeleBot(BOT_TOKEN)

# ТВОЙ ID — ТОЛЬКО ТЫ МОЖЕШЬ ИСПОЛЬЗОВАТЬ /add
ADMIN_ID = 6056106251   # ← ЗАМЕНИ НА СВОЙ ID (узнай через @userinfobot)

# Загружаем рестораны
restaurants = load_restaurants()

# --- КНОПКИ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("/menu")
    markup.add(btn_menu)
    return markup

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    resto_id = args[0] if args else None

    if resto_id and resto_id in restaurants:
        # Переход по ссылке t.me/твойбот?start=pizza_napoli
        r = restaurants[resto_id]
        text = f"*{r['name']}*\n\n{r['welcome']}"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Меню", callback_data=f"menu_{resto_id}")
        markup.add(btn)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        # Обычный /start
        if message.from_user.id == ADMIN_ID:
            bot.send_message(
                message.chat.id,
                "Привет, *Админ!*\n\n"
                "• /add — добавить ресторан\n"
                "• /menu — посмотреть",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                message.chat.id,
                "Привет!\n\n"
                "Посмотри меню: /menu",
                reply_markup=main_menu()
            )

# --- /menu ---
@bot.message_handler(commands=['menu'])
def menu(message):
    if not restaurants:
        bot.send_message(message.chat.id, "Рестораны пока не добавлены.", reply_markup=main_menu())
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for rid, r in restaurants.items():
        btn = types.InlineKeyboardButton(r['name'], callback_data=f"show_{rid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери ресторан:", reply_markup=markup)

# --- Показать меню ---
@bot.callback_query_handler(func=lambda c: c.data.startswith("show_"))
def show_menu(call):
    rid = call.data.split("_")[1]
    if rid not in restaurants:
        return
    r = restaurants[rid]
    text = f"*{r['name']}*\n\n{r['welcome']}\n\n"
    for cat, items in r['categories'].items():
        text += f"*{cat.upper()}*\n"
        for name, price in items:
            text += f"• {name} — ${price}\n"
        text += "\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# --- /add (ТОЛЬКО ДЛЯ АДМИНА) ---
@bot.message_handler(commands=['add'])
def add_resto(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Только админ может добавлять рестораны!")
        return

    msg = bot.send_message(message.chat.id, "ID ресторана (например, pizza_napoli):")
    bot.register_next_step_handler(msg, step_id)

def step_id(message):
    resto_id = message.text.strip().lower()
    if resto_id in restaurants:
        bot.reply_to(message, "Такой ID уже есть!")
        return
    msg = bot.send_message(message.chat.id, "Название ресторана:")
    bot.register_next_step_handler(msg, step_name, resto_id)

def step_name(message, resto_id):
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Приветствие (например: Добро пожаловать!):")
    bot.register_next_step_handler(msg, step_welcome, resto_id, name)

def step_welcome(message, resto_id, name):
    welcome = message.text.strip()
    msg = bot.send_message(message.chat.id, "Меню (формат: категория: блюдо $цена)\nПример:\nпицца: Маргарита $16")
    bot.register_next_step_handler(msg, step_menu, resto_id, name, welcome)

def step_menu(message, resto_id, name, welcome):
    text = message.text.strip()
    categories = {}
    for line in text.split('\n'):
        if ':' in line:
            cat, items = line.split(':', 1)
            cat = cat.strip().lower()
            dishes = []
            for d in items.split(','):
                if '$' in d:
                    dish, price = d.rsplit('$', 1)
                    dishes.append((dish.strip(), price.strip()))
            if dishes:
                categories[cat] = dishes

    if not categories:
        bot.reply_to(message, "Не понял меню. Попробуй ещё раз.")
        return

    add_restaurant(resto_id, name, welcome, categories)
    global restaurants
    restaurants = load_restaurants()

    link = f"t.me/{bot.get_me().username}?start={resto_id}"
    bot.send_message(
        message.chat.id,
        f"Ресторан *{name}* добавлен!\n\n"
        f"Ссылка для клиентов:\n{link}",
        parse_mode="Markdown"
    )

# --- Запуск ---
if __name__ == "__main__":
    print("Ресторанов:", len(restaurants))
    print("Бот запущен!")
    bot.infinity_polling()
