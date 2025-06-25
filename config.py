import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища з .env файлу
load_dotenv()

# Налаштування бази даних
# Спочатку перевіряємо чи є DATABASE_URL (для Render/Heroku)
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Якщо DATABASE_URL не встановлено, будуємо з окремих параметрів
    DB_USER = os.getenv('DB_USER', 'abobina')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '2323')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'finance_bot')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Налаштування Telegram бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Налаштування OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Other settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
PORT = int(os.getenv("PORT", 8000))
