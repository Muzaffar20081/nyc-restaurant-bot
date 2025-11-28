import os
import httpx
from config import CAFES

async def ask_grok(text: str, cart_info: str = "", cafe_key: str = "italy", ALL_ITEMS: dict = None) -> str:
    # Получаем название кафе
    cafe_name = CAFES.get(cafe_key, {}).get("name", "Ресторан")
    
    # Создаем текст меню для текущего кафе
    menu_text = f"🍽️ *МЕНЮ {cafe_name.upper()}:*\n"
    if ALL_ITEMS:
        for item, price in ALL_ITEMS.items():
            menu_text += f"• {item} - {price}₽\n"
    else:
        menu_text += "• Меню временно недоступно\n"
    
    prompt = f"""{menu_text}

Клиент: "{text}"
Корзина: {cart_info}
Ресторан: {cafe_name}

Ты - сотрудник {cafe_name}. Отвечай коротко и вежливо!
- Если просят меню - направь в раздел меню
- Если заказывают товар - подтверди добавление в корзину
- Если спрашивают про корзину - покажи содержимое
- Если просят итого - покажи сумму
- На вопросы о ресторане отвечай кратко
- Будь полезным и дружелюбным
- Отвечай на русском языке"""

    try:
        # Если есть Grok API ключ - используем AI
        api_key = os.getenv('GROK_API_KEY')
        if api_key:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 150
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
        
        # Если нет API ключа - используем простой AI
        return await simple_ai_fallback(text, cart_info, cafe_name, ALL_ITEMS)
                
    except Exception as e:
        return await simple_ai_fallback(text, cart_info, cafe_name, ALL_ITEMS)

async def simple_ai_fallback(text: str, cart_info: str, cafe_name: str, ALL_ITEMS: dict) -> str:
    """Простой AI если Grok недоступен"""
    text_lower = text.lower()
    
    # Показ корзины
    if any(word in text_lower for word in ['корзин', 'заказ', 'что в корзин', 'покажи корзин']):
        if cart_info and cart_info != "пустая":
            return f"🛒 *Ваша корзина:*\n{cart_info}\n\nИспользуйте кнопку 'Корзина' для управления"
        else:
            return "🛒 Корзина пустая! Добавьте товары из меню."
    
    # Очистка корзины
    elif any(word in text_lower for word in ['очист', 'удал', 'очис', 'очисти']):
        return "🗑 Корзина очищена! (Для очистки используйте кнопку 'Очистить корзину')"
    
    # Добавление товаров
    elif any(word in text_lower for word in ['добав', 'хочу', 'закажи', 'дай', 'положи']):
        if ALL_ITEMS:
            found_items = []
            for item_name in ALL_ITEMS.keys():
                if item_name.lower() in text_lower:
                    found_items.append(item_name)
            
            if found_items:
                return f"✅ Добавлено в корзину: {', '.join(found_items)}\n\nИспользуйте кнопку 'Корзина' для просмотра"
            else:
                item_list = ", ".join(list(ALL_ITEMS.keys())[:5])
                return f"Не нашел товар в меню 😔\n\nПопулярные товары: {item_list}..."
        else:
            return "Меню временно недоступно. Используйте кнопки навигации."
    
    # Помощь
    elif any(word in text_lower for word in ['помощ', 'help', 'совет', 'рекомен', 'что посоветуешь']):
        if ALL_ITEMS:
            popular = list(ALL_ITEMS.keys())[:3]
            return f"🤖 Популярное в {cafe_name}:\n• {chr(10) + '• '.join(popular)}\n\nПросто напишите название блюда чтобы добавить его в корзину!"
        else:
            return "🤖 Я могу помочь с заказом! Напишите что хотите заказать или используйте кнопки меню."
    
    # Приветствие
    elif any(word in text_lower for word in ['привет', 'hello', 'hi', 'здаров', 'здравств']):
        return f"Привет! 😊 Добро пожаловать в {cafe_name}! Чем могу помочь?"
    
    # Благодарность
    elif any(word in text_lower for word in ['спасибо', 'благодар', 'thanks']):
        return "Пожалуйста! 😊 Рад помочь! Что-нибудь ещё?"
    
    # Непонятная команда
    else:
        return "Не совсем понял запрос 🤔\n\nПопробуйте:\n• Написать название блюда\n• 'Покажи корзину' \n• 'Что посоветуешь?'\n• Или используйте кнопки меню"
