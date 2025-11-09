import os
import telebot
from telebot import types
from dotenv import load_dotenv
from database import load_restaurants, create_example_restaurant, add_restaurant
from config import RESTAURANTS_FOLDER

# Загружаем .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244967100:AAFG7beMN450dqwzlqQDjnFJoHxWl0qjXAE")
bot = telebot.TeleBot(BOT_TOKEN)

# Админ ID (твой)
ADMIN_ID = 6056106251  # ← ЗАМЕНИ НА СВОЙ ID

# Загружаем рестораны
restaurants = load_restaurants()

# --- КНОПКИ ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("/menu")
    btn_help = types.KeyboardButton("/help")
    btn_about = types.KeyboardButton("/about")
    markup.add(btn_menu, btn_help, btn_about)
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_add = types.KeyboardButton("/add")
    btn_back = types.KeyboardButton("/menu")
    markup.add(btn_add, btn_back)
    return markup

# --- КОМАНДЫ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    resto_id = args[0] if args else None

    if resto_id and resto_id in restaurants:
        # Переход по ссылке
        resto = restaurants[resto_id]
        text = f"*{resto['name']}*\n\n{resto['welcome']}"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("📋 Меню", callback_data=f"menu_{resto_id}")
        markup.add(btn)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        # Обычный /start
        bot.send_message(
            message.chat.id,
            f"Привет, *{message.from_user.first_name}!*\n\n"
            "Я — бот для ресторанов NYC 🍕\n"
            "Нажми /menu, чтобы увидеть доступные заведения!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

@bot.message_handler(commands=['menu'])
def menu(message):
    if not restaurants:
        bot.send_message(message.chat.id, "Рестораны пока не добавлены.", reply_markup=main_menu())
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for rid, r in restaurants.items():
        btn = types.InlineKeyboardButton(f"{r['name']}", callback_data=f"menu_{rid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери ресторан:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def show_menu(call):
    resto_id = call.data.split("_")[1]
    if resto_id not in restaurants:
        bot.answer_callback_query(call.id, "Ресторан не найден.")
        return

    resto = restaurants[resto_id]
    text = f"*{resto['name']}*\n\n"
    for cat, items in resto['categories'].items():
        text += f"*{cat.upper()}*\n"
        for name, price in items:
            text += f"• {name} — ${price}\n"
        text += "\n"
    text += "Напиши /start, чтобы вернуться."

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['add'])
def add_resto(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Только админ может добавлять рестораны!")
        return

    msg = bot.send_message(message.chat.id, "Шаг 1: Введите ID ресторана (например, pizza_napoli):")
    bot.register_next_step_handler(msg, process_id_step)

def process_id_step(message):
    resto_id = message.text.strip().lower()
    if resto_id in restaurants:
        bot.reply_to(message, "Такой ID уже есть!")
        return
    msg = bot.send_message(message.chat.id, "Шаг 2: Название ресторана:")
    bot.register_next_step_handler(msg, process_name_step, resto_id)

def process_name_step(message, resto_id):
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "Шаг 3: Приветствие (например, Добро пожаловать!):")
    bot.register_next_step_handler(msg, process_welcome_step, resto_id, name)

def process_welcome_step(message, resto_id, name):
    welcome = message.text.strip()
    msg = bot.send_message(message.chat.id, "Шаг 4: Категории и блюда (формат: категория: блюдо $цена)\nПример:\nпицца: Маргарита $16")
    bot.register_next_step_handler(msg, process_categories_step, resto_id, name, welcome)

def process_categories_step(message, resto_id, name, welcome):
    text = message.text.strip()
    categories = {}
    for line in text.split('\n'):
        if ':' in line:
            cat, items = line.split(':', 1)
            cat = cat.strip().lower()
            dishes = []
            for d in items.split(','):
                if '$' in d:
                    dish_name, price = d.rsplit('$', 1)
                    dishes.append((dish_name.strip(), price.strip()))
            if dishes:
                categories[cat] = dishes

    if not categories:
        bot.reply_to(message, "Не распознал блюда! Попробуй ещё раз.")
        return

    add_restaurant(resto_id, name, welcome, categories)
    global restaurants
    restaurants = load_restaurants()

    link = f"t.me/{bot.get_me().username}?start={resto_id}"
    bot.send_message(
        message.chat.id,
        f"Ресторан *{name}* добавлен!\n\n"
        f"Ссылка для клиентов:\n{link}",
        parse_mode="Markdown",
        reply_markup=admin_menu()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "*Помощь:*\n"
        "/start — начать\n"
        "/menu — список ресторанов\n"
        "/help — эта справка\n"
        "/about — о боте",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(
        message.chat.id,
        "Бот для ресторанов NYC\n"
        "Создан для автоматизации заказов\n"
        "Версия: 1.0",
        reply_markup=main_menu()
    )

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("Ресторанов:", len(restaurants))
    print("Бот запущен!")
    bot.infinity_polling()
  
