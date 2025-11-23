# ai_brain.py - AI ДЛЯ ЛЮБОГО РЕСТОРАНА
import os
import httpx
from menu import ALL_ITEMS, RESTAURANT_NAME

async def ask_grok(text: str, cart_info: str = "") -> str:
    menu_text = f"🍽️ *МЕНЮ {RESTAURANT_NAME.upper()}:*\n"
    for item, price in ALL_ITEMS.items():
        menu_text += f"• {item} - {price}₽\n"
    
    prompt = f"""{menu_text}

Клиент: "{text}"
Корзина: {cart_info}

Ты - сотрудник {RESTAURANT_NAME}. Отвечай коротко и вежливо!
- Если просят меню - направь в раздел меню
- Если заказывают товар - подтверди добавление в корзину
- Если спрашивают про корзину - покажи содержимое
- Если просят итого - покажи сумму
- На вопросы о ресторане отвечай кратко
- Будь полезным и дружелюбным"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('GROK_API_KEY')}",
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
            else:
                return "Используйте кнопки меню для заказа 🍔"
                
    except Exception as e:
        return "Используйте кнопки меню для заказа 🍔"
