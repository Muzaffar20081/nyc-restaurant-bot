# create_env.py - создает .env файл автоматически

def create_env_file():
    env_content = """BOT_TOKEN=8244967100:AAFG7beMM5Qdqwz1qQDjnfJoHxM1QqjXAE
ADMIN_ID=6056106251"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env успешно создан!")
    print("📝 Содержимое файла:")
    print(env_content)
    print("\n🔧 Теперь можно запускать бота: python bot.py")

if __name__ == "__main__":
    create_env_file()