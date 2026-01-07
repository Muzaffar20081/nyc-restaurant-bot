# test.py
import sys
print(f"Python версия: {sys.version}")
print(f"Путь к Python: {sys.executable}")

try:
    import aiogram
    print(f"✅ Aiogram установлен: {aiogram.__version__}")
except ImportError:
    print("❌ Aiogram не установлен")

try:
    import asyncio
    print("✅ Asyncio работает")
except ImportError:
    print("❌ Asyncio не работает")
