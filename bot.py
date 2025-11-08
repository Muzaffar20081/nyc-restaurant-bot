# bot.py
import telebot
from telebot import types
from database import load_restaurants, create_example_restaurant, add_restaurant
from config import RESTAURANTS_FOLDER

# === ЗАПУСК ===
create_example_restaurant()
RESTAURANTS = load_restaurants()
bot = telebot.TeleBot("8244967100:AAFG7beMN450dqwzlqQDjnFJoHxWl0qjXAE")

# === АДМИН ID (ЗАМЕНИ НА СВОЙ!) ===
ADMIN_ID = 123456789  # ← Узнай у @userinfobot

# === СОСТОЯНИЕ ДОБАВЛЕНИЯ ===
add_state = {}

# === /add — ПОШАГОВО ===
@bot.message_handler(commands=['add'])
def start_add(message):
    if message.from_user.id != ADMIN_ID:
        return
    chat_id = message.chat.id
    add_state[chat_id] = {"step": 1, "data": {}}
    bot.send_message(chat_id, "Шаг 1: Введите <b>ID</b> (например: sushi_zen)", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.chat.id in add_state)
def handle_add(message):
    chat_id = message.chat.id
    state = add_state[chat_id]
    text = message.text.strip()

    if state["step"] == 1:
        if not text.replace("_", "").isalnum():
            bot.send_message(chat_id, "Только буквы, цифры, _")
            return
        state["data"]["id"] = text
        state["step"] = 2
        bot.send_message(chat_id, "Шаг 2: Название ресторана")

    elif state["step"] == 2:
        state["data"]["name"] = text
        state["step"] = 3
        bot.send_message(chat_id, "Шаг 3: Приветствие")

    elif state["step"] == 3:
        state["data"]["welcome"] = text
        state["step"] = 4
        state["data"]["menu"] = {}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Готово")
        bot.send_message(chat_id, "Шаг 4: Добавляйте категории\nФормат: <b>еда: Блюдо $10</b>\nИли <b>Готово</b>", parse_mode="HTML", reply_markup=markup)

    elif state["step"] == 4:
        if text == "Готово":
            data = state["data"]
            add_restaurant(data["id"], data["name"], data["welcome"], data["menu"])
            bot.send_message(chat_id, f"Ресторан <b>{data['name']}</b> добавлен!\n<code>t.me/YourBot?start={data['id']}</code>", parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
            global RESTAURANTS
            RESTAURANTS = load_restaurants()
            del add_state[chat_id]
        else:
            try:
                cat, items = text.split(":", 1)
                state["data"]["menu"][cat.strip()] = [i.strip() for i in items.split(",") if i.strip()]
                bot.send_message(chat_id, f"Добавлено: <b>{cat.strip()}</b>")
            except:
                bot.send_message(chat_id, "Ошибка! Формат: <b>еда: Блюдо $10</b>", parse_mode="HTML")

# === Остальной код (start, menu, handle) ===
user_rest = {}

@bot.message_handler(commands=['start'])
def start(m):
    args = m.text.split()
    if len(args) > 1 and args[1] in RESTAURANTS:
        user_rest[m.chat.id] = args[1]
        bot.send_message(m.chat.id, RESTAURANTS[args[1]]["welcome"])
    else:
        bot.send_message(m.chat.id, "Используйте: /start pizza_napoli")

@bot.message_handler(commands=['menu'])
def menu(m):
    rid = user_rest.get(m.chat.id)
    if not rid: return bot.send_message(m.chat.id, "Сначала /start ...")
    resto = RESTAURANTS[rid]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in resto["menu"]:
        markup.add(types.KeyboardButton(cat))
    bot.send_message(m.chat.id, f"Меню {resto['name']}", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle(m):
    rid = user_rest.get(m.chat.id)
    if not rid: return
    text = m.text
    if text in RESTAURANTS[rid]["menu"]:
        items = "\n".join(RESTAURANTS[rid]["menu"][text])
        bot.send_message(m.chat.id, f"*{text}*\n{items}", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, f"Заказ: *{text}*", parse_mode="Markdown")

# === ЗАПУСК ===
print(f"Ресторанов: {len(RESTAURANTS)}")
bot.polling(non_stop=True)