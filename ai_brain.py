# ai_brain.py - МОЗГ БОТА С GROK AI
import os
import httpx
from menu import ALL_ITEMS

async def ask_grok(text: str, cart_info: str = "") -> str:
    # Формируем текст меню для промпта
    menu_text = "МЕНЮ BURGER KING:\n"
    for item, price in ALL_ITEMS.items():
        menu_text += f"{item} - {price}₽\n"
    
    prompt = f"""{menu_text}

Клиент написал: "{text}"
Корзина: {cart_info}

Ты дерзкий сотрудник Burger King. Отвечай коротко и по-падански!
- Если просят меню или "что есть" - ответь "Смотри меню выше 👆"
- Если заказывают товар из меню - скажи "Закинул в корзину! 🛒"
- Если спрашивают про корзину - ответь "В корзине: {cart_info}"
- Если говорят "очисти корзину" - скажи "Корзина очищена! 🧹"
- Если просят итого или сумму - покажи общую сумму
- На остальное отвечай кратко и по-делу"""

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
                return "Чё-то с API, брат... 🛠️"
                
    except Exception as e:
        return f"Технические шоколадки... 🔌"
