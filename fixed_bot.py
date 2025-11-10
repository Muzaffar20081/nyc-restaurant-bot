import os
import telebot
import json
from telebot import types

# Настройки
BOT_TOKEN = "8244967100:AAFG7beMM5Qdqwz1qQDjnfJoHxM1QqjXAE"
ADMIN_ID = 6056106251

bot = telebot.TeleBot(BOT_TOKEN)

# Загружаем рестораны напрямую
def load_restaurants():
    try:
        with open('restaurants.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

restaurants = load_restaurants()

# Если ресторанов нет - создаем Burger King
if not restaurants:
    print("🍔 Создаю Burger King...")
    restaurants = {
        "burger_king": {
            "name": "Burger King",
            "welcome": "Добро пожаловать в Burger King! 🍔\n\nHome of the Whopper!",
            "categories": {
                "бургеры": [
                    ["Воппер", "8"],
                    ["Чизбургер", "5"],
                    ["Бекон Кинг", "9"],
                    ["Чикен Кинг", "7"]
                ],
                "картошка и закуски": [
                    ["Картошка фри", "3"],
                    ["Луковые кольца", "4"],
                    ["Наггетсы (10шт)", "6"]
                ],
                "напитки": [
                    ["Кола", "2"],
                    ["Фанта", "2"],
                    ["Спрайт", "2"],
                    ["Кофе", "3"]
                ]
            }
        }
    }
    
    # Сохраняем в JSON
    with open('restaurants.json', 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

print(f"✅ Загружено ресторанов: {len(restaurants)}")
for name in restaurants:
    print(f"   - {restaurants[name]['name']}")

# Кнопки
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("🍽 Меню")
    btn_help = types.KeyboardButton("🆘 Помощь")
    markup.add(btn_menu, btn_help)
    return markup

# Команды
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Привет, *{message.from_user.first_name}!* 👋\n\n"
        "Я — бот для ресторанов NYC 🍔\n"
        "Нажми 🍽 Меню чтобы увидеть рестораны!",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['menu'])
def menu(message):
    if not restaurants:
        bot.send_message(message.chat.id, "📭 Рестораны пока не добавлены.")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for rid, r in restaurants.items():
        btn = types.InlineKeyboardButton(f"🍽 {r['name']}", callback_data=f"menu_{rid}")
        markup.add(btn)
    
    bot.send_message(message.chat.id, "🏪 Выбери ресторан:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def show_menu(call):
    resto_id = call.data.split("_")[1]
    if resto_id not in restaurants:
        bot.answer_callback_query(call.id, "❌ Ресторан не найден.")
        return

    resto = restaurants[resto_id]
    text = f"*{resto['name']}* 🍽\n\n"
    
    for cat, items in resto['categories'].items():
        text += f"*{cat.upper()}*\n"
        for name, price in items:
            text += f"• {name} — ${price}\n"
        text += "\n"
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    
    if text == "🍽 Меню":
        menu(message)
    elif text == "🆘 Помощь":
        bot.send_message(message.chat.id, "Нажми 🍽 Меню чтобы увидеть рестораны!")
    else:
        bot.send_message(message.chat.id, "Используй кнопки меню! 👆")

# Запуск
print("🚀 Бот запущен! Ищи @NYC_Restaurant_Bot в Telegram")
bot.infinity_polling()