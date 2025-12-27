import os
import httpx

GROK_API_KEY = os.getenv("GROK_API_KEY")

async def ask_ai(text: str) -> str:
    prompt = f"""Ты — дерзкий сотрудник Burger King в России.
Клиент написал: "{text}"

Отвечай коротко, по-пацански, с юмором.
Если просят меню — отвечай: "Меню открыто!"
Если заказывают — отвечай: "Закинул в корзину!"
Если спрашивают цену — отвечай ценой."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
                json={
                    "model": "grok-2-latest",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                    "max_tokens": 150
                }
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            return "Брат, Grok приуныл... Попробуй ещё раз!"
    except Exception as e:
        return "Интернет тупит, брат... Спроси ещё раз!"
