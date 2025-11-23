import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RESTAURANT_ID = os.getenv("RESTAURANT_ID", "burger_king")  # ID ресторана из базы
ADMIN_ID = os.getenv("ADMIN_ID", "")  # Для уведомлений
