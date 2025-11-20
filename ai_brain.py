# ai_brain.py — весь мозг Grok здесь
import httpx

import logging

MENU = """
Воппер — 349₽
Двойной Воппер — 449₽
Чизбургер — 149₽
Биг Кинг — 399₽
Картошка большая — 149₽
Наггетсы 9шт — 259₽
Кола 0.5 — 119₽
Кола 1л — 179₽
Коктейль — 199₽
"""

async def ask_grok(text: str, cart_info: str = "") -> str:
    prompt = f"""{MENU}

Клиент написал: "{text}"
Корзина: {cart_info}

Ты дерзкий сотрудник Burger King. 
- Если просят меню — ответь ровно: /menu
- Если заказывают — добавь в корзину и скажи "Закинул!"
- Если "сколько" — только сумма
- Отвечай коротко и по-пацански"""

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('GROK_API_KEY')}"},
                json={
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                    "max_tokens": 200
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            return "Техработы, брат"
    except:
        return "На перекуре 1 сек"