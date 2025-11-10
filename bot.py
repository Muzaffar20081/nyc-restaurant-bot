import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244967100:AAFG7beMN450dqwzlqQDjnFJoHxWl0qjXAE")
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_ID = 6056106251  # ← ТВОЙ ID

# Читаем рестораны
try:
    with open("restaurants.json", "r", encoding="utf-8") as f:
        restaurants = json.load(f)
except:
    restaurants = {}

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    resto_id = args[0] if args else None

    if resto_id and resto_id in restaurants:
        show_resto_menu(message.chat.id, resto_id)
    else:
        if message.from_user.id == ADMIN_ID:
            bot.send_message(message.chat.id, "Привет, *Админ!*\n\nРестораны в `restaurants.json`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "Привет!\n\n/menu — посмотреть")

@bot.message_handler(commands=['menu'])
def menu(message):
    if not restaurants:
        bot.send_message(message.chat.id, "Рестораны не добавлены.")
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for rid, r in restaurants.items():
        btn = types.InlineKeyboardButton(r['name'], callback_data=f"show_{rid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери ресторан:", reply_markup=markup)

# --- ОБРАБОТКА НАЖАТИЯ НА КНОПКУ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("show_"))
def callback_show_menu(call):
    rid = call.data.split("_")[1]
    if rid not in restaurants:
        bot.answer_callback_query(call.id, "Ресторан не найден.")
        return
    show_resto_menu(call.message.chat.id, rid, message_id=call.message.message_id)

def show_resto_menu(chat_id, rid, message_id=None):
    r = restaurants[rid]
    text = f"*{r['name']}*\n\n{r['welcome']}\n\n"
    for cat, items in r['categories'].items():
        text += f"*{cat.upper()}*\n"
        for name, price in items:
            text += f"• {name} — ${price}\n"
        text += "\n"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))

    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    menu(call.message)

if __name__ == "__main__":
    print("Бот запущен! Ресторанов:", len(restaurants))
    bot.infinity_polling()
