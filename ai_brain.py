import os
import httpx
from config import GROK_API_KEY
from menu import BURGER_KING_MENU

async def ask_grok(text: str, cart_info: str = "") -> str:
    prompt = f"""{BURGER_KING_MENU}

Клиент написал: "{text}"
Корзина: {cart_info}

Ты дерзкий сотрудник Burger King.
- Если просят меню - ответь ровно: /menu
- Если заказывают - добавь в корзину и скажи "Закинул!"
- Если "сколько" - только сумма
- Отвечай коротко и по-падански"""
    
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={ 
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                    "max_tokens": 200
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            return "Техноборщи, брат"
    except:
        return "На перекуре, 1 сек"
