import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8244967100:AAFG7beMN450dqwzlqQDjnFJoHxWl0qjXAE")
bot = telebot.TeleBot(BOT_TOKEN)

# Читаем рестораны из файла
with open("restaurants.json", "r", encoding="utf-8") as f:
    restaurants = json.load(f)

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    resto_id = args[0] if args else None

    if resto_id and resto_id in restaurants:
        r = restaurants[resto_id]
        text = f"*{r['name']}*\n\n{r['welcome']}"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Меню", callback_data=f"show_{resto_id}")
        markup.add(btn)
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Привет!\n\n/menu — посмотреть рестораны")

@bot.message_handler(commands=['menu'])
def menu(message):
    if not restaurants:
        bot.send_message(message.chat.id, "Рестораны не добавлены.")
        return
    markup = types.InlineKeyboardMarkup()
    for rid, r in restaurants.items():
        btn = types.InlineKeyboardButton(r['name'], callback_data=f"show_{rid}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("show_"))
def show_menu(call):
    rid = call.data.split("_")[1]
    if rid not in restaurants: return
    r = restaurants[rid]
    text = f"*{r['name']}*\n\n{r['welcome']}\n\n"
    for cat, items in r['categories'].items():
        text += f"*{cat.upper()}*\n"
        for name, price in items:
            text += f"• {name} — ${price}\n"
        text += "\n"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    print("Бот запущен! Ресторанов:", len(restaurants))
    bot.infinity_polling()
